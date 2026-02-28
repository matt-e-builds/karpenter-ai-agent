from __future__ import annotations

from typing import Any, List

from karpenter_ai_agent.rag.index import InMemoryVectorIndex, get_default_index
from karpenter_ai_agent.rag.models import RAGQuery, RAGResult


def retrieve_context(
    query: RAGQuery,
    *,
    index: InMemoryVectorIndex | None = None,
) -> RAGResult:
    search_index = index or get_default_index()
    contexts = search_index.search(query.query, top_k=query.top_k)
    return RAGResult(contexts=contexts)


def build_issue_query(issue: Any) -> str:
    parts: List[str] = []
    for attr in ("rule_id", "category", "message", "recommendation", "resource_kind", "resource_name"):
        value = getattr(issue, attr, None)
        if value:
            parts.append(str(value))
    metadata = getattr(issue, "metadata", None)
    if isinstance(metadata, dict):
        field = metadata.get("field")
        if field:
            parts.append(str(field))
    return " ".join(parts).strip()
