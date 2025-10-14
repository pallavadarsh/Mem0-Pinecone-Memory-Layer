from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class ChatRequest(BaseModel):
    user_id: str
    message: str
    run_id: Optional[str] = None
    type: Optional[str] = "auto"
    tags: Optional[List[str]] = None

class PolicyTrace(BaseModel):
    classified_type: str
    rationale: str
    specificity: float
    longevity: float
    score: float
    decision: str                 # "store" | "skip_duplicate" | "skip_low_score"
    dedup_top_scores: List[float] = []


class ChatResponse(BaseModel):
    reply: str
    retrieved: List[Dict[str, Any]]
    stored: Dict[str, Any] | None = None
    summary: str | None = None
    policy: PolicyTrace | None = None      

class RetrieveResponse(BaseModel):
    results: List[Dict[str, Any]]