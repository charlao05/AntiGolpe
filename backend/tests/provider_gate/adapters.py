"""Provider-neutral interfaces for the Provider Gate experiment.

Real provider adapters remain local-only and explicitly gated. The adapter
contract exposes provider-specific cost estimation and real-cost extraction;
financial authorization and accounting remain exclusively in SpendTracker.
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

    def estimate_worst_case_cost(self, *, system_prompt: str | None, user_input: str) -> float:
        """Return the provider-specific worst-case cost estimate for one call."""
        ...

    def analyze(self, *, system_prompt: str | None, user_input: str) -> ProviderResponse:
        """Execute exactly one provider call after external authorization."""
        ...

    def calculate_real_cost(self, response: ProviderResponse) -> float:
        """Extract the definitive real cost from provider-reported usage."""
        ...


class ExternalProviderNotAuthorized(RuntimeError):
    """Raised when a real provider adapter is attempted before gate approval."""


def unavailable_provider(name: str) -> None:
    raise ExternalProviderNotAuthorized(
        f"Provider '{name}' is not authorized. Complete and approve the Provider Gate first."
    )
