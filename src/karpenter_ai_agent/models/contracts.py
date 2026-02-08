from __future__ import annotations

from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field

Severity = Literal["high", "medium", "low"]
IssueCategory = str


class Issue(BaseModel):
    rule_id: str
    severity: Severity
    category: IssueCategory
    message: str
    recommendation: str
    resource_name: Optional[str] = None
    resource_kind: Optional[str] = None
    patch_snippet: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    explanation: Optional["IssueExplanation"] = None


class ExplanationDoc(BaseModel):
    title: str
    source_url: str
    score: Optional[float] = None


class IssueExplanation(BaseModel):
    why_matters: Optional[str] = None
    what_to_change: List[str] = Field(default_factory=list)
    docs: List[ExplanationDoc] = Field(default_factory=list)


class ParseError(BaseModel):
    message: str
    path: Optional[str] = None
    line: Optional[int] = None


class CanonicalProvisioner(BaseModel):
    name: str
    kind: str
    nodeclass_name: Optional[str] = None
    consolidation_enabled: Optional[bool] = None
    spot_allowed: bool
    instance_families: List[str] = Field(default_factory=list)
    graviton_used: bool
    ttl_seconds_after_empty: Optional[int] = None
    raw_yaml: Dict[str, Any]


class CanonicalEC2NodeClass(BaseModel):
    name: str
    instance_types: List[str] = Field(default_factory=list)
    ami_selector_present: bool
    security_groups_present: bool
    subnets_present: bool
    instance_profile: Optional[str] = None
    role: Optional[str] = None
    raw_yaml: Dict[str, Any]


class CanonicalConfig(BaseModel):
    provisioners: List[CanonicalProvisioner] = Field(default_factory=list)
    ec2_nodeclasses: List[CanonicalEC2NodeClass] = Field(default_factory=list)


class AnalysisInput(BaseModel):
    yaml_text: str
    region: Optional[str] = None
    monthly_spend: Optional[float] = None
    options: Dict[str, Any] = Field(default_factory=dict)


class AgentResult(BaseModel):
    issues: List[Issue] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
    signals: Dict[str, Any] = Field(default_factory=dict)


class EvaluationResult(BaseModel):
    notes: List[str] = Field(default_factory=list)
    retries: int = 0


class AnalysisReport(BaseModel):
    region: Optional[str] = None
    health_score: int
    issues: List[Issue]
    issues_by_severity: Dict[str, int]
    optimizer_flags: Dict[str, Any]
    parse_errors: List[ParseError] = Field(default_factory=list)
    ai_summary: Optional[str] = None
    evaluation_notes: List[str] = Field(default_factory=list)
    raw: Dict[str, Any] = Field(default_factory=dict)


class ParserOutput(BaseModel):
    config: Optional[CanonicalConfig] = None
    parse_errors: List[ParseError] = Field(default_factory=list)
    normalized_metadata: Dict[str, Any] = Field(default_factory=dict)
