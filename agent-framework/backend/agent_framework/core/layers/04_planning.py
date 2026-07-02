from typing import List
from ..types import TaskDef


class PlanningDecomposition:
    def decompose(self, reasoning_text: str, max_tasks: int = 5) -> List[TaskDef]:
        if not reasoning_text:
            return []

        # naive split: look for lines starting with 'Step' or split by newlines
        parts = [p.strip() for p in reasoning_text.splitlines() if p.strip()]
        tasks = []
        idx = 1
        for p in parts:
            if len(tasks) >= max_tasks:
                break
            name = p
            task = TaskDef(id=f"task_{idx}", name=name[:80], dependencies=[], action_type="infer", parameters={})
            tasks.append(task)
            idx += 1
        return tasks

    def topological_sort(self, tasks: List[TaskDef]) -> List[TaskDef]:
        # Phase 1: tasks have no dependencies, return as-is
        return tasks
