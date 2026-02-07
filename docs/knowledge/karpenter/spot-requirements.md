# Spot capacity types and requirements
Source: https://karpenter.sh/docs/concepts/nodepools/

Notes:
- Spot capacity is enabled by allowing the "spot" capacity type in requirements.
- If a NodePool or Provisioner omits spot, Karpenter will only launch on-demand.
- Mixed capacity can improve cost but requires workloads to tolerate interruptions.
- Keep requirements consistent with application SLAs; do not force spot for critical pods.
- Validate that interruption handling (PDBs, disruption budgets) is in place.
- Prefer explicit requirements over defaults to avoid accidental on-demand bias.
