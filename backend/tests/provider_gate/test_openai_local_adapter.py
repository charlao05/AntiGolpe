import os

import pytest

from backend.tests.provider_gate.guard import ExternalProviderNotAuthorized
from backend.tests.provider_gate.openai_local_adapter import (
    MissingApiKey,
    OpenAIAdapter,
)


def test_adapter_fails_closed_without_confirmed_even_with_api_key(monkeypatch):
    """The API key must not bypass the Provider Gate authorization guard."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-key-for-testing")
    monkeypatch.delenv("ANTIGOLPE_PROVIDER_GATE_AUTHORIZED", raising=False)

    with pytest.raises(ExternalProviderNotAuthorized):
        OpenAIAdapter(model="gpt-4o-mini")


def test_adapter_checks_guard_before_reading_api_key(monkeypatch):
    """Authorization must fail before the adapter attempts credential access."""
    monkeypatch.delenv("ANTIGOLPE_PROVIDER_GATE_AUTHORIZED", raising=False)

    original_environ = os.environ

    class GuardFirstEnviron(dict):
        def get(self, key, default=None):
            if key == "OPENAI_API_KEY":
                raise AssertionError("API key was read before Provider Gate authorization")
            return original_environ.get(key, default)

    monkeypatch.setattr(os, "environ", GuardFirstEnviron())

    with pytest.raises(ExternalProviderNotAuthorized):
        OpenAIAdapter(model="gpt-4o-mini")


def test_adapter_requires_api_key_after_authorization(monkeypatch):
    """With authorization present, a missing credential fails locally before network use."""
    monkeypatch.setenv("ANTIGOLPE_PROVIDER_GATE_AUTHORIZED", "CONFIRMED")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(MissingApiKey):
        OpenAIAdapter(model="gpt-4o-mini")
