from __future__ import annotations

from typing import List, Optional

from karpenter_ai_agent.mcp.runtime import LocalMCPClient, ToolRegistry, ToolSpec
from karpenter_ai_agent.mcp.schemas import EstimateCostSignalsInput, EstimateCostSignalsOutput
from karpenter_ai_agent.mcp.tools import estimate_cost_signals
from karpenter_ai_agent.models import AgentResult, CanonicalConfig, Issue
from karpenter_ai_agent.agents._adapters import to_legacy_provisioner, issue_from_legacy
from rules import _check_spot, _check_graviton


class CostAgent:
    name = "cost"

    def __init__(self, mcp_client: LocalMCPClient | None = None) -> None:
        if mcp_client is None:
            registry = ToolRegistry()
            registry.register(
                ToolSpec(
                    name="estimate_cost_signals",
                    input_model=EstimateCostSignalsInput,
                    output_model=EstimateCostSignalsOutput,
                    handler=estimate_cost_signals,
                )
            )
            mcp_client = LocalMCPClient(registry)
        self._mcp = mcp_client

    def run(
        self,
        config: CanonicalConfig,
        region: Optional[str] = None,
        monthly_spend: Optional[float] = None,
    ) -> AgentResult:
        legacy_provisioners = [to_legacy_provisioner(p) for p in config.provisioners]

        issues: List[Issue] = []
        for prov in legacy_provisioners:
            issues.extend(
                issue_from_legacy(issue, "cost")
                for issue in _check_spot(prov) + _check_graviton(prov)
            )

        signals = self._mcp.call(
            "estimate_cost_signals",
            {
                "config": config.model_dump(),
                "region": region,
                "monthly_spend": monthly_spend,
            },
        )

        return AgentResult(issues=issues, signals=signals.signals)
