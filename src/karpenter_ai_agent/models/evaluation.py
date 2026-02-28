from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class EvaluationReason(BaseModel):
    code: str
    message: str
    rule_id: Optional[str] = None


class EvaluationResult(BaseModel):
    passed: bool = True
    reasons: List[EvaluationReason] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
    retries: int = 0
    latency_ms: float = Field(default=0.0, ge=0.0)
