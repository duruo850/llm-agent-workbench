"""GET /intent/classify 响应。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class IntentCandidateResponse(BaseModel):
    scene: str
    confidence: float


class IntentClassifyResponse(BaseModel):
    query: str
    scene: str
    confidence: float
    method: str
    candidates: list[IntentCandidateResponse] = Field(default_factory=list)
