# EC2NodeClass subnet and security group selectors
Source: https://karpenter.sh/docs/concepts/nodeclasses/

Notes:
- Subnet selectors define where nodes can launch; missing selectors can break scheduling.
- Security group selectors control network access for nodes.
- Use tag-based selectors to keep infra aligned with cluster boundaries.
- Avoid overly broad selectors that allow unintended subnets or security groups.
- Validate selectors exist in the target region and are reachable by the cluster.
