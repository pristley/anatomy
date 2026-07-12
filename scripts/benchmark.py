"""Performance benchmark for layers and full pipeline.

This script is resilient to being run from `backend/` (use: `python ../scripts/benchmark.py`).
"""

from __future__ import annotations

import asyncio
import time
import sys
from pathlib import Path
from typing import List
from importlib.util import spec_from_file_location, module_from_spec

# Ensure backend package is importable
HERE = Path(__file__).resolve().parent
REPO = HERE.parent
BACKEND = REPO / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def _load_layer(filename: str, attr: str):
    base = BACKEND / "agent_framework" / "core" / "layers"
    path = (base / filename).resolve()
    pkg = "agent_framework.core.layers"
    mod_name = f"{pkg}.{path.stem}"
    spec = spec_from_file_location(mod_name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module {filename}")
    mod = module_from_spec(spec)
    mod.__package__ = pkg
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return getattr(mod, attr)


async def benchmark_layer_1():
    InputLayer = _load_layer("01_input.py", "InputLayer")
    layer = InputLayer()
    queries = [
        "What is 2+2?",
        "How do I use Python?",
        "Tell me about machine learning",
    ]
    times: List[float] = []
    for q in queries:
        start = time.monotonic()
        _ = layer.process(q, "user1")
        elapsed = (time.monotonic() - start) * 1000
        times.append(elapsed)
    avg = sum(times) / len(times)
    print(f"Layer 1 (Input):       {avg:.2f}ms avg")
    return avg


async def benchmark_layer_2():
    UnderstandingLayer = _load_layer("02_understanding.py", "UnderstandingLayer")

    # create a dummy agent_input object with `query` attribute
    class Dummy:
        def __init__(self, query):
            self.query = query

    layer = UnderstandingLayer()
    inputs = [
        Dummy("What is Python?"),
        Dummy("How to code?"),
        Dummy("Tell me about AI"),
    ]
    times: List[float] = []
    for inp in inputs:
        start = time.monotonic()
        _ = layer.understand(inp)
        elapsed = (time.monotonic() - start) * 1000
        times.append(elapsed)
    avg = sum(times) / len(times)
    print(f"Layer 2 (Understanding): {avg:.2f}ms avg")
    return avg


async def benchmark_full_pipeline():
    # import Agent from core.agent
    from agent_framework.core.agent import Agent

    agent = Agent()
    queries = ["What is 2+2?", "How do I use Python?", "Tell me about machine learning"]
    times: List[float] = []
    for q in queries:
        start = time.monotonic()
        res = await agent._run_async(q, "user1")
        elapsed = (time.monotonic() - start) * 1000
        times.append(elapsed)
        print(
            f"  run -> success={res.get('success')} duration_ms={res.get('execution_time_ms')}"
        )
    avg = sum(times) / len(times)
    print(f"\nFull Pipeline:         {avg:.2f}ms avg")
    print(f"  Min: {min(times):.2f}ms")
    print(f"  Max: {max(times):.2f}ms")
    return avg


async def main():
    print("=" * 60)
    print("ANATOMY Framework Performance Benchmark")
    print("=" * 60)
    print()

    _l1 = await benchmark_layer_1()
    _l2 = await benchmark_layer_2()
    full = await benchmark_full_pipeline()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("Target simple query:   <500ms")
    print(f"Actual:                {full:.2f}ms")
    if full < 500:
        print("Status:                ✅ GOOD")
    elif full < 1000:
        print("Status:                🟡 ACCEPTABLE")
    else:
        print("Status:                🔴 NEEDS OPTIMIZATION")


if __name__ == "__main__":
    asyncio.run(main())
