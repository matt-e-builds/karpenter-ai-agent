# Karpenter AI Agent – Roadmap (Open Source)

> This roadmap outlines planned improvements for the **open-source Karpenter AI Agent**.  
> All items below focus on deterministic analysis, explainability, and safe automation.  
> 
---
## Current State

- Multi-agent structure (ParserAgent, CostAgent, ReliabilityAgent, SecurityAgent, CoordinatorAgent)
- LangGraph orchestration with deterministic flow and parse short-circuit
- MCP-style local tooling layer for deterministic helpers
- Agent unit tests + orchestration integration tests

---

## Completed

- Multi-agent architecture + Pydantic contracts
- LangGraph orchestration + CoordinatorAgent
- Internal MCP-compatible tool runtime (read-only, deterministic)
- Deterministic health scoring (0–100) in UI
- Agent unit tests + orchestration flow tests

---

## Roadmap Phases (Next)

### Step 1 — Expand EC2NodeClass rule coverage

- Detect missing AMI selectors
- Detect incomplete subnet selector configuration
- Detect incomplete security group selector configuration
- Validate IAM role/instanceProfile correctness
- Cross-validate NodePool ↔ EC2NodeClass references
- Generate patch suggestions for NodeClass findings

---

### Step 2 — Patch bundling and export

- Generate combined patch bundles grouped by NodePool
- Allow include/exclude of Spot, consolidation, TTL, Graviton fixes
- Export HTML and PDF reports for sharing

---

### Step 3 — UI/UX improvements

- Filtering and sorting by severity, name, and score
- Side-by-side comparison of two configurations
- Clear visual explanation of why each rule fired

---

### Step 4 — Regression fixtures and validation pack

- Add benchmark fixtures from public Karpenter examples
- Build a regression pack to prevent rule drift
- Expand integration tests for edge-case YAML

---

### Step 5 — Optional integrations (OSS)

- Document optional Prometheus/Cost Explorer inputs (out of scope for core logic)
- Provide structured JSON output for automation

---

## Planned Enhancements (OSS)

### Cost-focused analysis improvements

- Instance family diversity checks
- Estimated relative cost impact per recommendation
- Improved scoring weights based on AWS pricing characteristics
- Detection of Spot-only configurations without on-demand fallback
- ARM64 compatibility hints for Graviton adoption

---

### Reliability & operational best-practice checks

- Detect Karpenter controller placement risks
- Warn if controller pods run on Karpenter-managed nodes
- AMI hygiene checks (e.g., overly broad selectors)
- NodePool capacity narrowness detection
- Spot-only reliability warnings
- Taints and toleration mismatch detection
- NodePool ↔ EC2NodeClass consistency validation

---

### Tooling & integrations

- GitHub Actions integration for validating Karpenter YAML in PRs
- CLI interface for local and CI usage
- Plugin-style rule registration for easier extensibility
- Version-aware validation for multiple Karpenter releases

---

## Milestones & Versioning

| Version | Scope |
|------|------|
| v0.4 | NodePool rules, basic UI, AI explanations, patch suggestions |
| v0.5 | EC2NodeClass validation and UI surface |
| v0.6 | Scoring system and comparison dashboard |
| v0.7 | Report export and bundled patch generation |
| v0.8 | Reliability and operational best-practice rules |
| v1.0 | Stable OSS release with documented extension points |

---

## Non-Goals

To keep the project focused and maintainable, the following are explicitly **out of scope**:

- Cluster mutation or automatic writes
- Continuous background monitoring
- Billing, user accounts, or SaaS infrastructure
- Vendor lock-in or managed services
- Replacing human review in production environments
