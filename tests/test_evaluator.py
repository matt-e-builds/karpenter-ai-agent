from karpenter_ai_agent.agents.evaluator import EvaluatorAgent
from karpenter_ai_agent.models import AnalysisReport, ExplanationDoc, Issue, IssueExplanation
from karpenter_ai_agent.rag.models import RetrievedContext


def _base_report() -> AnalysisReport:
    return AnalysisReport(
        region="us-east-1",
        health_score=75,
        issues=[
            Issue(
                rule_id="security:missing-nodeclass",
                severity="high",
                category="security",
                message="NodePool is missing nodeClassRef",
                recommendation="Set nodeClassRef to an existing EC2NodeClass.",
                explanation=IssueExplanation(
                    why_matters="Without nodeClassRef, provisioning may fail.",
                    what_to_change=["Set spec.template.spec.nodeClassRef.name"],
                    docs=[
                        ExplanationDoc(
                            title="NodePool and EC2NodeClass Relationship",
                            source_url="https://karpenter.sh/docs/concepts/nodepools/",
                            score=0.9,
                        )
                    ],
                ),
            )
        ],
        issues_by_severity={"high": 1, "medium": 0, "low": 0},
        optimizer_flags={},
    )


def test_evaluator_passes_for_grounded_explanations():
    agent = EvaluatorAgent()
    report = _base_report()
    rag_context = {
        "security:missing-nodeclass": [
            RetrievedContext(
                title="NodePool and EC2NodeClass Relationship",
                source_url="https://karpenter.sh/docs/concepts/nodepools/",
                text="NodePool should reference a valid EC2NodeClass.",
                score=0.9,
            )
        ]
    }

    result = agent.run(report, rag_context=rag_context)

    assert result.passed is True
    assert result.reasons == []


def test_evaluator_fails_on_hallucinated_reference_and_citation():
    agent = EvaluatorAgent()
    report = _base_report()
    report.issues[0].explanation.docs[0].source_url = "notaurl"

    result = agent.run(
        report,
        rag_context={},
        generated_explanation="This also fixes cost:imaginary-rule.",
    )

    codes = {reason.code for reason in result.reasons}
    assert result.passed is False
    assert "unknown_finding_reference" in codes
    assert "invalid_doc_source_url" in codes
