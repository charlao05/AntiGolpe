from pathlib import Path
from fastapi import FastAPI,HTTPException,Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .schema import AnalyzeRequest,AnalysisResult
from .sanitizers import sanitize_text,sanitize_url
from .providers import MockProvider
from .safety import SafetyEngine
from .rate_limit import RateLimiter
from .incidents import incident_protocol
ROOT=Path(__file__).resolve().parents[2]
app=FastAPI(title="AntiGolpe",version="0.1.0")
provider=MockProvider(); safety=SafetyEngine(); limiter=RateLimiter()
@app.get('/api/health')
def health(): return {'ok':True,'provider':provider.metadata()}
@app.post('/api/analyze',response_model=AnalysisResult)
def analyze(payload:AnalyzeRequest,request:Request):
    ip=request.client.host if request.client else 'unknown'
    if not limiter.allowed(ip): raise HTTPException(status_code=429,detail='Limite temporário atingido. Tente novamente mais tarde.')
    text=sanitize_text(payload.text); url=sanitize_url(payload.url); combined=' '.join(x for x in [text,payload.situation or '',url or ''] if x)
    result=provider.analyze(payload,text,url); protocol=incident_protocol(payload.state,combined)
    if protocol: result.incident_protocol=protocol; result.safe_actions=protocol[:]
    return safety.validate(result)
frontend=ROOT/'frontend'
if frontend.exists(): app.mount('/assets',StaticFiles(directory=frontend),name='assets')
@app.get('/')
def index(): return FileResponse(frontend/'index.html')
