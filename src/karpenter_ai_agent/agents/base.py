from __future__ import annotations

from typing import Protocol

from karpenter_ai_agent.models import AnalysisInput, AgentResult


class BaseAgent(Protocol):
    name: str

    def run(self, analysis_input: AnalysisInput) -> AgentResult:
        ...
