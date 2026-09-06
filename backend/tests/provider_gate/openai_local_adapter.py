"""Real OpenAI adapter for the Provider Gate LOCAL experiment.

This adapter is deliberately provider-specific and contains no experiment
budget authority. Financial preflight and post-call accounting belong to the
single global SpendTracker coordinated by ExecutionOrchestrator.

Safety rules enforced by this module:
- This file is NEVER imported by backend/app, by CI workflows, or by the
  default production runtime. It is intended for explicit local execution only.
- Provider Gate authorization is checked before the API key is read.
- The API key is read only from OPENAI_API_KEY and is never logged or persisted.
- No raw prompt or raw response is persisted by this module.
- Pre-call estimation is exposed to the orchestrator; it is not authorization.
- Real usage is exposed to the orchestrator for definitive accounting.
"""
from __future__ import annotations

import os
import time
from typing import Any

from .adapters import ProviderResponse
from .guard import require_authorization
from .spend_tracker import ConfigurationError, InvalidUsage

MAX_OUTPUT_TOKENS = 800
INPUT_USD_PER_MILLION = 0.15
OUTPUT_USD_PER_MILLION = 0.60

# Provider/model pricing is adapter configuration, not experiment ceilings.
MODEL_PRICING: dict[str, tuple[float, float]] = {
    "gpt-4o-mini": (INPUT_USD_PER_MILLION, OUTPUT_USD_PER_MILLION),
}


class MissingApiKey(RuntimeError):
    """Raised when OPENAI_API_KEY is not set in the environment."""


class ProviderUsageError(InvalidUsage):
    """Raised when provider usage is absent, incomplete, or inconsistent."""


class PricingConfigurationError(ConfigurationError):
    """Raised when no approved price mapping exists for the configured model."""


class OpenAIAdapter:
    """Real OpenAI Chat Completions adapter. Local execution only."""

    name = "openai"

    def __init__(self, model: str = "gpt-4o-mini") -> None:
        # Structural fail-closed point: authorization is checked before any
        # attempt to read the API key.
        require_authorization()
        self.model = model
        self._api_key = os.environ.get("OPENAI_API_KEY")
        if not self._api_key:
            raise MissingApiKey(
                "OPENAI_API_KEY is not set. Export it in your local shell only; "
                "never hardcode it and never commit it."
            )

    def _client(self):
        from openai import OpenAI

        return OpenAI(api_key=self._api_key)

    def _pricing(self) -> tuple[float, float]:
        try:
            return MODEL_PRICING[self.model]
        except KeyError as exc:
            raise PricingConfigurationError(
                f"No approved pricing mapping for OpenAI model '{self.model}'"
            ) from exc

    def _estimate_cost_usd(self, input_tokens: int, output_tokens: int) -> float:
        input_price, output_price = self._pricing()
        return (
            input_tokens * input_price / 1_000_000
            + output_tokens * output_price / 1_000_000
        )

    @staticmethod
    def _conservative_input_token_estimate(messages: list[dict[str, str]]) -> int:
        """Estimate input tokens using UTF-8 bytes as a conservative proxy.

        This is a pre-call estimate only. It is not a billing tokenizer and
        must never replace provider-reported usage for final accounting.
        """
        content_bytes = sum(
            len(message.get("content", "").encode("utf-8")) for message in messages
        )
        message_overhead = 64 * len(messages)
        return content_bytes + message_overhead

    def estimate_worst_case_cost(self, *, system_prompt: str | None, user_input: str) -> float:
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_input})
        estimated_input_tokens = self._conservative_input_token_estimate(messages)
        return self._estimate_cost_usd(estimated_input_tokens, MAX_OUTPUT_TOKENS)

    def calculate_real_cost(self, response: ProviderResponse) -> float:
        input_tokens = response.input_tokens
        output_tokens = response.output_tokens
        if input_tokens is None or output_tokens is None:
            raise ProviderUsageError(
                "Provider usage is absent or incomplete; real cost cannot be determined"
            )
        if not isinstance(input_tokens, int) or not isinstance(output_tokens, int):
            raise ProviderUsageError("Provider usage token counts are not integers")
        if input_tokens < 0 or output_tokens < 0:
            raise ProviderUsageError("Provider usage token counts cannot be negative")
        return self._estimate_cost_usd(input_tokens, output_tokens)

    def analyze(self, *, system_prompt: str | None, user_input: str) -> ProviderResponse:
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_input})

        # The ExecutionOrchestrator has already completed financial preflight
        # and moved the global tracker to RUNNING before this method is called.
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

        text = response.choices[0].message.content or ""
        return ProviderResponse(
            text=text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
        )


__all__ = [
    "MAX_OUTPUT_TOKENS",
    "MissingApiKey",
    "MODEL_PRICING",
    "OpenAIAdapter",
    "PricingConfigurationError",
    "ProviderUsageError",
]
