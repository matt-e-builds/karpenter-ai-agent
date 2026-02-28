from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from karpenter_ai_agent.rag.embedder import TfidfEmbedder
from karpenter_ai_agent.rag.loader import DEFAULT_DOCS_PATH, chunk_documents, load_markdown_documents
from karpenter_ai_agent.rag.models import Chunk, RetrievedContext


@dataclass
class InMemoryVectorIndex:
    chunks: List[Chunk]
    vectors: List[Dict[str, float]]
    norms: List[float]
    embedder: TfidfEmbedder

    @classmethod
    def build(cls, docs_path: Path = DEFAULT_DOCS_PATH) -> "InMemoryVectorIndex":
        documents = load_markdown_documents(docs_path)
        chunks = chunk_documents(documents)
        embedder = TfidfEmbedder()
        corpus = [f"{chunk.title} {chunk.text}" for chunk in chunks]
        embedder.fit(corpus)
        vectors: List[Dict[str, float]] = [embedder.transform(text) for text in corpus]
        norms = [math.sqrt(sum(value * value for value in vector.values())) for vector in vectors]
        return cls(chunks=chunks, vectors=vectors, norms=norms, embedder=embedder)

    def search(self, query: str, top_k: int = 3) -> List[RetrievedContext]:
        cleaned = query.strip()
        if not cleaned:
            return []

        query_vec = self.embedder.transform(cleaned)
        if not query_vec:
            return []
        query_norm = math.sqrt(sum(value * value for value in query_vec.values()))
        if query_norm == 0:
            return []

        scored: List[Tuple[Chunk, float]] = []
        for chunk, vector, norm in zip(self.chunks, self.vectors, self.norms):
            if norm == 0:
                continue
            dot = 0.0
            for token, weight in query_vec.items():
                dot += weight * vector.get(token, 0.0)
            score = dot / (query_norm * norm)
            if score > 0:
                scored.append((chunk, score))
        scored.sort(key=lambda item: item[1], reverse=True)
        return [
            RetrievedContext(
                title=chunk.title,
                source_url=chunk.source_url,
                text=chunk.text,
                score=score,
            )
            for chunk, score in scored[: max(top_k, 0)]
        ]


_DEFAULT_INDEX: InMemoryVectorIndex | None = None


def get_default_index() -> InMemoryVectorIndex:
    global _DEFAULT_INDEX
    if _DEFAULT_INDEX is None:
        _DEFAULT_INDEX = InMemoryVectorIndex.build(DEFAULT_DOCS_PATH)
    return _DEFAULT_INDEX
