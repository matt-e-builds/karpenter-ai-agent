from __future__ import annotations

from typing import List

from karpenter_ai_agent.mcp.runtime import LocalMCPClient, ToolRegistry, ToolSpec
from karpenter_ai_agent.mcp.schemas import ValidateYamlSchemaInput, ValidateYamlSchemaOutput
from karpenter_ai_agent.mcp.tools import validate_yaml_schema
from karpenter_ai_agent.models import (
    AnalysisInput,
    ParserOutput,
    CanonicalConfig,
    CanonicalProvisioner,
    CanonicalEC2NodeClass,
)
from parser import parse_provisioner_yaml


class ParserAgent:
    name = "parser"

    def __init__(self, mcp_client: LocalMCPClient | None = None) -> None:
        if mcp_client is None:
            registry = ToolRegistry()
            registry.register(
                ToolSpec(
                    name="validate_yaml_schema",
                    input_model=ValidateYamlSchemaInput,
                    output_model=ValidateYamlSchemaOutput,
                    handler=validate_yaml_schema,
                )
            )
            mcp_client = LocalMCPClient(registry)
        self._mcp = mcp_client

    def run(self, analysis_input: AnalysisInput) -> ParserOutput:
        validation = self._mcp.call(
            "validate_yaml_schema", {"yaml_text": analysis_input.yaml_text}
        )
        if not validation.valid:
            return ParserOutput(config=None, parse_errors=validation.errors)

        provisioners, nodeclasses = parse_provisioner_yaml(analysis_input.yaml_text)

        canonical_provisioners: List[CanonicalProvisioner] = [
            CanonicalProvisioner(**p.__dict__) for p in provisioners
        ]
        canonical_nodeclasses: List[CanonicalEC2NodeClass] = [
            CanonicalEC2NodeClass(**nc.__dict__) for nc in nodeclasses
        ]

        config = CanonicalConfig(
            provisioners=canonical_provisioners,
            ec2_nodeclasses=canonical_nodeclasses,
        )

        return ParserOutput(
            config=config,
            normalized_metadata={
                "provisioner_count": len(canonical_provisioners),
                "nodeclass_count": len(canonical_nodeclasses),
            },
        )
