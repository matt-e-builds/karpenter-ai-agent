from __future__ import annotations

import json
from typing import Iterable

from karpenter_ai_agent.rag.models import RetrievedChunk

EXPLANATION_SYSTEM_PROMPT = """You are an expert Karpenter reviewer.

You will be given one detected issue and a small set of Karpenter docs excerpts.
Your job is to explain ONLY the given issue. Do not invent new issues, do not
change severity, and do not add resources not mentioned in the issue.

Output format (strict):
WHY: <2-4 sentences>
CHANGE:
- <1-3 bullets>
DOCS:
- <use only provided source URLs>
"""


def build_issue_prompt(issue_payload: dict, chunks: Iterable[RetrievedChunk]) -> str:
    context = [
        {
            "title": chunk.title,
            "source_url": chunk.source_url,
            "text": chunk.text,
        }
        for chunk in chunks
    ]
    return json.dumps(
        {
            "issue": issue_payload,
            "retrieved_docs": context,
        },
        indent=2,
    )
