# Consolidation and disruption basics
Source: https://karpenter.sh/docs/concepts/disruption/

Notes:
- Consolidation removes underutilized or empty nodes to reduce waste.
- Disruption settings control when Karpenter can terminate nodes.
- If consolidation is disabled, scale-down may be slower and more expensive.
- Prefer conservative policies for stateful or latency-sensitive workloads.
- Review max disruptions and budgets to avoid excessive churn.
- Align consolidation settings with cluster autoscaler expectations.
