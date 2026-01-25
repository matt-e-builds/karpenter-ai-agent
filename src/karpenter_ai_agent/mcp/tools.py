from __future__ import annotations

from typing import Dict, Any

from karpenter_ai_agent.models import ParseError, CanonicalConfig
from karpenter_ai_agent.mcp.schemas import (
    ValidateYamlSchemaInput,
    ValidateYamlSchemaOutput,
    EstimateCostSignalsInput,
    EstimateCostSignalsOutput,
    ExplainRecommendationInput,
    ExplainRecommendationOutput,
)
from parser import parse_provisioner_yaml


def validate_yaml_schema(
    payload: ValidateYamlSchemaInput,
) -> ValidateYamlSchemaOutput:
    """Validate YAML structure using existing parser logic."""
    try:
        parse_provisioner_yaml(payload.yaml_text)
        return ValidateYamlSchemaOutput(valid=True)
    except Exception as exc:  # noqa: BLE001
        return ValidateYamlSchemaOutput(
            valid=False,
            errors=[ParseError(message=str(exc))],
        )


def estimate_cost_signals(
    payload: EstimateCostSignalsInput,
) -> EstimateCostSignalsOutput:
    """Return deterministic cost-related signals from the canonical config."""
    provisioners = payload.config.provisioners
    signals: Dict[str, Any] = {
        "total_provisioners": len(provisioners),
        "spot_enabled": sum(1 for p in provisioners if p.spot_allowed),
        "graviton_used": sum(1 for p in provisioners if p.graviton_used),
    }
    return EstimateCostSignalsOutput(signals=signals)


def explain_recommendation(
    payload: ExplainRecommendationInput,
) -> ExplainRecommendationOutput:
    """Return a deterministic, template-based explanation."""
    explanation = (
        f"Rule '{payload.rule_id}' triggered based on the provided configuration. "
        "Review the recommendation and apply only after validation."
    )
    return ExplainRecommendationOutput(explanation=explanation)
