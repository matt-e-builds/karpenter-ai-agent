from pathlib import Path

from fastapi.testclient import TestClient

import main
from karpenter_ai_agent.models import AnalysisInput
from karpenter_ai_agent.orchestration.graph import run_analysis_graph
from models import Issue as LegacyIssue

FIXTURES = Path(__file__).parent / "fixtures"


def _set_last_report(report):
    issues = [
        LegacyIssue(
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
    main.LAST_REPORT = report
    main.LAST_ISSUES = issues


def test_patch_bundle_route():
    yaml_text = (FIXTURES / "basic-karpenter.yaml").read_text()
    report = run_analysis_graph(AnalysisInput(yaml_text=yaml_text, region="us-east-1"))
    _set_last_report(report)

    client = TestClient(main.app)
    response = client.get("/download/patch-bundle.yaml?ttl=1")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-yaml")
    assert "ttlSecondsAfterEmpty" in response.text
