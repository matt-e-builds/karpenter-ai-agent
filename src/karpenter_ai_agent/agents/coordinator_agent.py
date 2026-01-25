from __future__ import annotations

from karpenter_ai_agent.models import AnalysisInput, AnalysisReport
from karpenter_ai_agent.orchestration.graph import run_analysis_graph


class CoordinatorAgent:
    name = "coordinator"

    def run(self, analysis_input: AnalysisInput) -> AnalysisReport:
        return run_analysis_graph(analysis_input)
