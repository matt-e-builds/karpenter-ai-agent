from pathlib import Path

from karpenter_ai_agent.agents import CoordinatorAgent
from karpenter_ai_agent.models import AnalysisInput
from karpenter_ai_agent.rag.explain import attach_issue_explanations
from models import Issue

FIXTURES = Path(__file__).parent / "fixtures"


def test_issue_docs_attached_without_llm():
    yaml_text = (FIXTURES / "basic-karpenter.yaml").read_text()
    report = CoordinatorAgent().run(AnalysisInput(yaml_text=yaml_text, region="us-east-1"))

    issues = [
        Issue(
            severity=i.severity,
            category=i.category,
            message=i.message,
            recommendation=i.recommendation,
            provisioner_name=i.resource_name,
            resource_kind=i.resource_kind,
            resource_name=i.resource_name,
            patch_snippet=i.patch_snippet,
            field=(i.metadata.get("field") if isinstance(i.metadata, dict) else None),
        )
        for i in report.issues
    ]

    severities_before = [issue.severity for issue in issues]
    attach_issue_explanations(issues, llm_available=False)

    severities_after = [issue.severity for issue in issues]
    assert severities_before == severities_after
    assert any(issue.explanation and issue.explanation.docs for issue in issues)
