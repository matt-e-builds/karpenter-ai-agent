import json as json_lib

from llm_client import generate_issue_explanation
from models import Issue
from karpenter_ai_agent.rag.models import RetrievedChunk


def test_issue_prompt_includes_retrieved_chunks(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key")

    issue = Issue(
        severity="high",
        category="EC2NodeClass",
        message="Missing instanceProfile",
        recommendation="Set an instanceProfile",
        provisioner_name="demo",
        resource_kind="EC2NodeClass",
        resource_name="demo",
    )
    chunks = [
        RetrievedChunk(
            chunk_id="doc-0",
            doc_id="ec2nodeclass-iam",
            title="EC2NodeClass instanceProfile and IAM role",
            source_url="https://karpenter.sh/docs/concepts/nodeclasses/",
            text="instanceProfile or role is required for node permissions.",
            score=0.9,
        )
    ]

    def fake_post(url, json=None, headers=None, timeout=None):
        assert json is not None
        content = json["messages"][1]["content"]
        payload = json_lib.loads(content)
        assert payload["retrieved_docs"][0]["text"] == chunks[0].text
        class FakeResponse:
            status_code = 200
            def json(self):
                return {
                    "choices": [
                        {
                            "message": {
                                "content": "WHY: This matters.\nCHANGE:\n- Fix it.\nDOCS:\n- https://karpenter.sh/docs/concepts/nodeclasses/"
                            }
                        }
                    ]
                }
        return FakeResponse()

    monkeypatch.setattr("llm_client.requests.post", fake_post)

    explanation = generate_issue_explanation(issue, chunks)
    assert explanation is not None
    assert explanation.why_matters
    assert explanation.what_to_change
