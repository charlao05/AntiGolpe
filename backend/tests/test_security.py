from backend.app.safety import SafetyEngine
from backend.app.schema import AnalysisResult,RiskLevel,UserState
from backend.app.incidents import incident_protocol
def test_forbidden_language_falls_back():
    r=AnalysisResult(risk_level=RiskLevel.BAIXA_ATENCAO,summary='É 100% seguro.',signals=[],evidence=[],safe_actions=[],avoid_actions=[],independent_verification=[],uncertainties=[])
    assert SafetyEngine().validate(r).risk_level==RiskLevel.NAO_DETERMINADO
def test_pix_incident_protocol():
    s=incident_protocol(UserState.JA_FUI_VITIMA,'Acabei de fazer um Pix'); assert any('MED' in x for x in s); assert any('banco' in x for x in s)
def test_card_incident_does_not_use_med():
    s=incident_protocol(UserState.JA_FUI_VITIMA,'Meu cartão foi usado'); assert any('bloqueie' in x.lower() for x in s); assert not any('MED' in x for x in s)
