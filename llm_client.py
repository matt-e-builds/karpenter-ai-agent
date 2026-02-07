import os
import re
import json
import requests
from dataclasses import asdict
from typing import Optional, List
from models import Issue, IssueExplanation
from karpenter_ai_agent.rag.models import RetrievedChunk
from karpenter_ai_agent.rag.prompts import EXPLANATION_SYSTEM_PROMPT, build_issue_prompt

SYSTEM_PROMPT = """You are an expert AWS cost optimization consultant specializing in Kubernetes and Karpenter.

You receive a JSON payload describing Karpenter Provisioner / NodePool / EC2NodeClass analysis (region, a summary object, and a list of issues). Your job is to write a short, human-readable report.

The JSON you receive has this shape:
{
  "region": "us-east-1",
  "summary": {
    "issues_by_severity": {"high": int, "medium": int, "low": int},
    "optimization_status": {
      "total_provisioners": int,
      "spot_enabled": int,
      "graviton_used": int,
      "consolidation_enabled": int
    },
    "health_score": int,
    "health_score_max": int,
    "ec2_nodeclass_count": int
  },
  "issues": [ ... ]   // list of issue objects with provisioner_name, severity, category, message, recommendation, etc.
}

HARD FORMATTING RULES (FOLLOW STRICTLY):
- Do NOT use Markdown headings (no '#', '##', '###').
- Do NOT use bold or italics markers (no '**', '*' or '_').
- Do NOT output fenced code blocks (no triple backticks at all).
- Do NOT output YAML, JSON, or other configuration snippets.
- Use only plain text paragraphs and simple bullet lists.
- For bullets, only use this style: '- ' at the start of the line.

STRICT CORRECTNESS RULES (VERY IMPORTANT):
- Every bullet in the High, Medium, Low, and Recommended actions sections MUST be grounded in the 'issues' array from the JSON input.
- Do NOT invent or restate issues that are not present in the input JSON.
- Do NOT generalize ttlSecondsAfterEmpty or other settings across provisioners unless an issue explicitly mentions that setting for those provisioners.
- If only some provisioners are affected by an issue, name exactly those provisioners (do not add more).
- You may aggregate multiple issue entries into a single bullet, but you MUST NOT change which provisioners or resources are affected.
- Avoid duplicate bullets that say the same thing. Each distinct problem should appear once, possibly mentioning multiple provisioners in one bullet.
- You MUST keep your counts consistent with the 'summary.issues_by_severity' object. If it says 6 high / 5 medium / 1 low, your prose must reflect that (and not 11 vs 12, etc.).
- Do NOT mention any monthly spend values or dollar amounts. The input does not contain a reliable cost estimate; focus only on configuration and relative cost impact.

STRUCTURE:
1) Start with 2–3 sentences giving an overall summary of the configuration and risk level. This summary must also be consistent with the counts and severities present in the 'summary.issues_by_severity' and 'summary.health_score'.

2) Then write the following section titles, in this exact order, each as plain text ending with a colon:

High severity issues:
Medium severity issues:
Low severity issues or observations:
Recommended actions:

3) Under each section title, use bullet points ("- ") to describe the relevant points.
   - Refer to provisioner, nodepool, or EC2NodeClass names where helpful.
   - If there are no items for a section, write a single bullet: "- None."

4) In "Recommended actions:", list ALL concrete actions implied by the issues (not just the top 3).
   - Group similar actions when possible (for example: enable Spot for multiple provisioners in one bullet).
   - Each recommended action must be directly justified by at least one issue from the 'issues' array.
   - Focus on actionable guidance: what to change and why (cost impact, resilience, efficiency, or correctness).

Keep the tone concise, practical, and focused on Karpenter and AWS cost / efficiency best practices.
Do not include any YAML or configuration examples in your response.
"""


def _sanitize_ai_text(text: str) -> str:
    """
    Post-process the model output to strip any code/YAML blocks or
    'Suggested YAML' sections that slip through.
    """
    if not text:
        return text

    # Remove fenced code blocks ``` ... ```
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)

    # Drop any lines that look like YAML/patch headings from the model
    cleaned_lines = []
    for line in text.splitlines():
        lower = line.strip().lower()
        if lower.startswith("suggested yaml"):
            continue
        if lower.startswith("yaml patch"):
            continue
        cleaned_lines.append(line)

    cleaned = "\n".join(cleaned_lines)

    # Collapse 3+ blank lines down to 2
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()


def _parse_issue_explanation(text: str) -> IssueExplanation:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    section = None
    why_lines: List[str] = []
    change_lines: List[str] = []

    for line in lines:
        upper = line.upper()
        if upper.startswith("WHY:"):
            section = "why"
            content = line[4:].strip()
            if content:
                why_lines.append(content)
            continue
        if upper.startswith("CHANGE:"):
            section = "change"
            continue
        if upper.startswith("DOCS:"):
            section = "docs"
            continue

        if section == "why":
            why_lines.append(line)
        elif section == "change" and line.startswith("-"):
            change_lines.append(line[1:].strip())

    why_matters = " ".join(why_lines).strip() if why_lines else None
    return IssueExplanation(why_matters=why_matters, what_to_change=change_lines)


def is_llm_enabled() -> bool:
    return bool(os.environ.get("GROQ_API_KEY"))


def call_free_model(region: str, summary: dict, issues: list) -> str:
    """
    Call the Groq API with Llama 3.3 model for AI analysis.

    Args:
        region: AWS region
        summary: Analysis summary dictionary (plain dict, not dataclass)
        issues: List of detected issues (list of plain dicts, not dataclass objects)

    Returns:
        The AI-generated analysis report as a string
    """
    api_key = os.environ.get("GROQ_API_KEY")

    if not api_key:
        return "GROQ_API_KEY not set"

    url = "https://api.groq.com/openai/v1/chat/completions"

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "region": region,
                        "summary": summary,
                        "issues": issues,
                    },
                    indent=2,
                ),
            },
        ],
        "max_tokens": 900,
        "temperature": 0.2,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)

        if response.status_code != 200:
            return f"HTTP {response.status_code}: {response.text[:200]}"

        raw = response.json()["choices"][0]["message"]["content"]
        return _sanitize_ai_text(raw)

    except requests.exceptions.Timeout:
        return "AI analysis timed out. Please try again."
    except requests.exceptions.RequestException as e:
        return f"Request failed: {str(e)}"
    except (KeyError, json.JSONDecodeError, IndexError) as e:
        return f"Response parsing failed: {str(e)}"


def generate_issue_explanation(
    issue: Issue,
    chunks: List[RetrievedChunk],
) -> Optional[IssueExplanation]:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None

    issue_payload = {
        "severity": issue.severity,
        "category": issue.category,
        "message": issue.message,
        "recommendation": issue.recommendation,
        "resource_kind": issue.resource_kind,
        "resource_name": issue.resource_name,
        "field": issue.field,
    }

    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": EXPLANATION_SYSTEM_PROMPT},
            {"role": "user", "content": build_issue_prompt(issue_payload, chunks)},
        ],
        "max_tokens": 300,
        "temperature": 0.2,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=45)
        if response.status_code != 200:
            return None
        raw = response.json()["choices"][0]["message"]["content"]
        cleaned = _sanitize_ai_text(raw)
        if not cleaned:
            return None
        return _parse_issue_explanation(cleaned)
    except requests.exceptions.RequestException:
        return None
    except (KeyError, json.JSONDecodeError, IndexError):
        return None


def generate_report(region: str, summary: dict, issues: List[Issue]) -> str:
    """
    Generates AI analysis report using call_free_model.
    Converts Issue dataclass objects to plain dicts before passing to call_free_model.

    Args:
        region: AWS region
        summary: Analysis summary dictionary
        issues: List of Issue dataclass objects

    Returns:
        The AI-generated analysis report as a string
    """
    summary_dict = summary
    issues_list = [asdict(i) for i in issues]
    return call_free_model(region, summary_dict, issues_list)
