from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Sequence, Set
from pydantic import BaseModel, Field

from karpenter_ai_agent.models import AnalysisReport
from karpenter_ai_agent.models.patches import PatchCategory, PatchSuggestion

DEFAULT_CATEGORIES: Set[PatchCategory] = {"spot", "consolidation", "ttl", "graviton"}


class Bundle(BaseModel):
    nodepool_name: str
    selected_categories: Set[PatchCategory] = Field(default_factory=set)
    suggestions: List[PatchSuggestion] = Field(default_factory=list)
    yaml_documents: List[str] = Field(default_factory=list)
    bundle_yaml: str = ""


def _sort_suggestions(suggestions: Iterable[PatchSuggestion]) -> List[PatchSuggestion]:
    return sorted(suggestions, key=lambda s: s.sort_key())


def _format_patch_document(suggestion: PatchSuggestion) -> str:
    header = (
        f"# Fix: {suggestion.rule_id} for "
        f"{suggestion.resource_kind}/{suggestion.resource_name}"
    )
    patch = suggestion.patch_yaml.strip()
    return f"{header}\n{patch}\n"


def _bundle_yaml(docs: Sequence[str]) -> str:
    return "\n---\n".join(doc.strip() for doc in docs if doc.strip())


def _nodepool_refs(report: AnalysisReport) -> Dict[str, Optional[str]]:
    raw = report.raw or {}
    refs = raw.get("nodepool_refs")
    if isinstance(refs, dict):
        return {str(k): (v if isinstance(v, str) else None) for k, v in refs.items()}
    return {}


def _nodeclass_to_nodepools(nodepool_refs: Dict[str, Optional[str]]) -> Dict[str, List[str]]:
    mapping: Dict[str, List[str]] = {}
    for nodepool, nodeclass in nodepool_refs.items():
        if not nodeclass:
            continue
        mapping.setdefault(nodeclass, []).append(nodepool)
    return mapping


def _target_bundles(
    suggestion: PatchSuggestion,
    nodeclass_map: Dict[str, List[str]],
) -> List[str]:
    kind = suggestion.resource_kind
    name = suggestion.resource_name
    if kind == "EC2NodeClass":
        nodepools = nodeclass_map.get(name)
        return nodepools if nodepools else ["_unscoped"]
    if kind in {"NodePool", "Provisioner"}:
        return [name] if name else ["_unscoped"]
    return ["_unscoped"]


def build_bundles(
    report: AnalysisReport,
    include_categories: Optional[Set[PatchCategory]] = None,
) -> Dict[str, Bundle]:
    categories = include_categories or set(DEFAULT_CATEGORIES)
    nodepool_refs = _nodepool_refs(report)
    nodeclass_map = _nodeclass_to_nodepools(nodepool_refs)

    bundles: Dict[str, Bundle] = {}
    for suggestion in report.patch_suggestions:
        if suggestion.category not in categories:
            continue
        for bundle_name in _target_bundles(suggestion, nodeclass_map):
            bundle = bundles.setdefault(
                bundle_name,
                Bundle(nodepool_name=bundle_name, selected_categories=categories),
            )
            bundle.suggestions.append(suggestion)

    for bundle in bundles.values():
        ordered = _sort_suggestions(bundle.suggestions)
        bundle.yaml_documents = [_format_patch_document(s) for s in ordered]
        bundle.bundle_yaml = _bundle_yaml(bundle.yaml_documents)

    return dict(sorted(bundles.items(), key=lambda item: item[0]))


def build_bundle_yaml(
    report: AnalysisReport,
    include_categories: Optional[Set[PatchCategory]] = None,
) -> str:
    categories = include_categories or set(DEFAULT_CATEGORIES)
    suggestions = _sort_suggestions(
        [s for s in report.patch_suggestions if s.category in categories]
    )
    docs = [_format_patch_document(suggestion) for suggestion in suggestions]
    return _bundle_yaml(docs)


def build_bundle_yaml_for_nodepool(
    report: AnalysisReport,
    nodepool_name: str,
    include_categories: Optional[Set[PatchCategory]] = None,
) -> str:
    bundles = build_bundles(report, include_categories)
    bundle = bundles.get(nodepool_name)
    if not bundle:
        return ""
    return bundle.bundle_yaml
