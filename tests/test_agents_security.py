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
