# EC2NodeClass instanceProfile and IAM role
Source: https://karpenter.sh/docs/concepts/nodeclasses/

Notes:
- instanceProfile or role is required for node permissions.
- Missing IAM settings can prevent node launch or block cloud API access.
- Use a dedicated instance profile scoped to the cluster.
- Avoid sharing instance profiles across unrelated clusters or environments.
- Prefer least-privilege policies; audit required permissions regularly.
