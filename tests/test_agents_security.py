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
