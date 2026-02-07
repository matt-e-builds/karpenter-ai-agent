from karpenter_ai_agent.rag.store import KnowledgeStore, DEFAULT_KNOWLEDGE_PATH
from karpenter_ai_agent.rag.retrieve import retrieve


def test_retrieval_loads_knowledge_pack():
    store = KnowledgeStore.load(DEFAULT_KNOWLEDGE_PATH)
    assert store.chunks


def test_retrieval_finds_instance_profile_docs():
    store = KnowledgeStore.load(DEFAULT_KNOWLEDGE_PATH)
    result = retrieve("instanceProfile", top_k=3, store=store)
    assert any("instanceprofile" in chunk.title.lower() for chunk in result.chunks)


def test_retrieval_finds_subnet_selectors_docs():
    store = KnowledgeStore.load(DEFAULT_KNOWLEDGE_PATH)
    result = retrieve("subnet selectors", top_k=3, store=store)
    assert any("subnet" in chunk.text.lower() for chunk in result.chunks)
