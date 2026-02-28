from pathlib import Path

from karpenter_ai_agent.models import AnalysisInput
from karpenter_ai_agent.models.evaluation import EvaluationReason, EvaluationResult
from karpenter_ai_agent.orchestration.graph import run_analysis_graph

FIXTURES = Path(__file__).parent / "fixtures"


def test_explanation_flow_retries_once_and_fails_closed(monkeypatch):
    calls = {"count": 0}

    def always_fail(*args, **kwargs):  # noqa: ANN002, ANN003
        calls["count"] += 1
        return EvaluationResult(
            passed=False,
            reasons=[
                EvaluationReason(
                    code="hallucinated_citation",
                    message="Citation was not present in RAG context.",
                )
            ],
            notes=["hallucinated_citation"],
        )

    monkeypatch.setattr(
        "karpenter_ai_agent.orchestration.graph.evaluator_agent.run",
        always_fail,
    )

    yaml_text = (FIXTURES / "basic-karpenter.yaml").read_text()
    report = run_analysis_graph(
        AnalysisInput(
            yaml_text=yaml_text,
            region="us-east-1",
            options={"enable_explanations": True, "enable_evaluator": True},
        )
    )

    assert calls["count"] == 2
    assert report.raw.get("evaluation_retries") == 1
    assert report.raw.get("explanation_fail_closed") is True
    assert all(issue.explanation is None for issue in report.issues)


def test_explanation_flow_retries_once_and_keeps_explanations_when_second_passes(monkeypatch):
    calls = {"count": 0}

    def fail_then_pass(*args, **kwargs):  # noqa: ANN002, ANN003
        calls["count"] += 1
        if calls["count"] == 1:
            return EvaluationResult(
                passed=False,
                reasons=[
                    EvaluationReason(
                        code="missing_required_docs",
                        message="Explanation is missing required citations.",
                    )
                ],
                notes=["missing_required_docs"],
            )
        return EvaluationResult(passed=True, reasons=[], notes=[])

    monkeypatch.setattr(
        "karpenter_ai_agent.orchestration.graph.evaluator_agent.run",
        fail_then_pass,
    )

    yaml_text = (FIXTURES / "basic-karpenter.yaml").read_text()
    report = run_analysis_graph(
        AnalysisInput(
            yaml_text=yaml_text,
            region="us-east-1",
            options={"enable_explanations": True, "enable_evaluator": True},
        )
    )

    assert calls["count"] == 2
    assert report.raw.get("evaluation_retries") == 1
    assert report.raw.get("evaluation_passed") is True
