from __future__ import annotations

from typing import Iterable, List
from urllib.parse import urlparse

from karpenter_ai_agent.rag.models import RetrievedChunk


def render_citations(chunks: Iterable[RetrievedChunk]) -> List[dict]:
    citations: List[dict] = []
    seen = set()
    for chunk in chunks:
        url = (chunk.source_url or "").strip()
        if not url or url in seen:
            continue
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            continue
        citations.append(
            {
                "title": chunk.title.strip() or "Karpenter docs",
                "source_url": url,
                "score": chunk.score,
            }
        )
        seen.add(url)
    return citations
