# NodePool and EC2NodeClass Relationship
source: https://karpenter.sh/docs/concepts/nodepools/

NodePool and EC2NodeClass should be linked through `spec.template.spec.nodeClassRef`.
If the reference is missing or points to a non-existent EC2NodeClass, scheduling can fail
or nodes can launch with unexpected defaults.

Keep NodePool constraints focused on workload intent, and keep infrastructure-specific
settings in EC2NodeClass. This separation makes ownership clearer and reduces drift.

Common issue pattern: a NodePool has limits and disruption policies, but no valid
nodeClassRef target. That should be treated as a high-severity reliability and security risk.
