# RAG (Retrieval-Augmented Generation)

This project uses a small, curated local corpus to ground explanation-only outputs.
The corpus is stored under docs/knowledge and includes Karpenter and AWS references
written as short internal summaries with source URLs.

## What is indexed
- Curated Karpenter docs summaries (NodePool, EC2NodeClass, disruption, Spot)
- Curated AWS EKS/EC2 references relevant to node IAM, AMIs, and networking

## Scope limits
- Retrieval is local and deterministic (no web scraping at runtime).
- Explanations never affect findings, severities, or scoring.
- LLM use is optional and only for narrative explanation quality.

## Refresh process
1) Add or update a short summary file under docs/knowledge.
2) Keep each file concise (10-40 lines) and include a Source URL.
3) Run tests to confirm retrieval still works.
