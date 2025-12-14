# Karpenter AI Agent

![CI](https://github.com/matt-e-builds/karpenter-ai-agent/actions/workflows/ci.yml/badge.svg)

## Overview
Karpenter AI Agent is an open-source analysis and optimization tool for Kubernetes clusters that use Karpenter on AWS. It ingests Provisioner, NodePool, and EC2NodeClass manifests, applies deterministic static rules to detect correctness gaps and efficiency issues, and (optionally) produces an AI-generated natural-language summary strictly based on the rule results. The agent exposes a FastAPI web interface so platform teams can upload YAML, review findings, and download remediation snippets in one place.

All rule logic is deterministic and testable; AI output is an optional enhancement. The project is released under the MIT License.

## Features
- **Robust YAML parsing** – Handles multi-document uploads, Provisioners, NodePools, and EC2NodeClasses with defensive parsing for edge cases.
- **Deterministic rule engine** – Checks Spot adoption, consolidation configuration, Graviton coverage, `ttlSecondsAfterEmpty`, and EC2NodeClass IAM/subnet/security-group settings.
- **Actionable issue output** – Severity-tagged findings with human-readable recommendations, health score summary, and ready-to-apply YAML patch snippets (copy-to-clipboard in the UI).
- **Optional AI summary** – Groq-backed natural-language synopsis of the deterministic findings; never used for core logic.
- **Modern web UI** – FastAPI + Jinja templates with dark theme, structured cards, and health score visualization.
- **Test coverage + CI** – Pytest fixtures for rules/edge cases plus GitHub Actions that run pytest and pip-audit on every push and pull request.

## Screenshots

### Upload form
![Upload form](screenshots/upload.png)

### Summary view
![Summary view](screenshots/summary.png)

### Issues and patches
![Issues and patches](screenshots/issues-and-patches.png)

### AI analysis
![AI analysis](screenshots/ai-analysis.png)

## Installation
```bash
git clone https://github.com/matt-e-builds/karpenter-ai-agent.git
cd karpenter-ai-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optional: enable AI summaries by providing a Groq key.
```bash
export GROQ_API_KEY="your_groq_api_key_here"
```
If the variable is unset, the application still runs; AI summaries are simply disabled.

## Running the App
```bash
python main.py
```
Then open http://127.0.0.1:5000 and upload one or more Karpenter YAML files.

## Project Structure
```text
karpenter-ai-agent/
├── main.py             # FastAPI entrypoint
├── parser.py           # YAML parsing helpers
├── rules.py            # Deterministic rule engine + scoring
├── models.py           # Dataclasses for configs and issues
├── llm_client.py       # Optional Groq integration for summaries
├── templates/          # Jinja2 templates for form/results
├── static/             # Static assets (CSS/JS)
├── tests/
│   ├── fixtures/       # Sample Provisioner / NodePool / NodeClass YAML
│   └── test_rules.py   # Rule + summary tests
├── requirements.txt
├── pyproject.toml
└── README.md
```

## License
MIT License. See [LICENSE](./LICENSE) for details.

## Maintainer
Maintained by **Matt E.**  
GitHub: https://github.com/matt-e-builds
