# EKS node IAM permissions
Source: https://docs.aws.amazon.com/eks/latest/userguide/worker-node-iam-role.html

Notes:
- Worker nodes need an IAM role or instance profile with EKS node permissions.
- Missing permissions can block node registration or cluster API access.
- Keep node IAM roles scoped to the cluster and required AWS services.
- Avoid sharing node roles across unrelated clusters or environments.
- Review managed policies and custom permissions regularly.
