from __future__ import annotations

from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field

from karpenter_ai_agent.models import CanonicalConfig, ParseError


class ValidateYamlSchemaInput(BaseModel):
    yaml_text: str


class ValidateYamlSchemaOutput(BaseModel):
    valid: bool
    errors: list[ParseError] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class EstimateCostSignalsInput(BaseModel):
    config: CanonicalConfig
    region: Optional[str] = None
    monthly_spend: Optional[float] = None


class EstimateCostSignalsOutput(BaseModel):
    signals: Dict[str, Any] = Field(default_factory=dict)


class ExplainRecommendationInput(BaseModel):
    rule_id: str
    context: Dict[str, Any] = Field(default_factory=dict)


class ExplainRecommendationOutput(BaseModel):
    explanation: str


class RetrieveKarpenterDocsInput(BaseModel):
    query: str
    top_k: int = Field(default=3, ge=1, le=10)


class RetrievedDocChunk(BaseModel):
    title: str
    source_url: str
    text: str
    score: float


class RetrieveKarpenterDocsOutput(BaseModel):
    chunks: List[RetrievedDocChunk] = Field(default_factory=list)
