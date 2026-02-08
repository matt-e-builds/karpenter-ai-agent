from pathlib import Path

from karpenter_ai_agent.models import AnalysisInput
from karpenter_ai_agent.orchestration.graph import run_analysis_graph

FIXTURES = Path(__file__).parent / "fixtures"


def test_orchestration_flow_valid_yaml():
    yaml_text = (FIXTURES / "basic-karpenter.yaml").read_text()
    report = run_analysis_graph(AnalysisInput(yaml_text=yaml_text, region="us-east-1"))

    assert report.health_score >= 0
    assert report.issues_by_severity
    assert not report.parse_errors


def test_orchestration_flow_invalid_yaml():
    bad_yaml = "kind: Provisioner\nmetadata: ["  # invalid YAML
    report = run_analysis_graph(AnalysisInput(yaml_text=bad_yaml))

    assert report.parse_errors


def test_orchestration_flow_explain_evaluate_does_not_change_findings():
    yaml_text = (FIXTURES / "basic-karpenter.yaml").read_text()
    base_report = run_analysis_graph(AnalysisInput(yaml_text=yaml_text, region="us-east-1"))
    eval_report = run_analysis_graph(
        AnalysisInput(
            yaml_text=yaml_text,
            region="us-east-1",
            options={"enable_explanations": True, "enable_evaluator": True},
        )
    )

    base_fingerprints = [
        (issue.rule_id, issue.severity, issue.message) for issue in base_report.issues
    ]
    eval_fingerprints = [
        (issue.rule_id, issue.severity, issue.message) for issue in eval_report.issues
    ]

    assert base_fingerprints == eval_fingerprints
    assert base_report.issues_by_severity == eval_report.issues_by_severity


def test_orchestration_flow_flags_missing_nodeclass():
    yaml_text = (FIXTURES / "nodepool-nodeclass.yaml").read_text()
    report = run_analysis_graph(AnalysisInput(yaml_text=yaml_text, region="us-east-1"))

    rule_ids = {issue.rule_id for issue in report.issues}
    assert "security:missing-nodeclass" in rule_ids
