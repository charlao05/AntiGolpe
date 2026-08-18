from .schema import AnalysisResult, RiskLevel
from .sanitizers import sanitize_text

FORBIDDEN = (
    "100% seguro",
    "pode confiar",
    "comprovadamente seguro",
    "você certamente recuperará",
    "vai recuperar o dinheiro",
    "não existe nenhum risco",
    "tenho certeza de que isso é legítimo",
)


def _sanitize_output(result: AnalysisResult) -> AnalysisResult:
    fields = {
        "summary": sanitize_text(result.summary),
        "signals": [sanitize_text(x) for x in result.signals],
        "evidence": [sanitize_text(x) for x in result.evidence],
        "safe_actions": [sanitize_text(x) for x in result.safe_actions],
        "avoid_actions": [sanitize_text(x) for x in result.avoid_actions],
        "independent_verification": [sanitize_text(x) for x in result.independent_verification],
        "uncertainties": [sanitize_text(x) for x in result.uncertainties],
        "incident_protocol": [sanitize_text(x) for x in (result.incident_protocol or [])] if result.incident_protocol else None,
    }
    return result.model_copy(update=fields)


class SafetyEngine:
    def validate(self, result: AnalysisResult) -> AnalysisResult:
        result = _sanitize_output(result)
        text = " ".join(
            [
                result.summary,
                *result.signals,
                *result.evidence,
                *result.safe_actions,
                *result.avoid_actions,
                *result.independent_verification,
                *result.uncertainties,
                *(result.incident_protocol or []),
            ]
        ).lower()
        if any(term in text for term in FORBIDDEN):
            return AnalysisResult(
                risk_level=RiskLevel.NAO_DETERMINADO,
                summary="Não foi possível produzir uma resposta segura o suficiente com os dados disponíveis.",
                signals=[],
                evidence=[],
                safe_actions=["não realize pagamentos nem forneça credenciais", "confirme pelo canal oficial"],
                avoid_actions=["não clique nem compartilhe dados sensíveis antes da confirmação"],
                independent_verification=["use diretamente o aplicativo, site ou telefone oficial"],
                uncertainties=["resposta substituída por fallback determinístico"],
                incident_protocol=None,
            )
        return result
