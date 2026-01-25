from __future__ import annotations

from typing import List

from karpenter_ai_agent.models import AgentResult, CanonicalConfig, Issue
from karpenter_ai_agent.agents._adapters import to_legacy_nodeclass, issue_from_legacy
from rules import _check_nodeclass_instance_profile


class SecurityAgent:
    name = "security"

    def run(self, config: CanonicalConfig) -> AgentResult:
        legacy_nodeclasses = [to_legacy_nodeclass(nc) for nc in config.ec2_nodeclasses]

        issues: List[Issue] = []
        for nc in legacy_nodeclasses:
            issues.extend(
                issue_from_legacy(issue, "security")
                for issue in _check_nodeclass_instance_profile(nc)
            )

        for nc in config.ec2_nodeclasses:
            if not nc.security_groups_present:
                issues.append(
                    Issue(
                        rule_id="security:missing-security-groups",
                        severity="high",
                        category="EC2NodeClass – Networking",
                        message=(
                            f"EC2NodeClass '{nc.name}' does not specify security groups."
                        ),
                        recommendation=(
                            "Configure securityGroupSelectorTerms to ensure nodes "
                            "are launched with the correct network security posture."
                        ),
                        resource_name=nc.name,
                        resource_kind="EC2NodeClass",
                    )
                )
            if not nc.subnets_present:
                issues.append(
                    Issue(
                        rule_id="security:missing-subnets",
                        severity="high",
                        category="EC2NodeClass – Networking",
                        message=(
                            f"EC2NodeClass '{nc.name}' does not specify subnets."
                        ),
                        recommendation=(
                            "Configure subnetSelectorTerms so nodes are placed into "
                            "approved subnets for your cluster."
                        ),
                        resource_name=nc.name,
                        resource_kind="EC2NodeClass",
                    )
                )

        return AgentResult(issues=issues)
