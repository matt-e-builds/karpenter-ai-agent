# NodePool vs Provisioner differences
Source: https://karpenter.sh/docs/concepts/

Notes:
- Provisioner is the legacy API; NodePool is the newer replacement.
- NodePool works with NodeClass (like EC2NodeClass) for infrastructure settings.
- Mixing Provisioner and NodePool in one cluster can be confusing; document intent.
- Ensure rules match the resource kind in use to avoid policy drift.
- Validate feature parity for fields that moved between API versions.
