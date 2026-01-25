from pathlib import Path

from karpenter_ai_agent.agents import ParserAgent, CostAgent
from karpenter_ai_agent.models import AnalysisInput

FIXTURES = Path(__file__).parent / "fixtures"


def test_cost_agent_flags_missing_spot_or_graviton():
    yaml_text = (FIXTURES / "basic-karpenter.yaml").read_text()
    parser = ParserAgent()
    parsed = parser.run(AnalysisInput(yaml_text=yaml_text))

    assert parsed.config is not None

    agent = CostAgent()
    result = agent.run(parsed.config)

    assert any(issue.category for issue in result.issues)
    assert any(issue.severity in ("high", "medium") for issue in result.issues)
