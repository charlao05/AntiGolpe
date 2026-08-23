"""Provider-neutral latency measurement types for the future harness."""
from dataclasses import dataclass


@dataclass(frozen=True)
class LatencySample:
    elapsed_ms: float

    def as_dict(self) -> dict[str, float]:
        return {"elapsed_ms": self.elapsed_ms}
