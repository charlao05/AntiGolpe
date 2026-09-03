"""Real OpenAI adapter for the Provider Gate LOCAL experiment.

Safety rules enforced by this module:
- This file is NEVER imported by backend/app, by CI workflows, or by the
  default production runtime. It is intended for explicit local execution only.
- Provider Gate authorization is checked before the API key is read.
- The API key is read only from OPENAI_API_KEY and is never logged or persisted.
- No raw prompt or raw response is persisted by this module.
- A conservative pre-call spend check combines a fixed output-token ceiling
  with an upper-bound input-token estimate. The tracker also records actual
  post-call usage and acts as a circuit breaker for subsequent calls.

The provider account's own billing controls remain an independent safety layer.
The local pre-call estimate is a guard, not a substitute for provider billing
limits or final invoice accounting.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

from .adapters import ProviderResponse
from .guard import require_authorization

MAX_TOTAL_USD = 3.00
MAX_CALL_USD = 0.50
MAX_OUTPUT_TOKENS = 800
INPUT_USD_PER_MILLION = 0.15
OUTPUT_USD_PER_MILLION = 0.60


class SpendCeilingExceeded(RuntimeError):
    """Raised when a local spend ceiling would be exceeded."""


class MissingApiKey(RuntimeError):
    """Raised when OPENAI_API_KEY is not set in the environment."""


@dataclass
class SpendTracker:
    """In-memory spend accounting; never persisted or logged."""

    total_usd: float = 0.0

    def assert_within_ceiling(self, worst_case_call_usd: float) -> None:
        """Reject a call before network access when its worst case is too high."""
        if worst_case_call_usd > MAX_CALL_USD:
            raise SpendCeilingExceeded(
                f"Worst-case call estimate ${worst_case_call_usd:.4f} exceeds "
                f"the ${MAX_CALL_USD:.2f} per-call ceiling."
            )
        if self.total_usd + worst_case_call_usd > MAX_TOTAL_USD:
            raise SpendCeilingExceeded(
                f"Running total ${self.total_usd:.4f} plus worst-case call "
                f"${worst_case_call_usd:.4f} would exceed the ${MAX_TOTAL_USD:.2f} "
                "provider ceiling."
            )

    def register(self, actual_call_usd: float) -> None:
        """Record actual usage returned by the provider after a completed call."""
        self.total_usd += actual_call_usd
        if self.total_usd > MAX_TOTAL_USD:
            raise SpendCeilingExceeded(
                f"Recorded spend ${self.total_usd:.4f} exceeded the "
                f"${MAX_TOTAL_USD:.2f} provider ceiling."
            )


class OpenAIAdapter:
    """Real OpenAI Chat Completions adapter. Local execution only."""

    name = "openai"

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        spend_tracker: SpendTracker | None = None,
    ) -> None:
        # Structural fail-closed point: authorization is checked before any
        # attempt to read the API key.
        require_authorization()
        self.model = model
        self._spend_tracker = spend_tracker or SpendTracker()
        self._api_key = os.environ.get("OPENAI_API_KEY")
        if not self._api_key:
            raise MissingApiKey(
                "OPENAI_API_KEY is not set. Export it in your local shell only; "
                "never hardcode it and never commit it."
            )

    def _client(self):
        from openai import OpenAI

        return OpenAI(api_key=self._api_key)

    @staticmethod
    def _estimate_cost_usd(input_tokens: int, output_tokens: int) -> float:
        return (
            input_tokens * INPUT_USD_PER_MILLION / 1_000_000
            + output_tokens * OUTPUT_USD_PER_MILLION / 1_000_000
        )

    @staticmethod
    def _conservative_input_token_estimate(messages: list[dict[str, str]]) -> int:
        """Conservative local estimate used only for the pre-call budget guard.

        UTF-8 byte length is intentionally used as an upper-bound-oriented
        approximation for this fixed synthetic benchmark. It is not a billing
        tokenizer and must not be used as final accounting.
        """
        content_bytes = sum(
            len(message.get("content", "").encode("utf-8")) for message in messages
        )
        message_overhead = 64 * len(messages)
        return content_bytes + message_overhead

    def _preflight_spend(self, messages: list[dict[str, str]]) -> None:
        estimated_input_tokens = self._conservative_input_token_estimate(messages)
        worst_case_cost = self._estimate_cost_usd(
            estimated_input_tokens,
            MAX_OUTPUT_TOKENS,
        )
        self._spend_tracker.assert_within_ceiling(worst_case_cost)

    def analyze(self, *, system_prompt: str | None, user_input: str) -> ProviderResponse:
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_input})

        # Budget check happens before client creation and before network access.
        self._preflight_spend(messages)
        client = self._client()

        start = time.monotonic()
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_completion_tokens=MAX_OUTPUT_TOKENS,
            temperature=0.0,
        )
        latency_ms = (time.monotonic() - start) * 1000

        usage: Any = getattr(response, "usage", None)
        input_tokens = getattr(usage, "prompt_tokens", None) if usage else None
        output_tokens = getattr(usage, "completion_tokens", None) if usage else None

        if input_tokens is not None and output_tokens is not None:
            estimated_cost = self._estimate_cost_usd(input_tokens, output_tokens)
            self._spend_tracker.register(estimated_cost)

        text = response.choices[0].message.content or ""

        return ProviderResponse(
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
        )
