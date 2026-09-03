from backend.tests.provider_gate.adapters import ExternalProviderNotAuthorized, unavailable_provider


def test_external_provider_guard_is_explicit():
    try:
        unavailable_provider("anthropic")
    except ExternalProviderNotAuthorized:
        return
    raise AssertionError("external provider access must remain blocked")
