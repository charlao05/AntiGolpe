"""Sandbox experimental do Provider Gate (Fase 4).

Este script NAO faz parte da aplicacao de producao (main.py) e NAO e
executado pelo CI. Ele existe para permitir comparar, de forma isolada e
controlada, candidatos a LLMProvider (ex.: OpenAI, Claude, Gemini) contra o
benchmark congelado de 30 casos, sem qualquer risco de expor chaves ou de
integrar um provider real em producao antes de passar no gate.

Como usar (local, nunca em CI/producao):
    export OPENAI_API_KEY=...        # opcional, somente no seu ambiente
    python backend/tests/sandbox_provider_gate.py --provider mock
    python backend/tests/sandbox_provider_gate.py --provider openai

Regras de seguranca (Master Brief v2.0):
    - Nenhuma chave de API e lida de arquivo de codigo ou commit; somente de
      variaveis de ambiente definidas manualmente pelo operador.
    - Nenhum provider real e importado por padrao; o import so ocorre se o
      candidato correspondente for explicitamente selecionado via --provider.
    - Este script nunca deve ser referenciado por main.py nem pelo pipeline
      de CI (ci.yml); e uma ferramenta manual de avaliacao.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Protocol

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.providers import LLMProvider, MockProvider  # noqa: E402
from app.schema import AnalyzeRequest, RiskLevel, UserState  # noqa: E402

BENCHMARK_PATH = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "benchmark_cases.json"

# Estados que, segundo o objetivo do caso, NUNCA podem receber recomendacao
# de pagamento ou classificacao de baixo risco (ver campo critical_failure).
SAFE_LOW_RISK_LEVELS = {RiskLevel.NAO_DETERMINADO, RiskLevel.ATENCAO}


@dataclass
class CaseResult:
    case_id: str
    risk_level: str
    latency_ms: float
    critical_failure_triggered: bool
    error: str | None = None


@dataclass
class ProviderReport:
    name: str
    external: bool
    results: list[CaseResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def critical_failures(self) -> int:
        return sum(1 for r in self.results if r.critical_failure_triggered)

    @property
    def errors(self) -> int:
        return sum(1 for r in self.results if r.error)

    @property
    def avg_latency_ms(self) -> float:
        vals = [r.latency_ms for r in self.results if r.error is None]
        return sum(vals) / len(vals) if vals else 0.0


class ProviderFactory(Protocol):
    def __call__(self) -> LLMProvider: ...


def _load_benchmark_cases() -> list[dict]:
    if not BENCHMARK_PATH.exists():
        raise FileNotFoundError(f"Benchmark nao encontrado em {BENCHMARK_PATH}")
    return json.loads(BENCHMARK_PATH.read_text(encoding="utf-8"))


def _build_request(case: dict) -> AnalyzeRequest:
    return AnalyzeRequest(
        text=case["input"],
        url=case.get("url"),
        situation=case.get("situation"),
        state=UserState(case["state"]),
    )


def _is_critical_failure(case: dict, result) -> bool:
    """Verifica se o resultado do provider viola a condicao critical_failure
    do caso: recomendar pagamento ou classificar como baixo risco quando o
    objetivo do caso exige o contrario.
    """
    critical_desc = (case.get("critical_failure") or "").lower()
    low_risk = result.risk_level in SAFE_LOW_RISK_LEVELS
    text_blob = " ".join(
        [result.summary, *result.safe_actions, *result.avoid_actions]
    ).lower()
    recommended_payment = any(
        marker in text_blob for marker in ("pague", "efetue o pagamento", "realize o pix")
    )
    if "baixo risco" in critical_desc and low_risk:
        return True
    if "pagamento" in critical_desc and recommended_payment:
        return True
    return False


def _make_mock_provider() -> LLMProvider:
    return MockProvider()


def _make_openai_provider() -> LLMProvider:
    raise NotImplementedError(
        "Provider OpenAI ainda nao implementado neste sandbox. "
        "Implemente uma subclasse de LLMProvider em um modulo local "
        "(fora do repositorio ou em branch privada) que leia "
        "OPENAI_API_KEY de variavel de ambiente e a registre aqui."
    )


def _make_claude_provider() -> LLMProvider:
    raise NotImplementedError(
        "Provider Claude ainda nao implementado neste sandbox. "
        "Implemente uma subclasse de LLMProvider que leia "
        "ANTHROPIC_API_KEY de variavel de ambiente e a registre aqui."
    )


def _make_gemini_provider() -> LLMProvider:
    raise NotImplementedError(
        "Provider Gemini ainda nao implementado neste sandbox. "
        "Implemente uma subclasse de LLMProvider que leia "
        "GOOGLE_API_KEY de variavel de ambiente e a registre aqui."
    )


PROVIDER_FACTORIES: dict[str, ProviderFactory] = {
    "mock": _make_mock_provider,
    "openai": _make_openai_provider,
    "claude": _make_claude_provider,
    "gemini": _make_gemini_provider,
}


def run_gate(provider_name: str) -> ProviderReport:
    factory = PROVIDER_FACTORIES.get(provider_name)
    if factory is None:
        raise ValueError(f"Provider desconhecido: {provider_name}")

    provider = factory()
    cases = _load_benchmark_cases()
    report = ProviderReport(name=provider_name, external=provider.metadata().get("external", False))

    for case in cases:
        request = _build_request(case)
        start = time.perf_counter()
        try:
            result = provider.analyze(request, request.text, request.url)
            elapsed_ms = (time.perf_counter() - start) * 1000
            failure = _is_critical_failure(case, result)
            report.results.append(
                CaseResult(
                    case_id=case["id"],
                    risk_level=result.risk_level.value,
                    latency_ms=elapsed_ms,
                    critical_failure_triggered=failure,
                )
            )
        except Exception as exc:  # noqa: BLE001 - queremos registrar qualquer falha
            elapsed_ms = (time.perf_counter() - start) * 1000
            report.results.append(
                CaseResult(
                    case_id=case["id"],
                    risk_level="ERRO",
                    latency_ms=elapsed_ms,
                    critical_failure_triggered=False,
                    error=str(exc),
                )
            )
    return report


def print_report(report: ProviderReport) -> None:
    print(f"\n=== Provider Gate: {report.name} (external={report.external}) ===")
    print(f"Casos avaliados: {report.total}")
    print(f"Falhas criticas (critical_failure): {report.critical_failures}")
    print(f"Erros de execucao: {report.errors}")
    print(f"Latencia media: {report.avg_latency_ms:.2f} ms")
    if report.critical_failures:
        print("\nCasos com falha critica:")
        for r in report.results:
            if r.critical_failure_triggered:
                print(f"  - {r.case_id}: risk_level={r.risk_level}")
    if report.errors:
        print("\nCasos com erro:")
        for r in report.results:
            if r.error:
                print(f"  - {r.case_id}: {r.error}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sandbox do Provider Gate (Fase 4, experimental).")
    parser.add_argument(
        "--provider",
        choices=sorted(PROVIDER_FACTORIES.keys()),
        default="mock",
        help="Provider candidato a avaliar contra o benchmark de 30 casos.",
    )
    args = parser.parse_args()

    report = run_gate(args.provider)
    print_report(report)

    # Gate falha (exit code != 0) se qualquer falha critica for detectada,
    # para uso em avaliacao manual ou script de comparacao futuro.
    return 1 if report.critical_failures > 0 or report.errors > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
