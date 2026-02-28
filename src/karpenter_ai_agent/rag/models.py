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


class RAGQuery(BaseModel):
    query: str
    top_k: int = Field(default=3, ge=1, le=10)


class RetrievedContext(BaseModel):
    title: str
    source_url: str
    text: str
    score: float = Field(ge=0)


class RAGResult(BaseModel):
    contexts: List[RetrievedContext] = Field(default_factory=list)
