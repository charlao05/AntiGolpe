"""Global financial authority for the Phase 5.1 execution experiment.

This module contains no provider SDK access and performs no network I/O.
There is exactly one tracker instance per complete experiment. Provider-level
spend is accounting inside the same global authority, never a separate tracker.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Final


class ExecutionState(str, Enum):
    READY = "READY"
    AUTHORIZED = "AUTHORIZED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    SPEND_LIMIT_REACHED = "SPEND_LIMIT_REACHED"
    SECURITY_ABORT = "SECURITY_ABORT"
    PROVIDER_FAILURE = "PROVIDER_FAILURE"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"


TERMINAL_STATES: Final[frozenset[ExecutionState]] = frozenset(
    {
        ExecutionState.BLOCKED,
        ExecutionState.SPEND_LIMIT_REACHED,
        ExecutionState.SECURITY_ABORT,
        ExecutionState.PROVIDER_FAILURE,
        ExecutionState.CONFIGURATION_ERROR,
    }
)


class SpendTrackerError(RuntimeError):
    """Base error for financial-governance failures."""


class ConfigurationError(SpendTrackerError):
    """Raised for invalid or inconsistent financial configuration."""


class SpendLimitReached(SpendTrackerError):
    """Raised when a requested or recorded call violates a financial ceiling."""


class InvalidUsage(SpendTrackerError):
    """Raised when real usage/cost cannot be trusted for accounting."""


@dataclass(frozen=True)
class SpendLimits:
    """Immutable closed financial configuration for one experiment."""

    global_ceiling: float
    provider_ceiling: float
    per_call_ceiling: float

    def __post_init__(self) -> None:
        values = (
            ("GLOBAL_CEILING", self.global_ceiling),
            ("PROVIDER_CEILING", self.provider_ceiling),
            ("PER_CALL_CEILING", self.per_call_ceiling),
        )
        for name, value in values:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ConfigurationError(f"{name} must be numeric")
            if not math.isfinite(float(value)) or float(value) <= 0:
                raise ConfigurationError(f"{name} must be finite and greater than zero")
        if self.provider_ceiling > self.global_ceiling:
            raise ConfigurationError("PROVIDER_CEILING cannot exceed GLOBAL_CEILING")
        if self.per_call_ceiling > self.provider_ceiling:
            raise ConfigurationError("PER_CALL_CEILING cannot exceed PROVIDER_CEILING")


class SpendTracker:
    """Single global financial authority for a serial experiment."""

    def __init__(self, *, global_ceiling: float, provider_ceiling: float, per_call_ceiling: float) -> None:
        self.limits = SpendLimits(global_ceiling, provider_ceiling, per_call_ceiling)
        self.global_spend = 0.0
        self.provider_spend: dict[str, float] = {}
        self.call_count = 0
        self.provider_call_count: dict[str, int] = {}
        self.state = ExecutionState.READY

    @property
    def is_terminal(self) -> bool:
        return self.state in TERMINAL_STATES

    def _require_nonterminal(self) -> None:
        if self.is_terminal:
            raise SpendTrackerError(f"Execution is terminal: {self.state.value}")

    @staticmethod
    def _validate_provider(provider: str) -> str:
        if not isinstance(provider, str) or not provider.strip():
            raise ConfigurationError("provider must be a non-empty string")
        return provider.strip()

    @staticmethod
    def _validate_cost(value: float, field: str) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise InvalidUsage(f"{field} must be numeric")
        value = float(value)
        if not math.isfinite(value) or value < 0:
            raise InvalidUsage(f"{field} must be finite and non-negative")
        return value

    def authorize(self, provider: str, estimated_worst_case: float) -> bool:
        """Authorize one specific call using all three ceiling conditions."""
        self._require_nonterminal()
        provider = self._validate_provider(provider)
        estimated_worst_case = self._validate_cost(estimated_worst_case, "estimated_worst_case")

        provider_spend = self.provider_spend.get(provider, 0.0)
        allowed = (
            self.global_spend + estimated_worst_case <= self.limits.global_ceiling
            and provider_spend + estimated_worst_case <= self.limits.provider_ceiling
            and estimated_worst_case <= self.limits.per_call_ceiling
        )
        if not allowed:
            self.state = ExecutionState.SPEND_LIMIT_REACHED
            return False

        self.state = ExecutionState.AUTHORIZED
        return True

    def begin_call(self) -> None:
        """Consume the one-call AUTHORIZED state immediately before adapter execution."""
        if self.state != ExecutionState.AUTHORIZED:
            raise SpendTrackerError(
                f"begin_call requires AUTHORIZED state, got {self.state.value}"
            )
        self.state = ExecutionState.RUNNING

    def register(self, provider: str, real_cost: float) -> None:
        """Record real provider cost; real usage is authoritative over estimates."""
        self._require_nonterminal()
        if self.state != ExecutionState.RUNNING:
            raise SpendTrackerError(
                f"register requires RUNNING state, got {self.state.value}"
            )
        provider = self._validate_provider(provider)
        real_cost = self._validate_cost(real_cost, "real_cost")

        new_global = self.global_spend + real_cost
        new_provider = self.provider_spend.get(provider, 0.0) + real_cost

        # Account the real cost before halting if a provider's actual usage
        # invalidates a preventive estimate. A known cost is never discarded.
        self.global_spend = new_global
        self.provider_spend[provider] = new_provider
        self.call_count += 1
        self.provider_call_count[provider] = self.provider_call_count.get(provider, 0) + 1

        if (
            real_cost > self.limits.per_call_ceiling
            or new_provider > self.limits.provider_ceiling
            or new_global > self.limits.global_ceiling
        ):
            self.state = ExecutionState.SPEND_LIMIT_REACHED
            raise SpendLimitReached("Real call cost exceeded an experiment ceiling")

        self.state = ExecutionState.COMPLETED

    def abort_security(self) -> None:
        """Apply the non-bypassable D1-D5 global stop."""
        if self.is_terminal:
            return
        self.state = ExecutionState.SECURITY_ABORT

    def fail_provider(self) -> None:
        if self.is_terminal:
            return
        self.state = ExecutionState.PROVIDER_FAILURE

    def fail_configuration(self) -> None:
        if self.is_terminal:
            return
        self.state = ExecutionState.CONFIGURATION_ERROR

    def block(self) -> None:
        if self.is_terminal:
            return
        self.state = ExecutionState.BLOCKED


__all__ = [
    "ConfigurationError",
    "ExecutionState",
    "InvalidUsage",
    "SpendLimitReached",
    "SpendTracker",
    "SpendTrackerError",
    "SpendLimits",
    "TERMINAL_STATES",
]
