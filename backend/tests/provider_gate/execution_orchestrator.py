"""Fail-closed, serial coordinator for the Phase 5.1 experiment.

The orchestrator is subordinate to three authorities:
- Provider Gate: environment/network authorization.
- SpendTracker: financial authorization and accounting.
- Safety authority: D1-D5 critical safety decision.

It owns no provider-specific pricing, safety heuristics, or financial ceilings.
It performs no network I/O itself and never activates Provider Gate authorization.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from .adapters import ProviderAdapter, ProviderResponse
from .guard import ExternalProviderNotAuthorized, require_authorization
from .spend_tracker import (
    ConfigurationError,
    ExecutionState,
    InvalidUsage,
    SpendLimitReached,
    SpendTracker,
    SpendTrackerError,
)


class AdapterWithCosting(ProviderAdapter, Protocol):
    def estimate_worst_case_cost(self, *, system_prompt: str | None, user_input: str) -> float:
        ...

    def calculate_real_cost(self, response: ProviderResponse) -> float:
        ...


class SafetyAuthority(Protocol):
    """External D1-D5 authority. False means a critical safety failure."""

    def evaluate(self, response: ProviderResponse) -> bool:
        ...


class IncidentRecorder(Protocol):
    """Audit sink; implementations must not persist raw prompts/responses."""

    def record(self, *, provider: str, error_type: str, state: ExecutionState) -> None:
        ...


@dataclass(frozen=True)
class ExecutionIncident:
    provider: str
    error_type: str
    state: ExecutionState


class ExecutionHalted(RuntimeError):
    """Raised when the experiment enters a terminal state."""

    def __init__(self, state: ExecutionState, message: str) -> None:
        super().__init__(message)
        self.state = state


class _NullIncidentRecorder:
    def record(self, *, provider: str, error_type: str, state: ExecutionState) -> None:
        return None


class ExecutionOrchestrator:
    """One global SpendTracker, one call at a time, with no auto-retry."""

    def __init__(
        self,
        *,
        providers: dict[str, AdapterWithCosting],
        spend_tracker: SpendTracker,
        safety_authority: SafetyAuthority,
        incident_recorder: IncidentRecorder | None = None,
        authorization_check: Callable[[], None] = require_authorization,
    ) -> None:
        if not callable(authorization_check):
            spend_tracker.fail_configuration()
            raise ConfigurationError("authorization_check must be callable")
        if not providers:
            spend_tracker.fail_configuration()
            raise ConfigurationError("At least one provider must be configured")
        for name, adapter in providers.items():
            if not isinstance(name, str) or not name.strip() or adapter is None:
                spend_tracker.fail_configuration()
                raise ConfigurationError("Every configured provider must have a non-empty name and adapter")
            if getattr(adapter, "name", None) != name:
                spend_tracker.fail_configuration()
                raise ConfigurationError(f"Provider key/name mismatch for '{name}'")
            if not callable(getattr(adapter, "estimate_worst_case_cost", None)):
                spend_tracker.fail_configuration()
                raise ConfigurationError(f"Provider '{name}' has no worst-case cost estimator")
            if not callable(getattr(adapter, "calculate_real_cost", None)):
                spend_tracker.fail_configuration()
                raise ConfigurationError(f"Provider '{name}' has no real-cost calculator")

        if safety_authority is None or not callable(getattr(safety_authority, "evaluate", None)):
            spend_tracker.fail_configuration()
            raise ConfigurationError("A D1-D5 SafetyAuthority is required")

        self.providers = dict(providers)
        self.spend_tracker = spend_tracker
        self.safety_authority = safety_authority
        self.incident_recorder = incident_recorder or _NullIncidentRecorder()
        self._authorization_check = authorization_check

    @property
    def state(self) -> ExecutionState:
        return self.spend_tracker.state

    @property
    def is_terminal(self) -> bool:
        return self.spend_tracker.is_terminal

    def _halt(self, state: ExecutionState, message: str) -> None:
        raise ExecutionHalted(state, message)

    def execute_one(self, *, provider: str, system_prompt: str | None, user_input: str) -> ProviderResponse:
        """Execute exactly one call. Every call receives a fresh financial preflight."""
        if self.is_terminal:
            self._halt(self.state, f"Execution already terminal: {self.state.value}")
        if self.state not in {ExecutionState.READY, ExecutionState.COMPLETED}:
            self._halt(self.state, f"Execution cannot start from {self.state.value}")
        if not isinstance(provider, str) or not provider.strip() or provider not in self.providers:
            self.spend_tracker.block()
            self._halt(ExecutionState.BLOCKED, "Provider is missing or not configured")

        adapter = self.providers[provider]
        try:
            estimated_worst_case = adapter.estimate_worst_case_cost(
                system_prompt=system_prompt,
                user_input=user_input,
            )
        except (ConfigurationError, InvalidUsage) as exc:
            self.spend_tracker.fail_configuration()
            self._record(provider, type(exc).__name__)
            self._halt(ExecutionState.CONFIGURATION_ERROR, str(exc))

        try:
            authorized = self.spend_tracker.authorize(provider, estimated_worst_case)
        except SpendTrackerError as exc:
            self.spend_tracker.fail_configuration()
            self._record(provider, type(exc).__name__)
            self._halt(ExecutionState.CONFIGURATION_ERROR, str(exc))

        if not authorized:
            self._record(provider, "SpendLimitReached")
            self._halt(ExecutionState.SPEND_LIMIT_REACHED, "Financial preflight rejected the call")

        # Provider Gate remains a separate environment authority. The
        # orchestrator can consult it, but cannot set CONFIRMED itself.
        try:
            self._authorization_check()
        except ExternalProviderNotAuthorized as exc:
            self.spend_tracker.block()
            self._record(provider, type(exc).__name__)
            self._halt(ExecutionState.BLOCKED, str(exc))

        self.spend_tracker.begin_call()

        try:
            response = adapter.analyze(system_prompt=system_prompt, user_input=user_input)
        except Exception as exc:
            # Network was already reachable/attempted: incident first, then stop.
            self._record(provider, type(exc).__name__)
            self.spend_tracker.fail_provider()
            self._halt(ExecutionState.PROVIDER_FAILURE, "Provider execution failed after network authorization")

        try:
            real_cost = adapter.calculate_real_cost(response)
        except InvalidUsage as exc:
            self._record(provider, type(exc).__name__)
            self.spend_tracker.fail_provider()
            self._halt(ExecutionState.PROVIDER_FAILURE, str(exc))
        except ConfigurationError as exc:
            self._record(provider, type(exc).__name__)
            self.spend_tracker.fail_configuration()
            self._halt(ExecutionState.CONFIGURATION_ERROR, str(exc))

        try:
            self.spend_tracker.register(provider, real_cost)
        except InvalidUsage as exc:
            # A malformed cost returned by an adapter is itself a post-network
            # provider/accounting failure. Never leave the experiment RUNNING.
            self._record(provider, type(exc).__name__)
            self.spend_tracker.fail_provider()
            self._halt(ExecutionState.PROVIDER_FAILURE, str(exc))
        except SpendLimitReached as exc:
            # The real cost has already been accounted by SpendTracker. Safety
            # is checked below and can supersede this budget terminal state.
            spend_limit_failure = exc
        else:
            spend_limit_failure = None

        try:
            safety_ok = self.safety_authority.evaluate(response)
        except Exception as exc:
            self._record(provider, type(exc).__name__)
            self.spend_tracker.abort_security()
            self._halt(ExecutionState.SECURITY_ABORT, "Safety authority failed closed")

        if not safety_ok:
            self._record(provider, "D1-D5")
            # Security has absolute precedence over budget state.
            self.spend_tracker.abort_security()
            self._halt(ExecutionState.SECURITY_ABORT, "Critical D1-D5 safety failure")

        if spend_limit_failure is not None:
            self._record(provider, type(spend_limit_failure).__name__)
            self._halt(ExecutionState.SPEND_LIMIT_REACHED, str(spend_limit_failure))

        return response

    def _record(self, provider: str, error_type: str) -> None:
        self.incident_recorder.record(
            provider=provider,
            error_type=error_type,
            state=self.spend_tracker.state,
        )


__all__ = [
    "AdapterWithCosting",
    "ExecutionHalted",
    "ExecutionIncident",
    "ExecutionOrchestrator",
    "IncidentRecorder",
    "SafetyAuthority",
]
