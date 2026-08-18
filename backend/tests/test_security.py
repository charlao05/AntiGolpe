from backend.app.incidents import incident_protocol
from backend.app.rate_limit import RateLimiter
from backend.app.safety import SafetyEngine
from backend.app.schema import AnalysisResult, RiskLevel, UserState


def test_forbidden_language_falls_back():
    result = AnalysisResult(
        risk_level=RiskLevel.BAIXA_ATENCAO,
        summary="É 100% seguro.",
        signals=[],
        evidence=[],
        safe_actions=[],
        avoid_actions=[],
        independent_verification=[],
        uncertainties=[],
    )
    assert SafetyEngine().validate(result).risk_level == RiskLevel.NAO_DETERMINADO


def test_output_pii_is_redacted():
    result = AnalysisResult(
        risk_level=RiskLevel.ALTO_RISCO,
        summary="CPF 123.456.789-00 e pessoa@example.com devem ser ignorados.",
        signals=["Telefone 11999998888"],
        evidence=["Pix 123e4567-e89b-12d3-a456-426614174000"],
        safe_actions=[],
        avoid_actions=[],
        independent_verification=[],
        uncertainties=[],
    )
    output = SafetyEngine().validate(result)
    combined = " ".join(
        [output.summary, *output.signals, *output.evidence, *output.safe_actions]
    )
    assert "123.456.789-00" not in combined
    assert "pessoa@example.com" not in combined
    assert "11999998888" not in combined
    assert "123e4567-e89b-12d3-a456-426614174000" not in combined


def test_pix_incident_protocol():
    steps = incident_protocol(UserState.JA_FUI_VITIMA, "Acabei de fazer um Pix")
    assert any("MED" in step for step in steps)
    assert any("banco" in step for step in steps)


def test_card_incident_does_not_use_med():
    steps = incident_protocol(UserState.JA_FUI_VITIMA, "Meu cartão foi usado")
    assert any("bloqueie" in step.lower() for step in steps)
    assert not any("MED" in step for step in steps)


def test_rate_limiter_blocks_after_limit():
    limiter = RateLimiter(limit=1, window_seconds=60)
    assert limiter.allowed("203.0.113.10") is True
    assert limiter.allowed("203.0.113.10") is False
