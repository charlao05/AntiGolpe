from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .incidents import incident_protocol
from .providers import MockProvider
from .rate_limit import RateLimiter
from .sanitizers import sanitize_text, sanitize_url
from .safety import SafetyEngine
from .schema import AnalysisResult, AnalyzeRequest, RiskLevel

ROOT = Path(__file__).resolve().parents[2]
app = FastAPI(title="AntiGolpe", version="0.1.0")
provider = MockProvider()
safety = SafetyEngine()
limiter = RateLimiter()


def deterministic_incident_result(protocol: list[str]) -> AnalysisResult:
    return AnalysisResult(
        risk_level=RiskLevel.ALTO_RISCO,
        summary="A prioridade agora é conter o possível incidente e preservar evidências.",
        signals=["o usuário informou uma situação pós-incidente"],
        evidence=["o protocolo foi acionado sem depender de modelo externo"],
        safe_actions=protocol,
        avoid_actions=["não forneça novos códigos, senhas ou pagamentos ao possível fraudador"],
        independent_verification=["use exclusivamente canais oficiais e independentes da mensagem suspeita"],
        uncertainties=["a orientação não confirma recuperação de valores nem a autenticidade de todos os fatos"],
        incident_protocol=protocol,
    )


def client_ip(request: Request) -> str:
    """Resolve the client IP for the Render/Cloudflare deployment topology.

    Prefer Cloudflare's trusted visitor-IP header, then Render's documented
    first X-Forwarded-For value, and finally the direct socket address.
    """
    headers = request.headers
    cf_ip = headers.get("cf-connecting-ip")
    if cf_ip and cf_ip.strip():
        return cf_ip.strip()

    forwarded = headers.get("x-forwarded-for")
    if forwarded:
        first = forwarded.split(",", 1)[0].strip()
        if first:
            return first

    return request.client.host if request.client else "unknown"


@app.get("/api/health")
def health():
    return {"ok": True, "provider": provider.metadata()}


@app.post("/api/analyze", response_model=AnalysisResult)
def analyze(payload: AnalyzeRequest, request: Request):
    ip = client_ip(request)
    if not limiter.allowed(ip):
        raise HTTPException(status_code=429, detail="Limite temporário atingido. Tente novamente mais tarde.")

    text = sanitize_text(payload.text)
    url = sanitize_url(payload.url)
    combined = " ".join(x for x in [text, payload.situation or "", url or ""] if x)

    protocol = incident_protocol(payload.state, combined)
    if payload.state.value == "JA_FUI_VITIMA" and protocol:
        return safety.validate(deterministic_incident_result(protocol))

    result = provider.analyze(payload, text, url)
    if protocol:
        result.incident_protocol = protocol
        result.safe_actions = protocol[:]
    return safety.validate(result)


frontend = ROOT / "frontend"
if frontend.exists():
    app.mount("/assets", StaticFiles(directory=frontend), name="assets")


@app.get("/")
def index():
    return FileResponse(frontend / "index.html")
