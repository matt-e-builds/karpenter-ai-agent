from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List
from io import StringIO
import os
import sys

SRC_PATH = os.path.join(os.path.dirname(__file__), "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)


from models import Issue, ProvisionerConfig, EC2NodeClassConfig
from parser import parse_provisioner_yaml
from rules import generate_summary
from llm_client import generate_report
from karpenter_ai_agent.agents import CoordinatorAgent, ParserAgent
from karpenter_ai_agent.agents._adapters import to_legacy_provisioner, to_legacy_nodeclass
from karpenter_ai_agent.models import AnalysisInput
from karpenter_ai_agent.rag.explain import attach_issue_explanations

app = FastAPI(title="Karpenter Optimization Agent")

# Holds the issues from the last successful analysis so we can export patches
LAST_ISSUES: List[Issue] = []

os.makedirs("templates", exist_ok=True)
os.makedirs("static", exist_ok=True)

templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})


@app.post("/analyze", response_class=HTMLResponse)
async def analyze(
    request: Request,
    region: str = Form(...),
    files: List[UploadFile] = File(...),
):
    all_provisioners: List[ProvisionerConfig] = []
    all_nodeclasses: List[EC2NodeClassConfig] = []
    parse_errors: List[str] = []
    yaml_chunks: List[str] = []

    # Parse uploaded YAML files
    for uploaded_file in files:
        if not uploaded_file.filename:
            continue

        try:
            content = await uploaded_file.read()
            yaml_content = content.decode("utf-8")
            yaml_chunks.append(yaml_content)

            # New parser return type: (provisioners, ec2_nodeclasses)
            provisioners, nodeclasses = parse_provisioner_yaml(yaml_content)
            all_provisioners.extend(provisioners)
            all_nodeclasses.extend(nodeclasses)
        except Exception as e:
            parse_errors.append(f"Error parsing {uploaded_file.filename}: {str(e)}")

    # No valid Karpenter resources
    if not all_provisioners and not all_nodeclasses:
        error_message = (
            "No Karpenter Provisioner, NodePool, or EC2NodeClass resources found "
            "in the uploaded files."
        )
        if parse_errors:
            error_message = (
                "Failed to parse any valid Karpenter resources from the uploaded files."
            )
        return templates.TemplateResponse(
            "results.html",
            {
                "request": request,
                "error": error_message,
                "parse_errors": parse_errors,
                "region": region,
            },
        )

    # Run CoordinatorAgent on combined YAML (deterministic graph)
    combined_yaml = "\n---\n".join(yaml_chunks)
    coordinator = CoordinatorAgent()
    report = coordinator.run(
        AnalysisInput(
            yaml_text=combined_yaml,
            region=region,
        )
    )

    # Convert canonical config for UI details
    parser_agent = ParserAgent()
    parser_output = parser_agent.run(AnalysisInput(yaml_text=combined_yaml))
    if parser_output.config:
        all_provisioners = [to_legacy_provisioner(p) for p in parser_output.config.provisioners]
        all_nodeclasses = [to_legacy_nodeclass(nc) for nc in parser_output.config.ec2_nodeclasses]

    # Convert new issues to legacy Issue objects for templates
    issues = [
        Issue(
            severity=i.severity,
            category=i.category,
            message=i.message,
            recommendation=i.recommendation,
            provisioner_name=i.resource_name,
            resource_kind=i.resource_kind,
            resource_name=i.resource_name,
            patch_snippet=i.patch_snippet,
            field=(i.metadata.get("field") if isinstance(i.metadata, dict) else None),
        )
        for i in report.issues
    ]

    attach_issue_explanations(issues)

    # Store for download endpoint
    global LAST_ISSUES
    LAST_ISSUES = issues

    summary = {
        "issues_by_severity": report.issues_by_severity,
        "optimization_status": report.optimizer_flags,
        "health_score": report.health_score,
        "health_score_max": 100,
        "ec2_nodeclass_count": len(all_nodeclasses),
    }

    # AI analysis via Groq
    ai_analysis = generate_report(region, summary, issues)

    return templates.TemplateResponse(
        "results.html",
        {
            "request": request,
            "region": region,
            "provisioners": all_provisioners,
            "ec2_nodeclasses": all_nodeclasses,
            "issues": issues,
            "summary": summary,
            "ai_analysis": ai_analysis,
            "parse_errors": parse_errors,
        },
    )


@app.get("/download-patches")
async def download_patches():
    """
    Combine all non-empty patch_snippet values from the last analysis
    into a single YAML document (separated by ---) and return as a download.
    """
    if not LAST_ISSUES:
        return HTMLResponse(
            "No analysis has been run yet, or there are no issues to export.",
            status_code=400,
        )

    patches = [issue.patch_snippet for issue in LAST_ISSUES if issue.patch_snippet]

    if not patches:
        return HTMLResponse(
            "No patch snippets are available for the current analysis.",
            status_code=400,
        )

    yaml_output = "\n---\n".join(patches)

    buffer = StringIO()
    buffer.write(yaml_output)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/x-yaml",
        headers={
            "Content-Disposition": 'attachment; filename="karpenter-patches.yaml"'
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)
