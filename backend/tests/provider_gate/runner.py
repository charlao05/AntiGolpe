"""Dry-run harness for the isolated Provider Gate experiment.

This module intentionally performs NO network calls and imports NO provider SDKs.
Its purpose is to validate benchmark loading, run planning and reproducible metadata
before real-provider execution is authorized.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BENCHMARK_PATH = ROOT / "tests" / "fixtures" / "benchmark_cases.json"


@dataclass(frozen=True)
class PlannedRun:
    case_id: str
    phase: str


def load_cases(path: Path = BENCHMARK_PATH) -> list[dict]:
    cases = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(cases, list) or len(cases) != 30:
        raise ValueError("Provider Gate requires exactly the frozen 30 benchmark cases")
    return cases


def plan_runs(cases: list[dict] | None = None) -> list[PlannedRun]:
    cases = load_cases() if cases is None else cases
    phases = ("pure", "framework", "framework_structured")
    return [PlannedRun(case["id"], phase) for phase in phases for case in cases]


def main() -> int:
    cases = load_cases()
    runs = plan_runs(cases)
    print(f"DRY RUN ONLY: {len(cases)} frozen cases")
    print(f"Planned experiment runs: {len(runs)}")
    print("External providers: DISABLED")
    print("API keys: NOT READ")
    print("Network: NOT USED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
