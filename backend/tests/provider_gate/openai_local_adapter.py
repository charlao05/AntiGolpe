"""Real OpenAI adapter for the Provider Gate LOCAL dry run.

Safety rules enforced by this module:
- This file is NEVER imported by backend/app, by CI workflows, or by the
  default pytest suite. It must be imported explicitly and manually by a
  human running the harness on their own machine.
- The API key is read only from the OPENAI_API_KEY environment variable.
  It is never hardcoded, never logged, never printed, and never included
  in any exception message.
- No raw prompt or raw response is persisted to disk by this module. The
  caller (runner) is responsible for writing only metadata/scores to
  backend/tests/provider_gate/results/, which is gitignored.
- A hard local spend ceiling is enforced (see MAX_TOTAL_USD / MAX_CALL_USD)
  as required by docs/PROVIDER_GATE.md Section 20.1.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass

from .adapters import ProviderResponse

# Hard local ceilings, mirroring docs/PROVIDER_GATE.md Section 20.1.
MAX_TOTAL_USD = 3.00  # per-provider ceiling for this experiment
MAX_CALL_USD = 0.50


class SpendCeilingExceeded(RuntimeError):
    """Raised when the local spend ceiling would be exceeded."""


class MissingApiKey(RuntimeError):
    """Raised when OPENAI_API_KEY is not set in the environment."""


@dataclass
class SpendTracker:
    """In-memory only. Never persisted, never logged."""

    total_usd: float = 0.0

    def register(self, call_usd: float) -> None:
        if call_usd > MAX_CALL_USD:
            raise SpendCeilingExceeded(
                f"Single call estimated at ${call_usd:.4f} exceeds per-call ceiling "
                f"of ${MAX_CALL_USD:.2f}."
            )
        if self.total_usd + call_usd > MAX_TOTAL_USD:
            raise SpendCeilingExceeded(
                f"Running total ${self.total_usd:.4f} + ${call_usd:.4f} would exceed "
                f"the ${MAX_TOTAL_USD:.2f} ceiling for this provider."
            )
        self.total_usd += call_usd


class OpenAIAdapter:
    """Real OpenAI Chat Completions adapter. Local execution only.

    Usage (from a local shell, never from CI):

        export OPENAI_API_KEY=sk-...
        python -c "
        from backend.tests.provider_gate.openai_local_adapter import OpenAIAdapter
        a = OpenAIAdapter(model='gpt-4o-mini')
        print(a.analyze(system_prompt=None, user_input='ping'))
        "
    """

    name = "openai"

    def __init__(self, model: str = "gpt-4o-mini", spend_tracker: SpendTracker | None = None) -> None:
        self.model = model
        self._spend_tracker = spend_tracker or SpendTracker()
        self._api_key = os.environ.get("OPENAI_API_KEY")
        if not self._api_key:
            raise MissingApiKey(
                "OPENAI_API_KEY is not set. Export it in your local shell only; "
                "never hardcode it and never commit it."
            )

    def _client(self):
        # Imported lazily so that importing this module never requires the
        # openai package to be installed in environments that only run the
        # dry-run suite (requirements.txt stays dependency-free by design).
        from openai import OpenAI

        return OpenAI(api_key=self._api_key)

    @staticmethod
    def _estimate_cost_usd(input_tokens: int, output_tokens: int) -> float:
        # Conservative placeholder rates; replace with the exact published
        # rate for the model/endpoint used before relying on this for
        # anything beyond a local safety ceiling.
        input_rate = 0.15 / 1_000_000
        output_rate = 0.60 / 1_000_000
        return input_tokens * input_rate + output_tokens * output_rate

    def analyze(self, *, system_prompt: str | None, user_input: str) -> ProviderResponse:
        client = self._client()
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_input})

        start = time.monotonic()
        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
        )
        latency_ms = (time.monotonic() - start) * 1000

        usage = getattr(response, "usage", None)
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
