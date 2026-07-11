"""Layer 4: Planning & decomposition."""

from __future__ import annotations

from typing import List, Dict

from ..types import TaskDef

# Simple in-memory cache for decompose results to speed up repeated calls
_decompose_cache: Dict[str, List[TaskDef]] = {}


class PlanningDecomposition:
    @staticmethod
    def decompose(reasoning_text: str, max_tasks: int = 5) -> List[TaskDef]:
        """Extract simple step-based tasks from the reasoning text.

        Looks for occurrences like 'Step 1:' or lines starting with 'Step'.
        """
        if not reasoning_text:
            return []

        # check cache
        try:
            key = str(hash(reasoning_text))
            cached = _decompose_cache.get(key)
            if cached is not None:
                return cached
        except Exception:
            key = None

        lines = [ln.strip() for ln in reasoning_text.splitlines() if ln.strip()]
        tasks: List[TaskDef] = []
        for ln in lines:
            if ln.lower().startswith("step") or ln.lower().startswith("- step"):
                # use the whole line as name
                tid = f"task_{len(tasks) + 1}"
                name = ln
                tasks.append(
                    TaskDef(
                        id=tid,
                        name=name,
                        dependencies=[],
                        action_type="tool",
                        parameters={},
                        status="pending",
                    )
                )
            if len(tasks) >= max_tasks:
                break

        # fallback: split by sentences if no explicit steps
        if not tasks:
            parts = [p.strip() for p in reasoning_text.split(".") if p.strip()]
            for p in parts[:max_tasks]:
                tid = f"task_{len(tasks) + 1}"
                tasks.append(
                    TaskDef(
                        id=tid,
                        name=p[:80],
                        dependencies=[],
                        action_type="tool",
                        parameters={},
                        status="pending",
                    )
                )

        # store in cache if key available
        if key is not None:
            try:
                _decompose_cache[key] = tasks
            except Exception:
                pass
        return tasks


def topological_sort(tasks: List[TaskDef]) -> List[TaskDef]:
    """Simple topological sort by dependencies using Kahn's algorithm.

    Tasks with missing dependencies are treated as having no deps.
    """
    id_map = {t.id: t for t in tasks}
    indeg = {t.id: 0 for t in tasks}
    adj: Dict[str, List[str]] = {t.id: [] for t in tasks}

    for t in tasks:
        for d in t.dependencies:
            if d in id_map:
                indeg[t.id] += 1
                adj[d].append(t.id)

    queue = [tid for tid, deg in indeg.items() if deg == 0]
    order: List[TaskDef] = []
    while queue:
        nid = queue.pop(0)
        order.append(id_map[nid])
        for m in adj.get(nid, []):
            indeg[m] -= 1
            if indeg[m] == 0:
                queue.append(m)

    # if cycle detected (not all tasks in order), append remaining
    remaining = [t for t in tasks if t.id not in {x.id for x in order}]
    return order + remaining


__all__ = ["PlanningDecomposition", "topological_sort"]
