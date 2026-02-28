from __future__ import annotations

from typing import List, Optional

from karpenter_ai_agent.rag.models import RAGQuery, RetrievedChunk
from karpenter_ai_agent.rag.render import render_citations
from karpenter_ai_agent.rag.tool import build_issue_query, retrieve_context
from karpenter_ai_agent.models import Issue as ContractIssue, ExplanationDoc, IssueExplanation as ContractExplanation
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
        query = RAGQuery(query=build_issue_query(issue), top_k=top_k)
        retrieval = retrieve_context(query)
        chunks = [
            RetrievedChunk(
                chunk_id=f"ctx-{index}",
                doc_id="karpenter-docs",
                title=context.title,
                source_url=context.source_url,
                text=context.text,
                score=context.score,
            )
            for index, context in enumerate(retrieval.contexts)
        ]
        citations = render_citations(chunks)
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
            explanation = generate_issue_explanation(issue, chunks)
            if explanation is None:
                explanation = IssueExplanation(why_matters=DEFAULT_NO_LLM_NOTE)
        else:
            explanation = IssueExplanation(why_matters=DEFAULT_NO_LLM_NOTE)

        explanation.docs = docs
        issue.explanation = explanation


def attach_contract_explanations(
    issues: List[ContractIssue],
    *,
    top_k: int = 3,
    llm_available: Optional[bool] = None,
) -> None:
    if llm_available is None:
        llm_available = is_llm_enabled()

    for issue in issues:
        query = RAGQuery(query=build_issue_query(issue), top_k=top_k)
        retrieval = retrieve_context(query)
        chunks = [
            RetrievedChunk(
                chunk_id=f"ctx-{index}",
                doc_id="karpenter-docs",
                title=context.title,
                source_url=context.source_url,
                text=context.text,
                score=context.score,
            )
            for index, context in enumerate(retrieval.contexts)
        ]
        citations = render_citations(chunks)
        if not citations:
            continue
        docs = [
            ExplanationDoc(
                title=citation["title"],
                source_url=citation["source_url"],
                score=citation.get("score"),
            )
            for citation in citations
        ]

        if llm_available:
            legacy_issue = Issue(
                severity=issue.severity,
                category=issue.category,
                message=issue.message,
                recommendation=issue.recommendation,
                provisioner_name=issue.resource_name,
                resource_kind=issue.resource_kind,
                resource_name=issue.resource_name,
                patch_snippet=issue.patch_snippet,
            )
            legacy_explanation = generate_issue_explanation(legacy_issue, chunks)
            if legacy_explanation is None:
                explanation = ContractExplanation(why_matters=DEFAULT_NO_LLM_NOTE)
            else:
                explanation = ContractExplanation(
                    why_matters=legacy_explanation.why_matters,
                    what_to_change=list(legacy_explanation.what_to_change),
                )
        else:
            explanation = ContractExplanation(why_matters=DEFAULT_NO_LLM_NOTE)

        explanation.docs = docs
        issue.explanation = explanation
