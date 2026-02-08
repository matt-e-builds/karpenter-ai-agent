from __future__ import annotations

from typing import Dict, List

from karpenter_ai_agent.models import AnalysisInput, ParserOutput, AgentResult, AnalysisReport, Issue
from karpenter_ai_agent.models.patches import build_patch_suggestions
from rules import generate_summary
from models import ProvisionerConfig, EC2NodeClassConfig, Issue as LegacyIssue


def _issues_by_severity(issues: List[Issue]) -> Dict[str, int]:
    counts = {"high": 0, "medium": 0, "low": 0}
    for issue in issues:
        if issue.severity in counts:
            counts[issue.severity] += 1
    return counts


def aggregate_results(
    *,
    analysis_input: AnalysisInput,
    parser_output: ParserOutput | None,
    cost_result: AgentResult | None,
    reliability_result: AgentResult | None,
    security_result: AgentResult | None,
) -> AnalysisReport:
    issues: List[Issue] = []
    for result in (cost_result, reliability_result, security_result):
        if result:
            issues.extend(result.issues)

    patch_suggestions = build_patch_suggestions(issues)

    if parser_output is None or parser_output.config is None:
        return AnalysisReport(
            region=analysis_input.region,
            health_score=0,
            issues=issues,
            issues_by_severity=_issues_by_severity(issues),
            optimizer_flags={},
            parse_errors=(parser_output.parse_errors if parser_output else []),
            patch_suggestions=patch_suggestions,
        )

    provisioners = [ProvisionerConfig(**p.model_dump()) for p in parser_output.config.provisioners]
    nodeclasses = [EC2NodeClassConfig(**nc.model_dump()) for nc in parser_output.config.ec2_nodeclasses]

    legacy_issues = [
        LegacyIssue(
            severity=i.severity,
            category=i.category,
            message=i.message,
            recommendation=i.recommendation,
            provisioner_name=i.resource_name,
            patch_snippet=i.patch_snippet,
        )
        for i in issues
    ]

    summary = generate_summary(provisioners, legacy_issues, nodeclasses)

    nodepool_refs = {
        prov.name: prov.nodeclass_name
        for prov in parser_output.config.provisioners
        if prov.kind == "NodePool"
    }

    return AnalysisReport(
        region=analysis_input.region,
        health_score=summary["health_score"],
        issues=issues,
        issues_by_severity=summary["issues_by_severity"],
        optimizer_flags=summary["optimization_status"],
        parse_errors=parser_output.parse_errors,
        patch_suggestions=patch_suggestions,
        raw={
            "nodepool_refs": nodepool_refs,
            "nodeclass_names": [nc.name for nc in parser_output.config.ec2_nodeclasses],
        },
    )
