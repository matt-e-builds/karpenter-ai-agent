from __future__ import annotations

from typing import List

from karpenter_ai_agent.models import AgentResult, CanonicalConfig, Issue
from karpenter_ai_agent.agents._adapters import to_legacy_nodeclass, issue_from_legacy
from rules import _check_nodeclass_instance_profile


def _normalized_str(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _extract_ami_selector_terms(raw_yaml: dict) -> list[dict]:
    spec = raw_yaml.get("spec", {}) if isinstance(raw_yaml, dict) else {}
    terms = spec.get("amiSelectorTerms")
    if isinstance(terms, list):
        return [term for term in terms if isinstance(term, dict)]
    return []


def _is_overly_broad_ami_term(term: dict) -> bool:
    if not term:
        return True
    allowed_keys = {"id", "name", "tags", "owners", "owner", "alias", "nameRegex"}
    if not any(key in term for key in allowed_keys):
        return True
    tags = term.get("tags")
    if isinstance(tags, dict) and not tags:
        return True
    for key in ("id", "name", "alias", "nameRegex"):
        value = term.get(key)
        if isinstance(value, str) and value.strip() == "*":
            return True
    return False


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
            ami_terms = _extract_ami_selector_terms(nc.raw_yaml)
            if not nc.ami_selector_present:
                issues.append(
                    Issue(
                        rule_id="security:missing-ami-selectors",
                        severity="high",
                        category="EC2NodeClass – AMI",
                        message=f"EC2NodeClass '{nc.name}' does not specify AMI selectors.",
                        recommendation=(
                            "Configure amiSelectorTerms or amiFamily to ensure nodes "
                            "launch with approved AMIs."
                        ),
                        patch_snippet=(
                            f"# Example AMI selector for EC2NodeClass '{nc.name}'\n"
                            "spec:\n"
                            "  amiSelectorTerms:\n"
                            "    - id: \"ami-0123456789abcdef0\"\n"
                        ),
                        resource_name=nc.name,
                        resource_kind="EC2NodeClass",
                        metadata={"field": "spec.amiSelectorTerms"},
                    )
                )
            elif any(_is_overly_broad_ami_term(term) for term in ami_terms):
                issues.append(
                    Issue(
                        rule_id="security:overly-broad-ami-selectors",
                        severity="medium",
                        category="EC2NodeClass – AMI",
                        message=(
                            f"EC2NodeClass '{nc.name}' uses overly broad AMI selectors."
                        ),
                        recommendation=(
                            "Tighten amiSelectorTerms with specific AMI IDs or tags "
                            "to prevent unintended images."
                        ),
                        patch_snippet=(
                            f"# Example tightened AMI selector for EC2NodeClass '{nc.name}'\n"
                            "spec:\n"
                            "  amiSelectorTerms:\n"
                            "    - tags:\n"
                            "        karpenter.sh/discovery: \"your-cluster\"\n"
                        ),
                        resource_name=nc.name,
                        resource_kind="EC2NodeClass",
                        metadata={"field": "spec.amiSelectorTerms"},
                    )
                )

            instance_profile = _normalized_str(nc.instance_profile)
            role = _normalized_str(nc.role)
            if (nc.instance_profile and not instance_profile) or (nc.role and not role):
                issues.append(
                    Issue(
                        rule_id="security:invalid-iam-settings",
                        severity="high",
                        category="EC2NodeClass – IAM",
                        message=(
                            f"EC2NodeClass '{nc.name}' has an invalid instanceProfile or role."
                        ),
                        recommendation=(
                            "Set instanceProfile or role to a valid IAM identifier "
                            "to ensure node permissions are configured correctly."
                        ),
                        patch_snippet=(
                            f"# Example IAM configuration for EC2NodeClass '{nc.name}'\n"
                            "spec:\n"
                            "  instanceProfile: your-eks-node-instance-profile-name\n"
                        ),
                        resource_name=nc.name,
                        resource_kind="EC2NodeClass",
                        metadata={"field": "spec.instanceProfile"},
                    )
                )
            if instance_profile and role:
                issues.append(
                    Issue(
                        rule_id="security:ambiguous-iam-settings",
                        severity="medium",
                        category="EC2NodeClass – IAM",
                        message=(
                            f"EC2NodeClass '{nc.name}' sets both instanceProfile and role."
                        ),
                        recommendation=(
                            "Choose either instanceProfile or role to avoid ambiguity."
                        ),
                        patch_snippet=(
                            f"# Example IAM configuration for EC2NodeClass '{nc.name}'\n"
                            "spec:\n"
                            "  instanceProfile: your-eks-node-instance-profile-name\n"
                            "  # Remove the role field if not required.\n"
                        ),
                        resource_name=nc.name,
                        resource_kind="EC2NodeClass",
                        metadata={"field": "spec.instanceProfile"},
                    )
                )

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
                        patch_snippet=(
                            f"# Example security group selector for EC2NodeClass '{nc.name}'\n"
                            "spec:\n"
                            "  securityGroupSelectorTerms:\n"
                            "    - tags:\n"
                            "        Name: \"eks-node-sg\"\n"
                        ),
                        resource_name=nc.name,
                        resource_kind="EC2NodeClass",
                        metadata={"field": "spec.securityGroupSelectorTerms"},
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
                        patch_snippet=(
                            f"# Example subnet selector for EC2NodeClass '{nc.name}'\n"
                            "spec:\n"
                            "  subnetSelectorTerms:\n"
                            "    - tags:\n"
                            "        Name: \"private-*\"\n"
                        ),
                        resource_name=nc.name,
                        resource_kind="EC2NodeClass",
                        metadata={"field": "spec.subnetSelectorTerms"},
                    )
                )

        return AgentResult(issues=issues)
