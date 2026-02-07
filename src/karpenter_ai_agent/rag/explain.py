from __future__ import annotations

from typing import List, Optional

from karpenter_ai_agent.rag.retrieve import retrieve_for_issue
from karpenter_ai_agent.rag.render import render_citations
from models import Issue, IssueDoc, IssueExplanation
from llm_client import generate_issue_explanation, is_llm_enabled

DEFAULT_NO_LLM_NOTE = (
    "Relevant docs found; enable AI summary for narrative explanation."
)


def attach_issue_explanations(
    issues: List[Issue],
    *,
    top_k: int = 3,
    llm_available: Optional[bool] = None,
) -> None:
    if llm_available is None:
        llm_available = is_llm_enabled()

    for issue in issues:
        retrieval = retrieve_for_issue(issue, top_k=top_k)
        citations = render_citations(retrieval.chunks)
        if not citations:
            continue
        docs = [
            IssueDoc(
                title=citation["title"],
                source_url=citation["source_url"],
                score=citation.get("score"),
            )
            for citation in citations
        ]

        if llm_available:
            explanation = generate_issue_explanation(issue, retrieval.chunks)
            if explanation is None:
                explanation = IssueExplanation(why_matters=DEFAULT_NO_LLM_NOTE)
        else:
            explanation = IssueExplanation(why_matters=DEFAULT_NO_LLM_NOTE)

        explanation.docs = docs
        issue.explanation = explanation
