from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List
import math
import re

from karpenter_ai_agent.rag.models import Chunk

DEFAULT_KNOWLEDGE_PATH = (
    Path(__file__).resolve().parents[3] / "docs" / "knowledge" / "karpenter"
)

_STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "into",
    "only",
    "over",
    "when",
    "then",
    "than",
    "must",
    "should",
    "can",
    "may",
    "are",
    "your",
    "you",
    "use",
    "using",
    "uses",
    "set",
    "sets",
    "not",
    "none",
}

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> List[str]:
    tokens = _TOKEN_RE.findall(text.lower())
    return [t for t in tokens if len(t) > 1 and t not in _STOPWORDS]


def _split_blocks(text: str) -> List[str]:
    blocks: List[str] = []
    current: List[str] = []
    for line in text.splitlines():
        if not line.strip():
            if current:
                blocks.append(" ".join(current).strip())
                current = []
            continue
        current.append(line.strip())
    if current:
        blocks.append(" ".join(current).strip())
    return blocks


def _split_long_block(block: str, max_len: int) -> List[str]:
    if len(block) <= max_len:
        return [block]
    chunks: List[str] = []
    text = block
    while len(text) > max_len:
        cut = text.rfind(". ", 0, max_len)
        if cut == -1:
            cut = max_len
        else:
            cut += 1
        chunk = text[:cut].strip()
        if chunk:
            chunks.append(chunk)
        text = text[cut:].strip()
    if text:
        chunks.append(text)
    return chunks


def _extract_doc_metadata(lines: List[str]) -> tuple[str, str]:
    title = "Karpenter docs"
    source_url = ""
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
        if line.lower().startswith("source:"):
            source_url = line.split(":", 1)[1].strip()
    return title, source_url


def _content_without_metadata(lines: List[str]) -> str:
    filtered: List[str] = []
    for line in lines:
        if line.startswith("# "):
            continue
        if line.lower().startswith("source:"):
            continue
        filtered.append(line)
    return "\n".join(filtered).strip()


def _load_chunks(path: Path, max_len: int) -> List[Chunk]:
    chunks: List[Chunk] = []
    for file_path in sorted(path.glob("*.md")):
        lines = file_path.read_text(encoding="utf-8").splitlines()
        title, source_url = _extract_doc_metadata(lines)
        content = _content_without_metadata(lines)
        if not content:
            continue
        blocks = _split_blocks(content)
        doc_id = file_path.stem
        idx = 0
        for block in blocks:
            for part in _split_long_block(block, max_len):
                chunk_id = f"{doc_id}-{idx}"
                idx += 1
                chunks.append(
                    Chunk(
                        chunk_id=chunk_id,
                        doc_id=doc_id,
                        title=title,
                        source_url=source_url,
                        text=part,
                    )
                )
    return chunks


def _compute_idf(chunks: Iterable[Chunk]) -> Dict[str, float]:
    docs = list(chunks)
    if not docs:
        return {}
    df: Dict[str, int] = {}
    for chunk in docs:
        tokens = set(_tokenize(f"{chunk.title} {chunk.text}"))
        for token in tokens:
            df[token] = df.get(token, 0) + 1
    n_docs = len(docs)
    return {term: math.log((1 + n_docs) / (1 + count)) + 1 for term, count in df.items()}


def _tfidf_vector(text: str, idf: Dict[str, float]) -> Dict[str, float]:
    tokens = _tokenize(text)
    if not tokens:
        return {}
    counts: Dict[str, int] = {}
    for token in tokens:
        counts[token] = counts.get(token, 0) + 1
    total = len(tokens)
    vector: Dict[str, float] = {}
    for token, count in counts.items():
        weight = (count / total) * idf.get(token, 0.0)
        if weight:
            vector[token] = weight
    return vector


@dataclass
class KnowledgeStore:
    chunks: List[Chunk]
    idf: Dict[str, float]
    vectors: List[Dict[str, float]]
    norms: List[float]

    @classmethod
    def load(cls, path: Path, max_len: int = 800) -> "KnowledgeStore":
        if not path.exists():
            return cls([], {}, [], [])
        chunks = _load_chunks(path, max_len)
        idf = _compute_idf(chunks)
        vectors: List[Dict[str, float]] = []
        norms: List[float] = []
        for chunk in chunks:
            vec = _tfidf_vector(f"{chunk.title} {chunk.text}", idf)
            vectors.append(vec)
            norms.append(math.sqrt(sum(weight * weight for weight in vec.values())))
        return cls(chunks=chunks, idf=idf, vectors=vectors, norms=norms)

    def search(self, query: str, top_k: int = 3) -> List[tuple[Chunk, float]]:
        if not self.chunks:
            return []
        query = query.strip()
        if not query:
            return []
        q_vec = _tfidf_vector(query, self.idf)
        if not q_vec:
            return []
        q_norm = math.sqrt(sum(weight * weight for weight in q_vec.values()))
        if q_norm == 0:
            return []

        scored: List[tuple[Chunk, float]] = []
        for chunk, vec, norm in zip(self.chunks, self.vectors, self.norms):
            if norm == 0:
                continue
            dot = 0.0
            for token, weight in q_vec.items():
                dot += weight * vec.get(token, 0.0)
            score = dot / (q_norm * norm)
            if score > 0:
                scored.append((chunk, score))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[: max(top_k, 0)]


_DEFAULT_STORE: KnowledgeStore | None = None


def get_default_store() -> KnowledgeStore:
    global _DEFAULT_STORE
    if _DEFAULT_STORE is None:
        _DEFAULT_STORE = KnowledgeStore.load(DEFAULT_KNOWLEDGE_PATH)
    return _DEFAULT_STORE
