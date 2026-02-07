from __future__ import annotations

from typing import List
from pydantic import BaseModel, Field


class Chunk(BaseModel):
    chunk_id: str
    doc_id: str
    title: str
    source_url: str
    text: str


class RetrievedChunk(Chunk):
    score: float = Field(ge=0)


class RetrievalResult(BaseModel):
    chunks: List[RetrievedChunk] = Field(default_factory=list)
