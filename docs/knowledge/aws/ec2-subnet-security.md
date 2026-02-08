# EC2 subnet and security group selection
Source: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-network-security.html

Notes:
- Subnets control IP ranges and routing for nodes.
- Security groups define allowed network flows for node ENIs.
- Overly broad selectors can place nodes into unintended networks.
- Tag-based selectors help keep infra aligned with cluster boundaries.
- Validate selectors exist in the target region and VPC.
