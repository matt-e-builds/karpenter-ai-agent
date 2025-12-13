# Contributing to Karpenter AI Agent

Thanks for your interest in contributing!

This project aims to stay:
- Deterministic and testable for core logic (rules + scoring)
- Helpful and safe for operators (clear findings + remediation snippets)
- Simple to run locally (FastAPI app + minimal dependencies)

## Quick start (local dev)

1) Fork the repo and clone your fork:
   - git clone https://github.com/<your-username>/karpenter-ai-agent.git
   - cd karpenter-ai-agent

2) Create and activate a virtualenv:
   - python3 -m venv .venv
   - source .venv/bin/activate

3) Install dependencies:
   - pip install -r requirements.txt
   - pip install pytest

4) Run tests:
   - pytest

5) Run the app:
   - python main.py
   - Open http://127.0.0.1:5000

## What to contribute

Good first contributions:
- New deterministic rules with tests + fixtures
- Parser hardening (edge cases, multi-doc YAML, type quirks)
- Better patch snippet generation (safe, minimal, clearly labeled)
- UI improvements (readability, UX, accessibility)
- Documentation improvements (README/ROADMAP clarifications)

## Rules for changes (important)

1) Determinism for core logic
- The rules engine and scoring must remain deterministic.
- AI output is optional and must never drive core findings.

2) Tests required for behavior changes
- Any new rule or scoring change must include:
  - At least one fixture update or new fixture
  - A test in tests/test_rules.py that asserts expected issues and summary counts

3) Do not invent issues in AI summaries
- If you touch the prompt or LLM wiring:
  - The AI summary must be grounded in the issues array
  - It must use exact counts from summary (no mismatches)

4) Patch snippet safety
- Patches are suggestions and should be minimal.
- Prefer patches that:
  - Add only the missing field(s)
  - Avoid changing unrelated configuration
  - Clearly indicate the target resource name in a comment

## Repo structure

- main.py: FastAPI entrypoint
- parser.py: YAML parsing for Provisioner/NodePool/EC2NodeClass
- rules.py: Deterministic rule engine + scoring
- llm_client.py: Optional AI summary generation
- templates/: Jinja templates
- static/: CSS/JS
- tests/: fixtures + pytest tests

## Style guidelines

Python:
- Prefer clear, explicit code over cleverness.
- Keep functions small and testable.
- Use type hints where it improves clarity.

Docs:
- Keep instructions copy/paste friendly.
- Avoid marketing fluff; be specific and technical.

## Submitting changes

1) Create a branch:
   - git checkout -b feat/<short-name>
   - or: git checkout -b fix/<short-name>

2) Make changes and run:
   - pytest

3) Commit with a clear message:
   - feat: add rule for missing subnet selectors
   - fix: handle nodeclass name as dict in nodepool
   - ui: improve ai analysis styling

4) Push your branch and open a PR.

## PR checklist

- [ ] Tests pass locally (pytest)
- [ ] New/changed behavior is covered by tests
- [ ] Fixtures updated or added when needed
- [ ] No breaking changes to existing outputs unless documented
- [ ] README/ROADMAP updated if user-facing behavior changed

## Reporting bugs / requesting features

Open a GitHub issue with:
- What you expected vs what happened
- The YAML you tested (or a reduced repro)
- Screenshots (for UI issues)
- Any error logs/tracebacks
