"""Memory Usage example (DOC-004).

Demonstrates Episodic and Semantic memory usage: storing and retrieving
entries, plus semantic retrieval with `SimpleEmbeddings`.

Run with:
    PYTHONPATH=.:backend .venv/bin/python3 examples/memory_usage_example.py

"""

import os
import sys
import json
import time
from datetime import datetime, timezone
from typing import Any

# Ensure backend package is importable when running directly
ROOT = os.path.dirname(os.path.dirname(__file__))
BACKEND = os.path.join(ROOT, "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

from agent_framework.memory.episodic import EpisodicMemory, Episode
from agent_framework.memory.semantic import SemanticMemory, SemanticRecord
from agent_framework.memory.retrieval import SimpleEmbeddings, SemanticRetrieval


def demo_episodic() -> Any:
    mem = EpisodicMemory()
    # store a few episodes
    for i in range(1, 4):
        ep = Episode(
            query=f"query {i}",
            reasoning=f"reasoning result {i}",
            tasks=[{"id": f"t{i}", "name": f"task {i}"}],
            outcome="success" if i % 2 == 1 else "partial",
            cost=0.0,
            tokens_used=10 * i,
            timestamp=datetime.now(timezone.utc),
        )
        mem.store(ep)

    # retrieve recent episodes
    recent = mem.retrieve("query")
    return [dict(query=e.query, reasoning=e.reasoning, outcome=e.outcome) for e in recent]


async def demo_semantic() -> Any:
    # semantic memory and simple retriever
    sem = SemanticMemory()
    # store some semantic records (topic/pattern)
    sem.store(SemanticRecord(text="How to boil an egg", embedding=[0.1] * 128, topic="cooking", success_rate=0.9))
    sem.store(SemanticRecord(text="Photosynthesis overview", embedding=[0.2] * 128, topic="biology", success_rate=0.95))

    # Use SemanticRetrieval with SimpleEmbeddings to store and retrieve entries
    retriever = SemanticRetrieval(embedding_model=SimpleEmbeddings(), backend=None)

    # store a few memory entries using retriever.store_memory
    await retriever.store_memory({"content": "I boiled an egg today", "agent_id": "demo"})
    await retriever.store_memory({"content": "I studied photosynthesis", "agent_id": "demo"})

    # retrieve similar to 'boil an egg'
    similar = await retriever.retrieve_similar("boil an egg", agent_id="demo", top_k=5)
    return similar


def main() -> None:
    print("Running Memory Usage example...\n")

    print("Episodic memory demo:")
    try:
        eps = demo_episodic()
        print(json.dumps(eps, indent=2, default=str))
    except Exception as exc:
        print("Episodic demo failed:", exc)

    print("\nSemantic memory demo (async):")
    try:
        import asyncio

        sim = asyncio.run(demo_semantic())
        print(json.dumps(sim, indent=2, default=str))
    except Exception as exc:
        print("Semantic demo failed:", exc)


if __name__ == "__main__":
    main()
