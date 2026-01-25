from __future__ import annotations

import re
from typing import List

from karpenter_ai_agent.models import (
    CanonicalProvisioner,
    CanonicalEC2NodeClass,
    Issue as ContractIssue,
)
from models import ProvisionerConfig, EC2NodeClassConfig, Issue as LegacyIssue


def to_legacy_provisioner(config: CanonicalProvisioner) -> ProvisionerConfig:
    return ProvisionerConfig(
        name=config.name,
        kind=config.kind,
        nodeclass_name=config.nodeclass_name,
        consolidation_enabled=config.consolidation_enabled,
        spot_allowed=config.spot_allowed,
        instance_families=list(config.instance_families),
        graviton_used=config.graviton_used,
        ttl_seconds_after_empty=config.ttl_seconds_after_empty,
        raw_yaml=dict(config.raw_yaml),
    )


def to_legacy_nodeclass(config: CanonicalEC2NodeClass) -> EC2NodeClassConfig:
    return EC2NodeClassConfig(
        name=config.name,
        instance_types=list(config.instance_types),
        ami_selector_present=config.ami_selector_present,
        security_groups_present=config.security_groups_present,
        subnets_present=config.subnets_present,
        instance_profile=config.instance_profile,
        role=config.role,
        raw_yaml=dict(config.raw_yaml),
    )


def issue_from_legacy(issue: LegacyIssue, prefix: str) -> ContractIssue:
    rule_id = _rule_id_from_message(prefix, issue.message)
    return ContractIssue(
        rule_id=rule_id,
        severity=issue.severity,
        category=issue.category,
        message=issue.message,
        recommendation=issue.recommendation,
        resource_name=issue.provisioner_name,
        resource_kind=issue.resource_kind,
        patch_snippet=issue.patch_snippet,
        metadata={
            "field": issue.field,
            "resource_name": issue.resource_name,
        },
    )


def _rule_id_from_message(prefix: str, message: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", message.lower()).strip("-")
    base = base[:60] if base else "unknown"
    return f"{prefix}:{base}"
