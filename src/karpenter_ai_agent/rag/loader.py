from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from karpenter_ai_agent.rag.models import Chunk

DEFAULT_DOCS_PATH = Path(__file__).resolve().parents[3] / "docs" / "karpenter"


@dataclass(frozen=True)
class MarkdownDocument:
    doc_id: str
    title: str
    source_url: str
    content: str


def load_markdown_documents(path: Path = DEFAULT_DOCS_PATH) -> List[MarkdownDocument]:
    if not path.exists():
        return []

    documents: List[MarkdownDocument] = []
    for file_path in sorted(path.glob("**/*.md")):
        raw = file_path.read_text(encoding="utf-8")
        lines = raw.splitlines()
        title = "Karpenter docs"
        source_url = ""
        for line in lines:
            if line.startswith("# "):
                title = line[2:].strip()
                break
        for line in lines:
            if line.lower().startswith("source:"):
                source_url = line.split(":", 1)[1].strip()
                break
        content = _strip_metadata(lines).strip()
        if not content:
            continue
        doc_id = str(file_path.relative_to(path)).replace("/", "-").replace("\\", "-")
        documents.append(
            MarkdownDocument(
                doc_id=doc_id,
                title=title,
                source_url=source_url,
                content=content,
            )
        )
    return documents


def chunk_documents(documents: Iterable[MarkdownDocument], max_chars: int = 700) -> List[Chunk]:
    chunks: List[Chunk] = []
    for document in documents:
        index = 0
        for block in _split_blocks(document.content):
            for piece in _split_long_block(block, max_chars=max_chars):
                chunks.append(
                    Chunk(
                        chunk_id=f"{document.doc_id}-{index}",
                        doc_id=document.doc_id,
                        title=document.title,
                        source_url=document.source_url,
                        text=piece,
                    )
                )
                index += 1
    return chunks


def _strip_metadata(lines: List[str]) -> str:
    body: List[str] = []
    for line in lines:
        if line.startswith("# "):
            continue
        if line.lower().startswith("source:"):
            continue
        body.append(line)
    return "\n".join(body)


def _split_blocks(text: str) -> List[str]:
    blocks: List[str] = []
    current: List[str] = []
    for line in text.splitlines():
        if line.strip():
            current.append(line.strip())
            continue
        if current:
            blocks.append(" ".join(current).strip())
            current = []
    if current:
        blocks.append(" ".join(current).strip())
    return blocks


def _split_long_block(block: str, max_chars: int) -> List[str]:
    if len(block) <= max_chars:
        return [block]

    parts: List[str] = []
    remaining = block
    while len(remaining) > max_chars:
        cut = remaining.rfind(". ", 0, max_chars)
        if cut < 0:
            cut = max_chars
        else:
            cut += 1
        part = remaining[:cut].strip()
        if part:
            parts.append(part)
        remaining = remaining[cut:].strip()
    if remaining:
        parts.append(remaining)
    return parts
