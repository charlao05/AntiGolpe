from backend.tests.provider_gate.cost_model import CostEstimate


def test_cost_estimate_is_provider_neutral():
    estimate = CostEstimate(input_tokens=500, output_tokens=300, input_usd=0.01, output_usd=0.02)
    assert estimate.total_usd == 0.03
