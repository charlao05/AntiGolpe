"""Fail-closed authorization guard for real Provider Gate adapters."""

from __future__ import annotations

import os

from .adapters import ExternalProviderNotAuthorized, unavailable_provider

AUTH_ENV = "ANTIGOLPE_PROVIDER_GATE_AUTHORIZED"
AUTH_VALUE = "CONFIRMED"


def require_authorization() -> None:
    """Allow real provider execution only after explicit local authorization.

    The default is always denied. This function is intentionally checked by
    real adapters themselves so a caller cannot bypass the gate merely by
    importing an adapter directly.
    """
    if os.environ.get(AUTH_ENV) != AUTH_VALUE:
        raise ExternalProviderNotAuthorized(
            "Provider Gate is not authorized. Set ANTIGOLPE_PROVIDER_GATE_AUTHORIZED=CONFIRMED "
            "only after all governance prerequisites have been approved."
        )


__all__ = [
    "AUTH_ENV",
    "AUTH_VALUE",
    "ExternalProviderNotAuthorized",
    "require_authorization",
    "unavailable_provider",
]
