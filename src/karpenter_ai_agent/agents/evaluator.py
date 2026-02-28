from __future__ import annotations

import re
import time
from typing import Dict, Iterable, List, Set
from urllib.parse import urlparse

from karpenter_ai_agent.models import AnalysisReport
from karpenter_ai_agent.models.evaluation import EvaluationReason, EvaluationResult
from karpenter_ai_agent.rag.models import RetrievedContext

RULE_ID_PATTERN = re.compile(r"\b[a-z]+:[a-z0-9-]+\b")


def _extract_rule_ids(text: str) -> Set[str]:
    return set(RULE_ID_PATTERN.findall(text.lower()))


def _is_valid_url(url: str) -> bool:
    parsed = urlparse((url or "").strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


class EvaluatorAgent:
    name = "evaluator"

    def run(
        self,
        report: AnalysisReport,
        *,
        rag_context: Dict[str, List[RetrievedContext]] | None = None,
        generated_explanation: str | None = None,
    ) -> EvaluationResult:
        started = time.perf_counter()
        reasons: List[EvaluationReason] = []

        findings_by_rule = {issue.rule_id for issue in report.issues}

        if generated_explanation:
            unknown = _extract_rule_ids(generated_explanation) - findings_by_rule
            for rule_id in sorted(unknown):
                reasons.append(
                    EvaluationReason(
                        code="unknown_finding_reference",
                        message="Explanation referenced a finding not in deterministic results.",
                        rule_id=rule_id,
                    )
                )

        for issue in report.issues:
            if issue.explanation is None:
                continue

            why_matters = (issue.explanation.why_matters or "").strip()
            if not why_matters:
                reasons.append(
                    EvaluationReason(
                        code="missing_required_why_matters",
                        message="Explanation is missing required why_matters content.",
                        rule_id=issue.rule_id,
                    )
                )

            if not issue.explanation.docs:
                reasons.append(
                    EvaluationReason(
                        code="missing_required_docs",
                        message="Explanation is missing required citations.",
                        rule_id=issue.rule_id,
                    )
                )
                continue

            unknown_ids = _extract_rule_ids(
                " ".join([why_matters, *issue.explanation.what_to_change])
            ) - findings_by_rule
            for unknown_rule in sorted(unknown_ids):
                reasons.append(
                    EvaluationReason(
                        code="hallucinated_finding_reference",
                        message="Explanation referenced findings that were not detected.",
                        rule_id=unknown_rule,
                    )
                )

            allowed_sources = _allowed_sources_for_issue(issue.rule_id, rag_context)
            for doc in issue.explanation.docs:
                if not _is_valid_url(doc.source_url):
                    reasons.append(
                        EvaluationReason(
                            code="invalid_doc_source_url",
                            message="Citation source_url must be an absolute http(s) URL.",
                            rule_id=issue.rule_id,
                        )
                    )
                    continue

                if allowed_sources and doc.source_url not in allowed_sources:
                    reasons.append(
                        EvaluationReason(
                            code="hallucinated_citation",
                            message="Citation was not present in retrieved RAG context.",
                            rule_id=issue.rule_id,
                        )
                    )

        duration_ms = (time.perf_counter() - started) * 1000.0
        notes = [f"{reason.code}: {reason.message}" for reason in reasons]
        return EvaluationResult(
            passed=not reasons,
            reasons=reasons,
            notes=notes,
            latency_ms=duration_ms,
        )


def _allowed_sources_for_issue(
    rule_id: str,
    rag_context: Dict[str, List[RetrievedContext]] | None,
) -> Set[str]:
    if rag_context is None:
        return set()
    contexts = rag_context.get(rule_id, [])
    return {context.source_url for context in contexts if context.source_url}
