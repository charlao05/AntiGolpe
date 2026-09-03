from backend.tests.provider_gate.runner import load_cases, plan_runs
from backend.tests.provider_gate.adapters import ExternalProviderNotAuthorized, unavailable_provider


def test_frozen_benchmark_has_exactly_30_cases():
    cases = load_cases()
    assert len(cases) == 30


def test_dry_run_plans_three_phases_without_network():
    runs = plan_runs()
    assert len(runs) == 90
    assert {run.phase for run in runs} == {
        "pure",
        "framework",
        "framework_structured",
    }


def test_real_provider_is_blocked_until_gate_approval():
    try:
        unavailable_provider("openai")
    except ExternalProviderNotAuthorized as exc:
        assert "not authorized" in str(exc).lower()
    else:
        raise AssertionError("real provider must remain blocked")
