from abc import ABC, abstractmethod
from .schema import AnalysisResult, AnalyzeRequest, RiskLevel, UserState

class LLMProvider(ABC):
    @abstractmethod
    def analyze(self, request: AnalyzeRequest, sanitized_text: str, sanitized_url: str | None) -> AnalysisResult: ...
    @abstractmethod
    def health_check(self) -> bool: ...
    @abstractmethod
    def metadata(self) -> dict: ...

class MockProvider(LLMProvider):
    def health_check(self) -> bool: return True
    def metadata(self) -> dict: return {"name":"mock","external":False}
    def analyze(self, request: AnalyzeRequest, sanitized_text: str, sanitized_url: str | None) -> AnalysisResult:
        t=f"{sanitized_text} {request.situation or ''} {sanitized_url or ''}".lower()
        critical=any(k in t for k in ["código sms","senha","acesso remoto","instale este app","instale o app"])
        high=any(k in t for k in ["pix","pague","pagamento","taxa","clique","retorno garantido","novo número","urgente","telegram"])
        if request.state==UserState.ESTOU_EM_DUVIDA and not critical and not high: level=RiskLevel.NAO_DETERMINADO
        elif critical: level=RiskLevel.RISCO_CRITICO
        elif high: level=RiskLevel.ALTO_RISCO
        else: level=RiskLevel.ATENCAO
        signals=[]
        for marker,label in [("urgente","pressão de urgência"),("pague","pedido de pagamento"),("pix","referência a Pix"),("senha","solicitação de credencial"),("código","solicitação de código"),("novo número","mudança de identidade/canal"),("retorno garantido","promessa financeira extraordinária"),("acesso remoto","pedido de controle remoto"),("telegram","mudança para canal menos verificável")]:
            if marker in t: signals.append(label)
        if not signals: signals=["nenhum sinal forte foi identificado no conteúdo fornecido"]
        return AnalysisResult(risk_level=level,summary="A avaliação é conservadora e orienta a ação mais segura com os dados disponíveis.",signals=signals,evidence=["a análise usou somente o conteúdo fornecido; nenhuma URL foi acessada"],safe_actions=["não efetue pagamentos nem forneça credenciais antes de verificar independentemente"],avoid_actions=["não clique quando houver canal oficial alternativo","não compartilhe senha, CVV ou códigos"],independent_verification=["confirme diretamente no aplicativo, site oficial ou telefone publicado pela instituição"],uncertainties=["a análise não confirma autenticidade nem elimina risco"])
