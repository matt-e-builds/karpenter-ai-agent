# Common misconfiguration patterns
Source: https://karpenter.sh/docs/concepts/

Notes:
- Missing or empty selectors (subnets, security groups, AMIs) can block provisioning.
- Overly strict requirements can make scheduling impossible.
- Disabling consolidation can leave empty nodes running longer than intended.
- Spot-only pools without interruption handling can impact availability.
- Inconsistent labels between NodePool/Provisioner and workloads lead to drift.
- Keep API version and field names aligned with the installed Karpenter version.
