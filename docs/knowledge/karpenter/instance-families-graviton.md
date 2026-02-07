# Instance families and Graviton usage
Source: https://karpenter.sh/docs/concepts/nodepools/

Notes:
- Explicit instance family requirements help avoid unintended defaults.
- Graviton (arm64) can reduce cost but requires compatible images and workloads.
- Mixed architectures need multi-arch images and scheduling constraints.
- Avoid pinning to a single family unless workload requirements demand it.
- Review allowed families when cost or availability issues surface.
