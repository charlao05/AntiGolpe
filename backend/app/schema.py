from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class UserState(str, Enum):
    AINDA_NAO_AGI = "AINDA_NAO_AGI"
    ESTOU_EM_DUVIDA = "ESTOU_EM_DUVIDA"
    JA_AGI = "JA_AGI"
    JA_FUI_VITIMA = "JA_FUI_VITIMA"

class RiskLevel(str, Enum):
    BAIXA_ATENCAO = "BAIXA_ATENCAO"
    ATENCAO = "ATENCAO"
    ALTO_RISCO = "ALTO_RISCO"
    RISCO_CRITICO = "RISCO_CRITICO"
    NAO_DETERMINADO = "NAO_DETERMINADO"

class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(default="", max_length=12000)
    url: Optional[str] = Field(default=None, max_length=4096)
    situation: Optional[str] = Field(default=None, max_length=4000)
    state: UserState

class AnalysisResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    risk_level: RiskLevel
    summary: str
    signals: List[str]
    evidence: List[str]
    safe_actions: List[str]
    avoid_actions: List[str]
    independent_verification: List[str]
    uncertainties: List[str]
    incident_protocol: Optional[List[str]] = None
