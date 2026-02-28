from __future__ import annotations

import math
import re
from typing import Dict, Iterable, List

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "this",
    "that",
    "from",
    "into",
    "when",
    "only",
    "must",
    "should",
    "not",
    "are",
    "you",
    "your",
}


def tokenize(text: str) -> List[str]:
    return [t for t in _TOKEN_RE.findall(text.lower()) if len(t) > 1 and t not in _STOPWORDS]


class TfidfEmbedder:
    def __init__(self) -> None:
        self._idf: Dict[str, float] = {}

    def fit(self, texts: Iterable[str]) -> None:
        docs = list(texts)
        if not docs:
            self._idf = {}
            return
        document_frequency: Dict[str, int] = {}
        for text in docs:
            for token in set(tokenize(text)):
                document_frequency[token] = document_frequency.get(token, 0) + 1
        total = len(docs)
        self._idf = {
            token: math.log((1 + total) / (1 + count)) + 1
            for token, count in document_frequency.items()
        }

    def transform(self, text: str) -> Dict[str, float]:
        tokens = tokenize(text)
        if not tokens:
            return {}
        counts: Dict[str, int] = {}
        for token in tokens:
            counts[token] = counts.get(token, 0) + 1
        total = len(tokens)
        vector: Dict[str, float] = {}
        for token, count in counts.items():
            weight = (count / total) * self._idf.get(token, 0.0)
            if weight:
                vector[token] = weight
        return vector

    @property
    def idf(self) -> Dict[str, float]:
        return dict(self._idf)
