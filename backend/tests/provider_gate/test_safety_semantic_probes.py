from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.tests.provider_gate.adapters import ProviderResponse
from backend.tests.provider_gate.safety_authority import DeterministicSafetyAuthority


PROBES_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "safety_semantic_probes.json"


def _load_probes() -> list[dict]:
    return json.loads(PROBES_PATH.read_text(encoding="utf-8"))


def _response(text: str) -> ProviderResponse:
    return ProviderResponse(text=text, input_tokens=1, output_tokens=1, latency_ms=1.0)


def test_semantic_probe_fixture_is_separate_from_frozen_benchmark():
    probes = _load_probes()
    assert probes
    assert all(probe["id"].startswith("P-") for probe in probes)
    assert len({probe["id"] for probe in probes}) == len(probes)


def test_every_required_semantic_category_has_safe_and_dangerous_probe():
    probes = _load_probes()
    categories = {}
    for probe in probes:
        categories.setdefault(probe["category"], set()).add(bool(probe["expected"]))

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
    assert expected_categories <= categories.keys()

    # Categories with an explicit polarity boundary must contain both outcomes.
    for category in (
        "negacao_simples",
        "negacao_modal",
        "negacao_coordenada",
        "limite_sentenca",
        "afirmacao_absoluta",
        "recusa_vs_divulgacao",
        "negacao_de_contencao",
    ):
        assert categories[category] == {True, False}, category


@pytest.mark.parametrize("probe", _load_probes(), ids=lambda probe: probe["id"])
def test_semantic_probe(probe: dict):
    authority = DeterministicSafetyAuthority(probe["case"])
    actual = authority.evaluate(_response(probe["response"]))
    assert actual is probe["expected"], (
        f"probe={probe['id']} category={probe['category']} "
        f"expected={probe['expected']} actual={actual} response={probe['response']!r}"
    )
