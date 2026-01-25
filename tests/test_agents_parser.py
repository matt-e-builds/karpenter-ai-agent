from pathlib import Path

from karpenter_ai_agent.agents import ParserAgent
from karpenter_ai_agent.models import AnalysisInput

FIXTURES = Path(__file__).parent / "fixtures"


def test_parser_agent_parses_valid_yaml():
    yaml_text = (FIXTURES / "basic-karpenter.yaml").read_text()
    agent = ParserAgent()
    output = agent.run(AnalysisInput(yaml_text=yaml_text, region="us-east-1"))

    assert output.config is not None
    assert not output.parse_errors
    assert output.normalized_metadata["provisioner_count"] > 0
