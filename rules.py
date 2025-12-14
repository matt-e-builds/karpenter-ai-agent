from typing import List, Dict, Optional
from models import Issue, ProvisionerConfig, EC2NodeClassConfig


# -----------------------------
# Core analysis entrypoint
# -----------------------------


def run_analysis(
    provisioners: List[ProvisionerConfig],
    ec2_nodeclasses: List[EC2NodeClassConfig],
) -> List[Issue]:
    """
    Run rules-based analysis over Provisioners / NodePools and EC2NodeClasses.
    """
    issues: List[Issue] = []

    # Index nodeclasses by name for relationship checks (if needed later)
    nodeclass_by_name: Dict[str, EC2NodeClassConfig] = {
        nc.name: nc for nc in ec2_nodeclasses
    }

    for prov in provisioners:
        issues.extend(_check_spot(prov))
        issues.extend(_check_consolidation(prov))
        issues.extend(_check_graviton(prov))
        issues.extend(_check_ttl(prov))

        # Future relationship checks (NodePool → NodeClass) could go here
        if prov.nodeclass_name:
            _ = nodeclass_by_name.get(prov.nodeclass_name)

    for nc in ec2_nodeclasses:
        issues.extend(_check_nodeclass_instance_profile(nc))
        # Additional EC2NodeClass rules could be added here later

    return issues


# -----------------------------
# Individual rule checks
# -----------------------------


def _check_spot(prov: ProvisionerConfig) -> List[Issue]:
    """
    High severity if Spot is not allowed for a provisioner / nodepool.
    """
    if prov.spot_allowed:
        return []

    message = "Spot instances are not enabled for this provisioner."
    recommendation = (
        "Enable Spot capacity type to reduce costs by up to 90%. "
        "Add 'karpenter.sh/capacity-type: spot' to your requirements."
    )

    patch = f"""# Enable Spot capacity for provisioner '{prov.name}'
spec:
  requirements:
    - key: karpenter.sh/capacity-type
      operator: In
      values: ["spot", "on-demand"]
"""

    return [
        Issue(
            provisioner_name=prov.name,
            severity="high",
            category="Cost Optimization",
            message=message,
            recommendation=recommendation,
            patch_snippet=patch,
        )
    ]


def _check_consolidation(prov: ProvisionerConfig) -> List[Issue]:
    """
    High severity when consolidation is explicitly disabled.
    If consolidation is None (not set), we stay silent for now.
    """
    if prov.consolidation_enabled is False:
        message = "Consolidation is explicitly disabled."
        recommendation = (
            "Enable consolidation to automatically reduce cluster costs by "
            "consolidating workloads onto fewer nodes."
        )

        patch = f"""# Enable consolidation for provisioner '{prov.name}'
spec:
  consolidation:
    enabled: true
"""

        return [
            Issue(
                provisioner_name=prov.name,
                severity="high",
                category="Resource Efficiency",
                message=message,
                recommendation=recommendation,
                patch_snippet=patch,
            )
        ]

    return []


def _check_graviton(prov: ProvisionerConfig) -> List[Issue]:
    """
    Medium severity if the provisioner does not use any Graviton families.
    """
    if prov.graviton_used:
        return []

    message = "No Graviton instance families are used by this provisioner."
    recommendation = (
        "Consider adding ARM-based Graviton instance families to improve "
        "price-performance where workloads are compatible."
    )

    patch = f"""# Add Graviton instance families for provisioner '{prov.name}'
spec:
  requirements:
    - key: node.kubernetes.io/instance-type
      operator: In
      values: ["m6g.large", "c6g.large"]  # adjust to your needs
"""

    return [
        Issue(
            provisioner_name=prov.name,
            severity="medium",
            category="Cost Optimization",
            message=message,
            recommendation=recommendation,
            patch_snippet=patch,
        )
    ]


def _check_ttl(prov: ProvisionerConfig) -> List[Issue]:
    """
    TTL rules:

    - If ttlSecondsAfterEmpty (or equivalent) is NOT configured → MEDIUM severity.
    - If ttlSecondsAfterEmpty is configured but > 600 seconds (10 minutes) → LOW severity.

    We do NOT generalize across provisioners; this is per-provisioner only.
    """
    issues: List[Issue] = []

    ttl = prov.ttl_seconds_after_empty

    # 1) Missing TTL → MEDIUM
    if ttl is None:
        message = "ttlSecondsAfterEmpty (or equivalent) is not configured."
        recommendation = (
            "Set ttlSecondsAfterEmpty or an equivalent disruption TTL so empty "
            "nodes are terminated automatically and you do not pay for idle capacity."
        )

        patch = f"""# Set ttlSecondsAfterEmpty for provisioner '{prov.name}'
spec:
  ttlSecondsAfterEmpty: 300
"""

        issues.append(
            Issue(
                provisioner_name=prov.name,
                severity="medium",
                category="Cost Optimization",
                message=message,
                recommendation=recommendation,
                patch_snippet=patch,
            )
        )
        return issues  # If it's missing, we don't also treat it as 'too high'

    # 2) TTL present but too high (> 600s) → LOW
    if ttl > 600:
        message = (
            f"ttlSecondsAfterEmpty is set to {ttl} seconds (> 600 seconds)."
        )
        recommendation = (
            "Consider reducing ttlSecondsAfterEmpty for faster cleanup of unused "
            "nodes and to reduce idle capacity costs."
        )

        patch = f"""# Reduce ttlSecondsAfterEmpty for provisioner '{prov.name}'
spec:
  ttlSecondsAfterEmpty: 300  # previous value: {ttl}
"""

        issues.append(
            Issue(
                provisioner_name=prov.name,
                severity="low",
                category="Cost Optimization",
                message=message,
                recommendation=recommendation,
                patch_snippet=patch,
            )
        )

    return issues


def _check_nodeclass_instance_profile(nc: EC2NodeClassConfig) -> List[Issue]:
    """
    High severity if an EC2NodeClass has neither instanceProfile nor role set.
    """
    if nc.instance_profile or nc.role:
        return []

    message = (
        f"EC2NodeClass '{nc.name}' does not specify an instanceProfile or IAM role."
    )
    recommendation = (
        "Configure an instanceProfile or role so nodes receive the correct IAM permissions "
        "for EKS, cloud provider integration, and workload access."
    )

    patch = f"""# Example IAM configuration for EC2NodeClass '{nc.name}'
spec:
  instanceProfile: your-eks-node-instance-profile-name
  # or use:
  # role: your-eks-node-role-name
"""

    return [
        Issue(
            provisioner_name=nc.name,
            severity="high",
            category="EC2NodeClass – IAM",
            message=message,
            recommendation=recommendation,
            patch_snippet=patch,
        )
    ]


# -----------------------------
# Summary / scoring
# -----------------------------


def generate_summary(
    provisioners: List[ProvisionerConfig],
    issues: List[Issue],
    ec2_nodeclasses: List[EC2NodeClassConfig],
) -> Dict:
    """
    Build a summarized view of analysis results for the UI, LLM, and tests.

    Returns:
      {
        "issues_by_severity": {"high": int, "medium": int, "low": int},
        "optimization_status": {
            "total_provisioners": int,
            "spot_enabled": int,
            "graviton_used": int,
            "consolidation_enabled": int,
        },
        "health_score": int,          # 0–100
        "health_score_max": int,      # always 100, used by UI & tests
        "ec2_nodeclass_count": int,
      }
    """
    # Severity counts
    issues_by_severity: Dict[str, int] = {"high": 0, "medium": 0, "low": 0}
    for issue in issues:
        sev = (issue.severity or "").lower()
        if sev in issues_by_severity:
            issues_by_severity[sev] += 1

    # Optimization status across provisioners
    total_provisioners = len(provisioners)
    spot_enabled = sum(1 for p in provisioners if p.spot_allowed)
    graviton_used = sum(1 for p in provisioners if p.graviton_used)
    consolidation_enabled = sum(
        1 for p in provisioners if p.consolidation_enabled is True
    )

    optimization_status = {
        "total_provisioners": total_provisioners,
        "spot_enabled": spot_enabled,
        "graviton_used": graviton_used,
        "consolidation_enabled": consolidation_enabled,
    }

    health_score_max = 100
    health_score = _compute_health_score(
        issues_by_severity=issues_by_severity,
        optimization_status=optimization_status,
    )

    # Clamp defensively (should already be 0–100)
    if health_score < 0:
        health_score = 0
    if health_score > health_score_max:
        health_score = health_score_max

    return {
        "issues_by_severity": issues_by_severity,
        "optimization_status": optimization_status,
        "health_score": health_score,
        "health_score_max": health_score_max,
        "ec2_nodeclass_count": len(ec2_nodeclasses),
    }


def _compute_health_score(
    issues_by_severity: Dict[str, int],
    optimization_status: Dict[str, int],
) -> int:
    """
    Simple heuristic health score (0–100).

    - High severity issues hurt the most.
    - Medium severity issues hurt moderately.
    - Low severity issues hurt a little.
    - Small positive credit for each provisioner that already uses
      Spot, Graviton, and consolidation.

    Tests also expect that a non-empty issue set does not end up with a
    trivial 0 score for edge-case configs, so we apply a small floor.
    """
    high = issues_by_severity.get("high", 0)
    medium = issues_by_severity.get("medium", 0)
    low = issues_by_severity.get("low", 0)

    spot_good = optimization_status.get("spot_enabled", 0)
    grav_good = optimization_status.get("graviton_used", 0)
    cons_good = optimization_status.get("consolidation_enabled", 0)

    score = 100
    # Base penalties
    score -= 8 * high
    score -= 5 * medium
    score -= 2 * low

    # Positive credit for best practices
    score += 3 * spot_good
    score += 2 * grav_good
    score += 2 * cons_good

    # Clamp to [0, 100]
    if score < 0:
        score = 0
    if score > 100:
        score = 100

    # Test + UX requirement: avoid trivial 0 when there *are* issues.
    if score == 0 and (high + medium + low) > 0:
        score = 5

    return int(score)