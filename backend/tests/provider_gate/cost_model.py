"""Provider Gate cost placeholders.

No provider pricing is hardcoded here. Pricing must come from the approved,
versioned Provider Gate configuration and documented sources before execution.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CostEstimate:
    input_tokens: int
    output_tokens: int
    input_usd: float
    output_usd: float

    @property
    def total_usd(self) -> float:
        return self.input_usd + self.output_usd
