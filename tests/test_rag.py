from karpenter_ai_agent.rag.loader import DEFAULT_DOCS_PATH, load_markdown_documents
from karpenter_ai_agent.rag.models import RAGQuery
from karpenter_ai_agent.rag.tool import retrieve_context


def test_rag_loader_reads_local_karpenter_docs():
    documents = load_markdown_documents(DEFAULT_DOCS_PATH)
    assert documents
    assert any(doc.source_url.startswith("https://") for doc in documents)


def test_retrieve_context_returns_grounded_results():
    result = retrieve_context(RAGQuery(query="nodeClassRef nodepool", top_k=3))
    assert result.contexts
    assert all(context.source_url.startswith("https://") for context in result.contexts)
