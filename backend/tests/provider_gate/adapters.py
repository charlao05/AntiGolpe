"""Provider adapter interfaces for the sandbox.

Real adapters are intentionally unavailable until the Provider Gate governance
contract is fully approved. This file contains only a provider-neutral protocol.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ProviderResponse:
    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    latency_ms: float | None = None


class ProviderAdapter(Protocol):
    name: str

    def analyze(self, *, system_prompt: str | None, user_input: str) -> ProviderResponse:
        """Execute one provider call.

        Real implementations are intentionally not supplied in this phase.
        """
        ...


class ExternalProviderNotAuthorized(RuntimeError):
    """Raised when a real provider adapter is attempted before gate approval."""


def unavailable_provider(name: str) -> None:
    raise ExternalProviderNotAuthorized(
        f"Provider '{name}' is not authorized. Complete and approve the Provider Gate first."
    )
