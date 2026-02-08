from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Tuple
from pydantic import BaseModel, Field

PatchCategory = Literal["spot", "consolidation", "ttl", "graviton", "nodeclass"]
Severity = Literal["high", "medium", "low"]

_SEVERITY_RANK: Dict[str, int] = {"high": 0, "medium": 1, "low": 2}


class PatchSuggestion(BaseModel):
    resource_kind: str
    resource_name: str
    category: PatchCategory
    patch_yaml: str
    rule_id: str
    severity: Severity
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def sort_key(self) -> Tuple[str, str, str, int, str]:
        severity_rank = _SEVERITY_RANK.get(self.severity, 9)
        return (
            self.resource_kind or "",
            self.resource_name or "",
            self.category,
            severity_rank,
            self.rule_id,
        )


def _infer_category(issue: Any) -> Optional[PatchCategory]:
    rule_id = str(getattr(issue, "rule_id", "") or "")
    message = str(getattr(issue, "message", "") or "").lower()
    resource_kind = str(getattr(issue, "resource_kind", "") or "")
    category_text = str(getattr(issue, "category", "") or "").lower()

    if rule_id.startswith("security:") or resource_kind == "EC2NodeClass":
        return "nodeclass"
    if "nodeclass" in category_text:
        return "nodeclass"
    if "spot" in message:
        return "spot"
    if "graviton" in message:
        return "graviton"
    if "ttlsecondsafterempty" in message or "ttl" in message:
        return "ttl"
    if "consolidation" in message:
        return "consolidation"
    return None


def issue_to_patch_suggestion(issue: Any) -> Optional[PatchSuggestion]:
    patch_yaml = getattr(issue, "patch_snippet", None)
    if not patch_yaml:
        return None
    category = _infer_category(issue)
    if category is None:
        return None
    resource_kind = getattr(issue, "resource_kind", None) or ""
    resource_name = getattr(issue, "resource_name", None) or ""

    return PatchSuggestion(
        resource_kind=resource_kind,
        resource_name=resource_name,
        category=category,
        patch_yaml=patch_yaml,
        rule_id=getattr(issue, "rule_id", "unknown"),
        severity=getattr(issue, "severity", "low"),
    )


def build_patch_suggestions(issues: List[Any]) -> List[PatchSuggestion]:
    suggestions = []
    for issue in issues:
        suggestion = issue_to_patch_suggestion(issue)
        if suggestion:
            suggestions.append(suggestion)
    return suggestions
