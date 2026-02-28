# Spot, Consolidation, and Disruption Controls
source: https://karpenter.sh/docs/concepts/disruption/

When using Spot capacity, pair requirements with disruption controls and clear workload
tolerations. Unbounded Spot usage without fallback can reduce reliability.

Consolidation settings should align with workload stability requirements. Aggressive
consolidation can increase churn; disabled consolidation can increase cost.

Use disruption budgets and safe eviction settings to balance savings and uptime. Review
the effects of `ttlSecondsAfterEmpty` and disruption policy values together.
