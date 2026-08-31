import os

import pytest

from backend.tests.provider_gate.guard import ExternalProviderNotAuthorized
from backend.tests.provider_gate.openai_local_adapter import (
    MissingApiKey,
    OpenAIAdapter,
    SpendCeilingExceeded,
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


def test_preflight_spend_rejects_before_client_creation(monkeypatch):
    """A worst-case request over the local ceiling is rejected before network access."""
    monkeypatch.setenv("ANTIGOLPE_PROVIDER_GATE_AUTHORIZED", "CONFIRMED")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-key-for-testing")

    adapter = OpenAIAdapter(model="gpt-4o-mini")

    def fail_if_client_created():
        raise AssertionError("OpenAI client was created before spend preflight")

    monkeypatch.setattr(adapter, "_client", fail_if_client_created)

    oversized_input = "x" * 3_500_000
    with pytest.raises(SpendCeilingExceeded):
        adapter.analyze(system_prompt=None, user_input=oversized_input)
