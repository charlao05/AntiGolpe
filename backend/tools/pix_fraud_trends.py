"""Coletor de tendencias publicas de fraude no Pix (BCB).

Este modulo e uma ferramenta MANUAL de inteligencia, nao faz parte do
fluxo de producao (main.py) e nao e chamado automaticamente pela API.
Ele consome o dataset publico e gratuito do Banco Central do Brasil
(Estatisticas de Fraude no Pix via MED) para gerar um resumo de
tendencia mensal, servindo como insumo para revisao humana e eventual
atualizacao manual do benchmark de casos (tests/fixtures/benchmark_cases.json).

Fonte de dados (publica, sem autenticacao, sem custo):
    https://olinda.bcb.gov.br/olinda/servico/Pix_DadosAbertos/versao/v1/odata/EstatisticasFraudesPix

Como usar (local ou em job agendado manual, nunca em runtime da API):
    python backend/tools/pix_fraud_trends.py
    python backend/tools/pix_fraud_trends.py --months 6

Regras de seguranca (Master Brief v2.0):
    - Nao grava nenhum dado sensivel de usuario; consome apenas
      estatisticas agregadas e publicas do Banco Central.
    - Nao e importado por main.py nem pelo pipeline de CI.
    - Nao decide nem altera comportamento do MockProvider automaticamente;
      apenas imprime/objetiva um relatorio para revisao humana.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass

BCB_ENDPOINT = (
    "https://olinda.bcb.gov.br/olinda/servico/Pix_DadosAbertos/versao/v1/odata/"
    "EstatisticasFraudesPix?$format=json&$orderby=AnoMes desc"
)

REQUEST_TIMEOUT_SECONDS = 20


@dataclass
class MonthlyFraudStat:
    ano_mes: str
    quantidade_fraudes: float | None
    valor_fraudes: float | None


def fetch_raw_data(timeout: int = REQUEST_TIMEOUT_SECONDS) -> dict:
    """Busca o payload bruto do dataset publico do Banco Central.

    Nao usa nenhuma chave de API: o endpoint OData do BCB e publico.
    """
    request = urllib.request.Request(
        BCB_ENDPOINT,
        headers={"Accept": "application/json", "User-Agent": "AntiGolpe-TrendWatch/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Falha ao consultar dataset publico do BCB: {exc}") from exc
    return json.loads(payload)


def parse_monthly_stats(raw: dict, months: int) -> list[MonthlyFraudStat]:
    values = raw.get("value", [])
    stats: list[MonthlyFraudStat] = []
    for item in values[:months]:
        stats.append(
            MonthlyFraudStat(
                ano_mes=str(item.get("AnoMes", "desconhecido")),
                quantidade_fraudes=item.get("QuantidadeFraude") or item.get("Quantidade"),
                valor_fraudes=item.get("ValorFraude") or item.get("Valor"),
            )
        )
    return stats


def print_report(stats: list[MonthlyFraudStat]) -> None:
    if not stats:
        print("Nenhum dado retornado pelo dataset publico do BCB.")
        return

    print("\n=== Tendencia de Fraude no Pix (MED) - Banco Central do Brasil ===")
    print("Fonte: dados publicos, agregados, sem informacao pessoal.\n")
    for stat in stats:
        qtd = stat.quantidade_fraudes if stat.quantidade_fraudes is not None else "N/D"
        valor = stat.valor_fraudes if stat.valor_fraudes is not None else "N/D"
        print(f"  {stat.ano_mes}: casos={qtd}  valor_estimado={valor}")

    print(
        "\nUso recomendado: revisar manualmente se houve alta relevante de"
        " modalidade de fraude no periodo e, se aplicavel, propor novos"
        " casos de teste em tests/fixtures/benchmark_cases.json via PR"
        " revisado por humano. Este script NAO altera nenhum arquivo"
        " automaticamente."
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Relatorio de tendencia de fraude no Pix (dados publicos do BCB)."
    )
    parser.add_argument(
        "--months",
        type=int,
        default=6,
        help="Quantidade de meses mais recentes a exibir (padrao: 6).",
    )
    args = parser.parse_args()

    try:
        raw = fetch_raw_data()
    except RuntimeError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    stats = parse_monthly_stats(raw, args.months)
    print_report(stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
