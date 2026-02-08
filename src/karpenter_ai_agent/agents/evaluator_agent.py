from __future__ import annotations

import json
from typing import List

import requests

from karpenter_ai_agent.models import AnalysisReport, EvaluationResult
from llm_client import is_llm_enabled

EVALUATOR_SYSTEM_PROMPT = """You are a strict evaluator of explanation quality.

You are given deterministic findings and their explanations with citations.
You must ONLY evaluate grounding, completeness, and clarity of the explanations.
Do NOT create, modify, or suppress findings. Do NOT change severities.

Output format:
- <issue> for any problems found
- None. if everything looks grounded and complete
"""


def _basic_checks(report: AnalysisReport) -> List[str]:
    notes: List[str] = []
    for issue in report.issues:
        explanation = issue.explanation
        if explanation is None:
            continue
        if not explanation.docs:
            notes.append(f"{issue.rule_id}: missing citations")
        if not explanation.why_matters:
            notes.append(f"{issue.rule_id}: missing why this matters")
    return notes


def _call_evaluator_model(payload: dict) -> List[str] | None:
    if not is_llm_enabled():
        return None

    import os

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None

    url = "https://api.groq.com/openai/v1/chat/completions"
    request_payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": EVALUATOR_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(payload, indent=2)},
        ],
        "max_tokens": 300,
        "temperature": 0.1,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, json=request_payload, headers=headers, timeout=45)
        if response.status_code != 200:
            return None
        raw = response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException:
        return None
    except (KeyError, IndexError, json.JSONDecodeError):
        return None

    notes: List[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("- "):
            note = line[2:].strip()
            if note and note.lower() != "none.":
                notes.append(note)
    return notes


class EvaluatorAgent:
    name = "evaluator"

    def run(
        self,
        report: AnalysisReport,
        *,
        use_llm: bool = False,
    ) -> EvaluationResult:
        notes = _basic_checks(report)

        if use_llm:
            payload = {
                "issues": [
                    {
                        "rule_id": issue.rule_id,
                        "severity": issue.severity,
                        "message": issue.message,
                        "recommendation": issue.recommendation,
                        "explanation": (
                            None
                            if issue.explanation is None
                            else issue.explanation.model_dump()
                        ),
                    }
                    for issue in report.issues
                ]
            }
            llm_notes = _call_evaluator_model(payload)
            if llm_notes:
                notes.extend(llm_notes)

        return EvaluationResult(notes=notes)
