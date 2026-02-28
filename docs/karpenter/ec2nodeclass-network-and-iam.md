# EC2NodeClass Network and IAM Requirements
source: https://karpenter.sh/docs/concepts/nodeclasses/

EC2NodeClass should include subnet and security group selectors that target approved network
resources. Missing selectors can prevent provisioning or lead to broad, unsafe defaults.

The EC2NodeClass identity should be explicit using either `spec.role` or
`spec.instanceProfile`. Ensure the IAM permissions are scoped to required AWS APIs only.

Avoid relying on implicit discovery behavior in production clusters. Explicit selectors and
identity configuration improve repeatability and incident response.
