"""Provider Gate scoring data structures.

No model judgment is performed here yet; this module only defines the
provider-neutral result shape for later audited scoring.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DeterministicScores:
    d1: bool | None = None
    d2: bool | None = None
    d3: bool | None = None
    d4: bool | None = None
    d5: bool | None = None
    d6: bool | None = None


@dataclass(frozen=True)
class EvaluativeScores:
    e1: int | None = None
    e2: int | None = None
    e3: int | None = None
    e4: int | None = None
