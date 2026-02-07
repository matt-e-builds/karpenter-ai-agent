from __future__ import annotations

from typing import Any, List

from karpenter_ai_agent.rag.models import RetrievedChunk, RetrievalResult
from karpenter_ai_agent.rag.store import KnowledgeStore, get_default_store


def retrieve(query: str, top_k: int = 3, store: KnowledgeStore | None = None) -> RetrievalResult:
    if store is None:
        store = get_default_store()
    results = store.search(query, top_k=top_k)
    chunks = [
        RetrievedChunk(
            chunk_id=chunk.chunk_id,
            doc_id=chunk.doc_id,
            title=chunk.title,
            source_url=chunk.source_url,
            text=chunk.text,
            score=score,
        )
        for chunk, score in results
    ]
    return RetrievalResult(chunks=chunks)


def build_issue_query(issue: Any) -> str:
    parts: List[str] = []
    for attr in ("category", "message", "recommendation", "resource_kind", "resource_name", "rule_id"):
        value = getattr(issue, attr, None)
        if value:
            parts.append(str(value))
    metadata = getattr(issue, "metadata", None)
    if isinstance(metadata, dict):
        field = metadata.get("field")
        if field:
            parts.append(str(field))
    field_attr = getattr(issue, "field", None)
    if field_attr:
        parts.append(str(field_attr))
    return " ".join(parts).strip()


def retrieve_for_issue(
    issue: Any,
    top_k: int = 3,
    store: KnowledgeStore | None = None,
) -> RetrievalResult:
    query = build_issue_query(issue)
    return retrieve(query, top_k=top_k, store=store)
