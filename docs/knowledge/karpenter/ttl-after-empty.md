# ttlSecondsAfterEmpty behavior
Source: https://karpenter.sh/docs/concepts/disruption/

Notes:
- ttlSecondsAfterEmpty is a legacy scale-down control for empty nodes.
- In newer Karpenter versions, disruption and consolidation controls are preferred.
- If ttlSecondsAfterEmpty is unset, empty nodes can persist longer than desired.
- Avoid overly aggressive TTLs that can cause churn and cold-start latency.
- Always check the resource kind and API version for the supported field name.
