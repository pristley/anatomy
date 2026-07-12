"""Additional tests for memory/retrieval utilities to improve coverage."""

import importlib.util
import sys
from pathlib import Path
import pytest


def _load_mod():
    backend_root = Path(__file__).resolve().parents[1]
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))
    path = backend_root / "agent_framework" / "memory" / "retrieval.py"
    spec = importlib.util.spec_from_file_location("retrieval", str(path))
    mod = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_simple_embeddings_and_cosine():
    mod = _load_mod()
    se = mod.SimpleEmbeddings(dim=8)
    v = se.embed("hello")
    assert isinstance(v, list) and len(v) == 8
    # cosine with identical vectors ~1
    assert mod._cosine(v, v) == pytest.approx(1.0)


def test_retriever_with_and_without_embedding():
    mod = _load_mod()
    emb = mod.SimpleEmbeddings(dim=4)
    docs = [
        {"input": "I like apples", "embedding": emb.embed("apples")},
        {"input": "No embed here"},
    ]
    r = mod.Retriever(emb)
    res = r.retrieve("apples", docs, top_k=2)
    assert any("similarity_score" in d for d in res)


@pytest.mark.asyncio
async def test_semantic_retrieval_local_store_and_filters():
    mod = _load_mod()
    emb = mod.SimpleEmbeddings(dim=8)
    sr = mod.SemanticRetrieval(
        embedding_model=emb, backend=None, similarity_threshold=0.0
    )

    _e1 = await sr.store_memory({"content": "I boiled an egg", "agent_id": "demo"})
    _e2 = await sr.store_memory(
        {"content": "I watched TV", "agent_id": "demo", "metadata": {"tags": ["media"]}}
    )

    recent = await sr.retrieve_recent("demo", limit=5)
    assert isinstance(recent, list) and len(recent) >= 2

    by_meta = await sr.retrieve_by_metadata("demo", {"tags": ["media"]}, limit=5)
    assert isinstance(by_meta, list)

    batch = await sr.batch_retrieve(["boil", "watch"], agent_id="demo", top_k=2)
    assert isinstance(batch, dict) and 0 in batch
