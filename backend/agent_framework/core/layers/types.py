"""Compatibility shim for tests expecting layer-local types module.

This module forwards to the canonical `agent_framework.core.types`.
"""

from agent_framework.core.types import TaskDef, ExecutionMetrics, AgentInput, AgentState

__all__ = [
    "TaskDef",
    "ExecutionMetrics",
    "AgentInput",
    "AgentState",
]
