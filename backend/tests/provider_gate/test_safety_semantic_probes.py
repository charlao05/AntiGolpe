from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.tests.provider_gate.adapters import ProviderResponse
from backend.tests.provider_gate.safety_authority import DeterministicSafetyAuthority


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"
PROBES_PATH = FIXTURES_DIR / "safety_semantic_probes.json"
MATRIX_PATH = FIXTURES_DIR / "safety_semantic_matrix.json"


def _load_probes() -> list[dict]:
    return json.loads(PROBES_PATH.read_text(encoding="utf-8"))


def _load_matrix() -> list[dict]:
    return json.loads(MATRIX_PATH.read_text(encoding="utf-8"))


def _response(text: str) -> ProviderResponse:
    return ProviderResponse(text=text, input_tokens=1, output_tokens=1, latency_ms=1.0)


def _observed(probe: dict) -> bool:
    authority = DeterministicSafetyAuthority(probe["case"])
    return authority.evaluate(_response(probe["response"]))


def test_semantic_probe_fixture_is_separate_from_frozen_benchmark():
    probes = _load_probes()
    assert probes
    assert all(probe["id"].startswith("P-") for probe in probes)
    assert len({probe["id"] for probe in probes}) == len(probes)


def test_required_semantic_categories_are_present():
    probes = _load_probes()
    categories = {probe["category"] for probe in probes}
    expected_categories = {
        "negacao_simples",
        "negacao_modal",
        "negacao_coordenada",
        "recomendacao_negativa_idiomatica",
        "limite_sentenca",
        "contexto_nao_afirmativo",
        "genero_gramatical",
        "forma_verbal",
        "afirmacao_absoluta",
        "rotulacao_credencial",
        "negacao_de_contencao",
        "protocolo_por_instrumento",
        "recusa_vs_divulgacao",
        "divulgacao_interna",
        "qr_whatsapp",
    }
    assert expected_categories <= categories


def test_18_class_matrix_is_complete_and_uses_distinct_safe_dangerous_probes():
    matrix = _load_matrix()
    probes = {probe["id"]: probe for probe in _load_probes()}
    assert len(matrix) == 18
    assert {row["class"] for row in matrix} == {f"SEM-{index:02d}" for index in range(1, 19)}
    for row in matrix:
        assert row["safe_probe"] in probes, row
        assert row["dangerous_probe"] in probes, row
        assert row["safe_probe"] != row["dangerous_probe"], row
        safe = probes[row["safe_probe"]]
        dangerous = probes[row["dangerous_probe"]]
        assert safe["expected"] is True, row
        assert dangerous["expected"] is False, row


@pytest.mark.parametrize("probe", _load_probes(), ids=lambda probe: probe["id"])
def test_semantic_probe(probe: dict):
    actual = _observed(probe)
    assert actual is probe["expected"], (
        f"probe={probe['id']} category={probe['category']} "
        f"expected={probe['expected']} actual={actual} response={probe['response']!r}"
    )


@pytest.mark.parametrize("row", _load_matrix(), ids=lambda row: row["class"])
def test_18_class_matrix_executes_both_directions(row: dict):
    probes = {probe["id"]: probe for probe in _load_probes()}
    safe = probes[row["safe_probe"]]
    dangerous = probes[row["dangerous_probe"]]
    observed_safe = _observed(safe)
    observed_dangerous = _observed(dangerous)
    assert observed_safe is True, (
        f"class={row['class']} name={row['name']} direction=safe "
        f"probe={safe['id']} expected=True observed={observed_safe}"
    )
    assert observed_dangerous is False, (
        f"class={row['class']} name={row['name']} direction=dangerous "
        f"probe={dangerous['id']} expected=False observed={observed_dangerous}"
    )
