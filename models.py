from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ProvisionerConfig:
    """
    Represents a Karpenter Provisioner or NodePool.
    """
    name: str
    kind: str  # "Provisioner" or "NodePool"
    nodeclass_name: Optional[str]
    consolidation_enabled: Optional[bool]
    spot_allowed: bool
    instance_families: List[str]
    graviton_used: bool
    ttl_seconds_after_empty: Optional[int]
    raw_yaml: Dict[str, Any]


@dataclass
class EC2NodeClassConfig:
    """
    Represents an EC2NodeClass (Karpenter v1beta1).
    """
    name: str
    instance_types: List[str]
    ami_selector_present: bool
    security_groups_present: bool
    subnets_present: bool
    instance_profile: Optional[str]
    role: Optional[str]
    raw_yaml: Dict[str, Any]


@dataclass
class Issue:
    """
    A single finding from the rules engine.
    """
    severity: str  # "high", "medium", "low"
    category: str  # e.g. "Spot", "Consolidation", "Graviton", "TTL", "EC2NodeClass"
    message: str
    recommendation: str

    # For UI / LLM aggregation
    provisioner_name: Optional[str] = None
    resource_kind: Optional[str] = None  # "Provisioner", "NodePool", "EC2NodeClass"
    resource_name: Optional[str] = None  # canonical name of the resource
    field: Optional[str] = None          # e.g. "spec.ttlSecondsAfterEmpty"

    # Optional YAML patch snippet (not populated in this rules version)
    patch_snippet: Optional[str] = None


@dataclass
class AnalysisResult:
    """
    Full analysis payload (useful if you later expose a JSON API).
    """
    region: str
    monthly_spend: Optional[float]
    provisioners: List[ProvisionerConfig] = field(default_factory=list)
    ec2_nodeclasses: List[EC2NodeClassConfig] = field(default_factory=list)
    issues: List[Issue] = field(default_factory=list)
