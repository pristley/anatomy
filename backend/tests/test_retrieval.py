import asyncio
import pytest

from agent_framework.memory.retrieval import (
    _cosine,
    SimpleEmbeddings,
    Retriever,
    SemanticRetrieval,
    OpenAIEmbeddings,
)


def test_cosine_basic():
    assert _cosine([1, 0], [1, 0]) == pytest.approx(1.0)
    assert _cosine([], [1, 2]) == 0.0
    assert _cosine([0, 0], [0, 0]) == 0.0


def test_simple_embeddings():
    e = SimpleEmbeddings(dim=8)
    v = e.embed("hello")
    assert isinstance(v, list)
    assert len(v) == 8


def test_retriever_scores():
    emb = SimpleEmbeddings(dim=4)
    docs = [
        {"input": "I like apples", "embedding": emb.embed("apples")},
        {"input": "I like oranges", "embedding": emb.embed("oranges")},
        {"input": "no embedding here"},
    ]
    r = Retriever(emb)
    res = r.retrieve("apples", docs, top_k=3)
    assert any("similarity_score" in d for d in res)


@pytest.mark.asyncio
async def test_semantic_retrieval_local_store():
    emb = SimpleEmbeddings(dim=8)
    sr = SemanticRetrieval(embedding_model=emb, backend=None, similarity_threshold=0.0)
    e1 = await sr.store_memory({"content": "I boiled an egg", "agent_id": "demo"})
    e2 = await sr.store_memory({"content": "I watched TV", "agent_id": "demo"})
    assert "id" in e1 and "embedding" in e1

    res = await sr.retrieve_similar("boil", agent_id="demo", top_k=5)
    assert isinstance(res, list)

    recent = await sr.retrieve_recent("demo", limit=5)
    assert isinstance(recent, list)

    batch = await sr.batch_retrieve(["boil", "watch"], agent_id="demo", top_k=2)
    assert isinstance(batch, dict) and 0 in batch


def test_openai_embeddings_no_key():
    o = OpenAIEmbeddings(api_key=None)
    with pytest.raises(RuntimeError):
        asyncio.get_event_loop().run_until_complete(o.aembed("x"))
