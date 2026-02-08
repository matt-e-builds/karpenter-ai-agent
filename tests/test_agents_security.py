from pathlib import Path

from karpenter_ai_agent.agents import ParserAgent, SecurityAgent
from karpenter_ai_agent.models import AnalysisInput

FIXTURES = Path(__file__).parent / "fixtures"


def test_security_agent_flags_missing_iam_or_networking():
    yaml_text = (FIXTURES / "edge-cases-karpenter.yaml").read_text()
    parser = ParserAgent()
    parsed = parser.run(AnalysisInput(yaml_text=yaml_text))

    assert parsed.config is not None

    agent = SecurityAgent()
    result = agent.run(parsed.config)

    assert result.issues


def test_security_agent_flags_ami_and_iam_issues():
    yaml_text = (FIXTURES / "ec2nodeclass-ami.yaml").read_text()
    parser = ParserAgent()
    parsed = parser.run(AnalysisInput(yaml_text=yaml_text))

    assert parsed.config is not None

    agent = SecurityAgent()
    result = agent.run(parsed.config)

    rule_ids = {issue.rule_id for issue in result.issues}
    assert "security:missing-ami-selectors" in rule_ids
    assert "security:overly-broad-ami-selectors" in rule_ids
    assert "security:ambiguous-iam-settings" in rule_ids
    assert "security:invalid-iam-settings" in rule_ids


def test_security_agent_flags_nodepool_nodeclass_mismatches():
    yaml_text = (FIXTURES / "nodepool-nodeclass.yaml").read_text()
    parser = ParserAgent()
    parsed = parser.run(AnalysisInput(yaml_text=yaml_text))

    assert parsed.config is not None

    agent = SecurityAgent()
    result = agent.run(parsed.config)

    issues_by_rule = {issue.rule_id: issue for issue in result.issues}
    missing_issue = issues_by_rule.get("security:missing-nodeclass")
    assert missing_issue is not None
    assert "missing-class-pool" in missing_issue.message
    assert "missing-class" in missing_issue.message
    assert missing_issue.patch_snippet
    assert "REPLACE_WITH_VALID_NODECLASS" in missing_issue.patch_snippet

    no_ref_issue = issues_by_rule.get("security:missing-nodeclass-ref")
    assert no_ref_issue is not None
    assert "no-ref-pool" in no_ref_issue.message
    assert no_ref_issue.patch_snippet
    assert "nodeClassRef" in no_ref_issue.patch_snippet
