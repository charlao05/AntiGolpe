from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from backend.tests.provider_gate.adapters import ProviderResponse
from backend.tests.provider_gate.execution_orchestrator import ExecutionHalted, ExecutionOrchestrator
from backend.tests.provider_gate.guard import ExternalProviderNotAuthorized
from backend.tests.provider_gate.spend_tracker import (
    ConfigurationError,
    ExecutionState,
    InvalidUsage,
    SpendTracker,
)


class FakeAdapter:
    name = "fake"

    def __init__(self, *, estimate: float = 0.10, response: ProviderResponse | None = None, error: Exception | None = None):
        self.estimate = estimate
        self.response = response or ProviderResponse("ok", input_tokens=10, output_tokens=10, latency_ms=1.0)
        self.error = error
        self.calls = 0

    def estimate_worst_case_cost(self, *, system_prompt: str | None, user_input: str) -> float:
        return self.estimate

    def analyze(self, *, system_prompt: str | None, user_input: str) -> ProviderResponse:
        self.calls += 1
        if self.error:
            raise self.error
        return self.response

    def calculate_real_cost(self, response: ProviderResponse) -> float:
        if response.input_tokens is None or response.output_tokens is None:
            raise InvalidUsage("usage missing")
        return (response.input_tokens + response.output_tokens) / 100_000


class BadCostAdapter(FakeAdapter):
    def calculate_real_cost(self, response: ProviderResponse) -> float:
        return float("nan")


class FakeSafety:
    def __init__(self, safe: bool = True):
        self.safe = safe
        self.calls = 0

    def evaluate(self, response: ProviderResponse) -> bool:
        self.calls += 1
        return self.safe


class RecordingIncidents:
    def __init__(self):
        self.items = []

    def record(self, *, provider: str, error_type: str, state: ExecutionState) -> None:
        self.items.append((provider, error_type, state))


def tracker() -> SpendTracker:
    return SpendTracker(global_ceiling=10.0, provider_ceiling=3.0, per_call_ceiling=0.50)


def test_global_tracker_has_required_state_and_no_provider_tracker():
    t = tracker()
    assert t.global_spend == 0.0
    assert t.provider_spend == {}
    assert t.call_count == 0
    assert t.provider_call_count == {}
    assert t.state is ExecutionState.READY


def test_configuration_rejects_invalid_or_inconsistent_limits():
    with pytest.raises(ConfigurationError):
        SpendTracker(global_ceiling=0, provider_ceiling=3, per_call_ceiling=0.5)
    with pytest.raises(ConfigurationError):
        SpendTracker(global_ceiling=3, provider_ceiling=4, per_call_ceiling=0.5)
    with pytest.raises(ConfigurationError):
        SpendTracker(global_ceiling=10, provider_ceiling=3, per_call_ceiling=4)


def test_limits_are_immutable():
    t = tracker()
    with pytest.raises(FrozenInstanceError):
        t.limits.global_ceiling = 99  # type: ignore[misc]
    with pytest.raises(ConfigurationError):
        t.limits = t.limits  # type: ignore[misc]
    with pytest.raises(ConfigurationError):
        t.global_spend = 99  # type: ignore[misc]
    with pytest.raises(ConfigurationError):
        t.state = ExecutionState.RUNNING  # type: ignore[misc]


def test_authorize_requires_all_three_financial_conditions():
    t = tracker()
    assert t.authorize("openai", 0.50) is True
    t.begin_call()
    t.register("openai", 0.49)
    assert t.authorize("openai", 0.50) is True

    t2 = SpendTracker(global_ceiling=10, provider_ceiling=0.60, per_call_ceiling=0.50)
    assert t2.authorize("openai", 0.50) is True
    t2.begin_call()
    t2.register("openai", 0.20)
    assert t2.authorize("openai", 0.50) is False
    assert t2.state is ExecutionState.SPEND_LIMIT_REACHED


def test_one_tracker_controls_multiple_providers_and_global_ceiling():
    shared = SpendTracker(global_ceiling=1.00, provider_ceiling=0.75, per_call_ceiling=0.50)
    assert shared.authorize("provider_a", 0.50) is True
    shared.begin_call()
    shared.register("provider_a", 0.50)

    assert shared.authorize("provider_b", 0.50) is True
    shared.begin_call()
    shared.register("provider_b", 0.50)

    # Both providers used only 0.50 each, but a third call cannot cross the
    # single global ceiling even though both provider budgets have headroom.
    assert shared.authorize("provider_a", 0.01) is False
    assert shared.state is ExecutionState.SPEND_LIMIT_REACHED
    assert shared.global_spend == pytest.approx(1.00)
    assert shared.provider_spend == {"provider_a": 0.50, "provider_b": 0.50}


def test_orchestrator_rejects_unknown_provider_without_network():
    adapter = FakeAdapter()
    incidents = RecordingIncidents()
    orch = ExecutionOrchestrator(
        providers={"fake": adapter},
        spend_tracker=tracker(),
        safety_authority=FakeSafety(),
        incident_recorder=incidents,
    )
    with pytest.raises(ExecutionHalted) as exc:
        orch.execute_one(provider="missing", system_prompt=None, user_input="x")
    assert exc.value.state is ExecutionState.BLOCKED
    assert adapter.calls == 0


def test_budget_preflight_happens_before_adapter_call():
    adapter = FakeAdapter(estimate=0.51)
    orch = ExecutionOrchestrator(
        providers={"fake": adapter},
        spend_tracker=tracker(),
        safety_authority=FakeSafety(),
    )
    with pytest.raises(ExecutionHalted) as exc:
        orch.execute_one(provider="fake", system_prompt=None, user_input="x")
    assert exc.value.state is ExecutionState.SPEND_LIMIT_REACHED
    assert adapter.calls == 0


def test_provider_gate_failure_is_pre_network_and_records_no_spend():
    adapter = FakeAdapter()
    incidents = RecordingIncidents()

    def denied() -> None:
        raise ExternalProviderNotAuthorized("blocked")

    orch = ExecutionOrchestrator(
        providers={"fake": adapter},
        spend_tracker=tracker(),
        safety_authority=FakeSafety(),
        incident_recorder=incidents,
        authorization_check=denied,
    )
    with pytest.raises(ExecutionHalted) as exc:
        orch.execute_one(provider="fake", system_prompt=None, user_input="x")
    assert exc.value.state is ExecutionState.BLOCKED
    assert adapter.calls == 0
    assert orch.spend_tracker.global_spend == 0


def test_success_registers_real_cost_and_allows_next_call_with_fresh_preflight():
    adapter = FakeAdapter(response=ProviderResponse("ok", input_tokens=1000, output_tokens=1000))
    safety = FakeSafety()
    orch = ExecutionOrchestrator(
        providers={"fake": adapter},
        spend_tracker=tracker(),
        safety_authority=safety,
        authorization_check=lambda: None,
    )
    orch.execute_one(provider="fake", system_prompt=None, user_input="one")
    assert orch.state is ExecutionState.COMPLETED
    assert orch.spend_tracker.call_count == 1
    assert orch.spend_tracker.provider_call_count["fake"] == 1
    assert orch.spend_tracker.global_spend == pytest.approx(0.02)

    orch.execute_one(provider="fake", system_prompt=None, user_input="two")
    assert orch.spend_tracker.call_count == 2
    assert adapter.calls == 2
    assert safety.calls == 2


def test_post_network_failure_records_incident_before_global_stop():
    adapter = FakeAdapter(error=TimeoutError("timeout"))
    incidents = RecordingIncidents()
    orch = ExecutionOrchestrator(
        providers={"fake": adapter},
        spend_tracker=tracker(),
        safety_authority=FakeSafety(),
        incident_recorder=incidents,
        authorization_check=lambda: None,
    )
    with pytest.raises(ExecutionHalted) as exc:
        orch.execute_one(provider="fake", system_prompt=None, user_input="x")
    assert exc.value.state is ExecutionState.PROVIDER_FAILURE
    assert orch.state is ExecutionState.PROVIDER_FAILURE
    assert incidents.items == [("fake", "TimeoutError", ExecutionState.RUNNING)]


def test_missing_usage_is_provider_failure_and_never_zero():
    adapter = FakeAdapter(response=ProviderResponse("ok", input_tokens=None, output_tokens=10))
    incidents = RecordingIncidents()
    orch = ExecutionOrchestrator(
        providers={"fake": adapter},
        spend_tracker=tracker(),
        safety_authority=FakeSafety(),
        incident_recorder=incidents,
        authorization_check=lambda: None,
    )
    with pytest.raises(ExecutionHalted) as exc:
        orch.execute_one(provider="fake", system_prompt=None, user_input="x")
    assert exc.value.state is ExecutionState.PROVIDER_FAILURE
    assert orch.spend_tracker.global_spend == 0
    assert incidents.items[0][1] == "InvalidUsage"


def test_malformed_real_cost_cannot_leave_execution_running():
    adapter = BadCostAdapter()
    incidents = RecordingIncidents()
    orch = ExecutionOrchestrator(
        providers={"fake": adapter},
        spend_tracker=tracker(),
        safety_authority=FakeSafety(),
        incident_recorder=incidents,
        authorization_check=lambda: None,
    )
    with pytest.raises(ExecutionHalted) as exc:
        orch.execute_one(provider="fake", system_prompt=None, user_input="x")
    assert exc.value.state is ExecutionState.PROVIDER_FAILURE
    assert orch.state is ExecutionState.PROVIDER_FAILURE
    assert incidents.items == [("fake", "InvalidUsage", ExecutionState.RUNNING)]
    assert orch.spend_tracker.global_spend == 0


def test_security_failure_overrides_budget_terminal_state():
    adapter = FakeAdapter(estimate=0.50, response=ProviderResponse("bad", input_tokens=60_000, output_tokens=0))
    safety = FakeSafety(safe=False)
    orch = ExecutionOrchestrator(
        providers={"fake": adapter},
        spend_tracker=tracker(),
        safety_authority=safety,
        authorization_check=lambda: None,
    )
    with pytest.raises(ExecutionHalted) as exc:
        orch.execute_one(provider="fake", system_prompt=None, user_input="x")
    assert exc.value.state is ExecutionState.SECURITY_ABORT
    assert orch.state is ExecutionState.SECURITY_ABORT
    assert orch.spend_tracker.call_count == 1


def test_terminal_state_is_irreversible_for_subsequent_calls():
    adapter = FakeAdapter(estimate=0.51)
    orch = ExecutionOrchestrator(
        providers={"fake": adapter},
        spend_tracker=tracker(),
        safety_authority=FakeSafety(),
    )
    with pytest.raises(ExecutionHalted):
        orch.execute_one(provider="fake", system_prompt=None, user_input="x")
    calls_after_stop = adapter.calls
    with pytest.raises(ExecutionHalted) as exc:
        orch.execute_one(provider="fake", system_prompt=None, user_input="y")
    assert exc.value.state is ExecutionState.SPEND_LIMIT_REACHED
    assert adapter.calls == calls_after_stop
