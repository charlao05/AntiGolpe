from backend.tests.provider_gate.no_network import NETWORK_EXECUTION_ENABLED, REAL_PROVIDERS_ENABLED


def test_network_and_real_providers_are_disabled():
    assert NETWORK_EXECUTION_ENABLED is False
    assert REAL_PROVIDERS_ENABLED is False
