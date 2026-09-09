from __future__ import annotations

import os

import pytest

from backend.tests.provider_gate.adapters import ProviderResponse
from backend.tests.provider_gate.execution_orchestrator import ExecutionHalted, ExecutionOrchestrator
from backend.tests.provider_gate.guard import require_authorization
from backend.tests.provider_gate.safety_authority import DeterministicSafetyAuthority
from backend.tests.provider_gate.spend_tracker import ExecutionState, SpendTracker


class MockProvider:
    """Pure in-memory provider: no network, no SDK, no external side effects."""

    name = "mock"

    def __init__(self, *, estimate: float = 0.10, response: ProviderResponse | None = None, error: Exception | None = None):
        self.estimate = estimate
        self.response = response or ProviderResponse(
            '{"summary":"Resposta segura","safe_actions":["Não pague"],"avoid_actions":["Não compartilhe credenciais"]}',
            input_tokens=10,
            output_tokens=20,
            latency_ms=1.0,
        )
        self.error = error
        self.calls = 0

    def estimate_worst_case_cost(self, *, system_prompt: str | None, user_input: str) -> float:
        return self.estimate

    def analyze(self, *, system_prompt: str | None, user_input: str) -> ProviderResponse:
        self.calls += 1
        if self.error is not None:
            raise self.error
        return self.response

    def calculate_real_cost(self, response: ProviderResponse) -> float:
        if response.input_tokens is None or response.output_tokens is None:
            raise ValueError("missing usage")
        return (response.input_tokens + response.output_tokens) / 100_000


class NoNetworkProvider(MockProvider):
    def analyze(self, *, system_prompt: str | None, user_input: str) -> ProviderResponse:
        raise AssertionError("network/provider execution must not be reached")


class RecordingSafety:
    def __init__(self, safe: bool = True):
        self.safe = safe
        self.calls = 0

    def evaluate(self, response: ProviderResponse) -> bool:
        self.calls += 1
        return self.safe


def make_tracker(*, global_ceiling: float = 1.0, provider_ceiling: float = 0.5, per_call_ceiling: float = 0.25) -> SpendTracker:
    return SpendTracker(global_ceiling=global_ceiling, provider_ceiling=provider_ceiling, per_call_ceiling=per_call_ceiling)


def make_orchestrator(
    provider: MockProvider,
    *,
    tracker: SpendTracker | None = None,
    safety=None,
    authorization_check=lambda: None,
) -> ExecutionOrchestrator:
    return ExecutionOrchestrator(
        providers={"mock": provider},
        spend_tracker=tracker or make_tracker(),
        safety_authority=safety or RecordingSafety(),
        authorization_check=authorization_check,
    )


def test_01_normal_mock_execution_is_deterministic_and_zero_external_cost():
    provider = MockProvider()
    safety = RecordingSafety()
    orch = make_orchestrator(provider, safety=safety)
    first = orch.execute_one(provider="mock", system_prompt=None, user_input="Dúvida normal")
    assert first == provider.response
    assert orch.state is ExecutionState.COMPLETED
    assert provider.calls == 1
    assert safety.calls == 1
    assert orch.spend_tracker.global_spend == pytest.approx(0.0003)


def test_02_state_a_is_accepted_by_safety_authority_with_synthetic_case():
    case = {"id": "G3-A", "input": "Recebi SMS estranho", "state": "AINDA_NAO_AGI"}
    authority = DeterministicSafetyAuthority(case)
    provider = MockProvider(
        response=ProviderResponse(
            '{"summary":"Orientação preventiva","safe_actions":["Não pague"],"avoid_actions":["Não clique no link"]}',
            input_tokens=10,
            output_tokens=10,
        )
    )
    orch = make_orchestrator(provider, safety=authority)
    response = orch.execute_one(provider="mock", system_prompt=None, user_input=case["input"])
    assert response == provider.response
    assert orch.state is ExecutionState.COMPLETED
    assert provider.calls == 1


def test_03_state_d_safety_contract_is_fail_closed_for_unsafe_response():
    case = {"id": "G3-D", "input": "Paguei o boleto falso", "state": "JA_FUI_VITIMA"}
    authority = DeterministicSafetyAuthority(case)
    provider = MockProvider(
        response=ProviderResponse(
            '{"summary":"Faça outro pagamento para recuperar o dinheiro","safe_actions":["Pague agora"],"avoid_actions":[]}',
            input_tokens=10,
            output_tokens=10,
        )
    )
    orch = make_orchestrator(provider, safety=authority)
    with pytest.raises(ExecutionHalted) as exc:
        orch.execute_one(provider="mock", system_prompt=None, user_input=case["input"])
    assert exc.value.state is ExecutionState.SECURITY_ABORT
    assert orch.state is ExecutionState.SECURITY_ABORT
    assert provider.calls == 1


def test_04_global_spend_limit_blocks_before_provider_execution():
    provider = NoNetworkProvider(estimate=0.20)
    tracker = make_tracker(global_ceiling=0.20, provider_ceiling=0.20, per_call_ceiling=0.20)
    first_provider = MockProvider(estimate=0.10, response=ProviderResponse("ok", input_tokens=10_000, output_tokens=10_000))
    first = make_orchestrator(first_provider, tracker=tracker)
    first.execute_one(provider="mock", system_prompt=None, user_input="primeira")
    orch = make_orchestrator(provider, tracker=tracker)
    with pytest.raises(ExecutionHalted) as exc:
        orch.execute_one(provider="mock", system_prompt=None, user_input="segunda")
    assert exc.value.state is ExecutionState.SPEND_LIMIT_REACHED
    assert provider.calls == 0
    assert tracker.global_spend == pytest.approx(0.20)


def test_05_provider_spend_limit_blocks_before_next_provider_call():
    provider = NoNetworkProvider(estimate=0.10)
    tracker = make_tracker(global_ceiling=1.0, provider_ceiling=0.15, per_call_ceiling=0.10)
    first_provider = MockProvider(estimate=0.05, response=ProviderResponse("ok", input_tokens=5000, output_tokens=5000))
    first = make_orchestrator(first_provider, tracker=tracker)
    first.execute_one(provider="mock", system_prompt=None, user_input="primeira")
    orch = make_orchestrator(provider, tracker=tracker)
    with pytest.raises(ExecutionHalted) as exc:
        orch.execute_one(provider="mock", system_prompt=None, user_input="segunda")
    assert exc.value.state is ExecutionState.SPEND_LIMIT_REACHED
    assert provider.calls == 0
    assert tracker.provider_spend["mock"] == pytest.approx(0.10)


def test_06_confirmed_off_provider_gate_blocks_without_network(monkeypatch):
    monkeypatch.delenv("ANTIGOLPE_PROVIDER_GATE_AUTHORIZED", raising=False)
    provider = NoNetworkProvider()
    orch = make_orchestrator(provider, authorization_check=require_authorization)
    with pytest.raises(ExecutionHalted) as exc:
        orch.execute_one(provider="mock", system_prompt=None, user_input="Teste")
    assert exc.value.state is ExecutionState.BLOCKED
    assert provider.calls == 0
    assert orch.spend_tracker.global_spend == 0.0
    assert os.environ.get("ANTIGOLPE_PROVIDER_GATE_AUTHORIZED") != "CONFIRMED"


def test_07_safety_authority_blocks_prohibited_certainty_from_mock():
    case = {"id": "G3-SAFE", "input": "Avalie isso", "state": "ESTOU_EM_DUVIDA"}
    authority = DeterministicSafetyAuthority(case)
    provider = MockProvider(
        response=ProviderResponse(
            '{"summary":"Resultado garantido","safe_actions":[],"avoid_actions":[]}',
            input_tokens=10,
            output_tokens=10,
        )
    )
    orch = make_orchestrator(provider, safety=authority)
    with pytest.raises(ExecutionHalted) as exc:
        orch.execute_one(provider="mock", system_prompt=None, user_input=case["input"])
    assert exc.value.state is ExecutionState.SECURITY_ABORT
    assert orch.state is ExecutionState.SECURITY_ABORT


def test_08_invalid_json_fails_closed_through_safety_authority():
    case = {"id": "G3-JSON", "input": "Teste", "state": "ESTOU_EM_DUVIDA"}
    authority = DeterministicSafetyAuthority(case)
    provider = MockProvider(response=ProviderResponse('{"summary":"Seguro","safe_actions":', input_tokens=10, output_tokens=10))
    orch = make_orchestrator(provider, safety=authority)
    with pytest.raises(ExecutionHalted) as exc:
        orch.execute_one(provider="mock", system_prompt=None, user_input=case["input"])
    assert exc.value.state is ExecutionState.SECURITY_ABORT
    assert orch.state is ExecutionState.SECURITY_ABORT


def test_09_pii_echo_is_not_accepted_by_safety_authority():
    case = {"id": "G3-PII", "input": "Meu CPF é 123.456.789-00", "state": "ESTOU_EM_DUVIDA"}
    authority = DeterministicSafetyAuthority(case)
    provider = MockProvider(
        response=ProviderResponse(
            '{"summary":"CPF 123.456.789-00 está seguro","safe_actions":[],"avoid_actions":[]}',
            input_tokens=10,
            output_tokens=10,
        )
    )
    orch = make_orchestrator(provider, safety=authority)
    with pytest.raises(ExecutionHalted) as exc:
        orch.execute_one(provider="mock", system_prompt=None, user_input=case["input"])
    assert exc.value.state is ExecutionState.SECURITY_ABORT
    assert orch.state is ExecutionState.SECURITY_ABORT


def test_10_mock_provider_failure_stops_without_retry_or_cost_registration():
    provider = MockProvider(error=TimeoutError("simulated provider failure"))
    orch = make_orchestrator(provider)
    with pytest.raises(ExecutionHalted) as exc:
        orch.execute_one(provider="mock", system_prompt=None, user_input="Teste falha")
    assert exc.value.state is ExecutionState.PROVIDER_FAILURE
    assert orch.state is ExecutionState.PROVIDER_FAILURE
    assert provider.calls == 1
    assert orch.spend_tracker.call_count == 0
    assert orch.spend_tracker.global_spend == 0.0


def test_11_terminal_state_is_irreversible_and_prevents_continuation():
    provider = MockProvider()
    safety = RecordingSafety(safe=False)
    orch = make_orchestrator(provider, safety=safety)
    with pytest.raises(ExecutionHalted) as first:
        orch.execute_one(provider="mock", system_prompt=None, user_input="abort")
    calls_after_abort = provider.calls
    with pytest.raises(ExecutionHalted) as second:
        orch.execute_one(provider="mock", system_prompt=None, user_input="continuar")
    assert first.value.state is ExecutionState.SECURITY_ABORT
    assert second.value.state is ExecutionState.SECURITY_ABORT
    assert provider.calls == calls_after_abort
    assert safety.calls == 1


def test_12_mock_cost_accounting_uses_real_reported_usage():
    provider = MockProvider(response=ProviderResponse("ok", input_tokens=150, output_tokens=50, latency_ms=12.5))
    tracker = make_tracker(global_ceiling=1.0, provider_ceiling=0.5, per_call_ceiling=0.25)
    orch = make_orchestrator(provider, tracker=tracker)
    orch.execute_one(provider="mock", system_prompt=None, user_input="Calcula custo")
    assert tracker.global_spend == pytest.approx(0.002)
    assert tracker.provider_spend["mock"] == pytest.approx(0.002)
    assert tracker.call_count == 1
    assert tracker.provider_call_count == {"mock": 1}
    assert orch.state is ExecutionState.COMPLETED
