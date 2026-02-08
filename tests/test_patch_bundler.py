from pathlib import Path

from karpenter_ai_agent.models import AnalysisInput
from karpenter_ai_agent.orchestration.graph import run_analysis_graph
from karpenter_ai_agent.remediation.bundler import (
    build_bundle_yaml,
    build_bundle_yaml_for_nodepool,
    build_bundles,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_patch_bundler_filters_categories():
    yaml_text = (FIXTURES / "basic-karpenter.yaml").read_text()
    report = run_analysis_graph(AnalysisInput(yaml_text=yaml_text, region="us-east-1"))

    ttl_only = build_bundle_yaml(report, {"ttl"})
    assert "ttlSecondsAfterEmpty" in ttl_only
    assert "Spot instances" not in ttl_only


def test_patch_bundler_groups_nodepool_and_nodeclass():
    yaml_text = (FIXTURES / "nodepool-nodeclass.yaml").read_text()
    report = run_analysis_graph(AnalysisInput(yaml_text=yaml_text, region="us-east-1"))

    bundles = build_bundles(report, {"nodeclass"})
    assert list(bundles.keys()) == sorted(bundles.keys())

    missing_bundle = bundles.get("missing-class-pool")
    assert missing_bundle is not None
    assert "REPLACE_WITH_VALID_NODECLASS" in missing_bundle.bundle_yaml

    good_bundle = bundles.get("good-pool")
    assert good_bundle is not None
    assert "instanceProfile" in good_bundle.bundle_yaml

    nodepool_yaml = build_bundle_yaml_for_nodepool(report, "missing-class-pool", {"nodeclass"})
    assert "REPLACE_WITH_VALID_NODECLASS" in nodepool_yaml
