from __future__ import annotations

from typing import List

from karpenter_ai_agent.models import AgentResult, CanonicalConfig, Issue
from karpenter_ai_agent.agents._adapters import to_legacy_provisioner, issue_from_legacy
from rules import _check_consolidation, _check_ttl


class ReliabilityAgent:
    name = "reliability"

    def run(self, config: CanonicalConfig) -> AgentResult:
        legacy_provisioners = [to_legacy_provisioner(p) for p in config.provisioners]

        issues: List[Issue] = []
        for prov in legacy_provisioners:
            issues.extend(
                issue_from_legacy(issue, "reliability")
                for issue in _check_consolidation(prov) + _check_ttl(prov)
            )

        return AgentResult(issues=issues)
