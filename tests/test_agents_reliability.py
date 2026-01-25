from pathlib import Path

from karpenter_ai_agent.agents import ParserAgent, ReliabilityAgent
from karpenter_ai_agent.models import AnalysisInput

FIXTURES = Path(__file__).parent / "fixtures"


def test_reliability_agent_flags_ttl_or_consolidation():
    yaml_text = (FIXTURES / "edge-cases-karpenter.yaml").read_text()
    parser = ParserAgent()
    parsed = parser.run(AnalysisInput(yaml_text=yaml_text))

    assert parsed.config is not None

    agent = ReliabilityAgent()
    result = agent.run(parsed.config)

    assert any(issue.severity in ("high", "medium", "low") for issue in result.issues)
