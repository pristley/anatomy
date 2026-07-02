"""Core type definitions for agents (Pydantic models).

These models use Pydantic v2-style validators.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class TaskDef(BaseModel):
    id: str
    name: str
    dependencies: List[str] = Field(default_factory=list)
    action_type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    status: str = "pending"


class ExecutionMetrics(BaseModel):
    tokens_used: int = 0
    cost: float = 0.0
    latency_ms: int = 0

    @field_validator("cost")
    @classmethod
    def _check_cost(cls, v: float) -> float:
        if v is None:
            return 0.0
        if v < 0:
            raise ValueError("cost must be >= 0")
        return v


class AgentInput(BaseModel):
    query: str
    user_id: str
    context: Optional[Dict[str, Any]] = None
    priority: int = 0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("timestamp")
    @classmethod
    def _ensure_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v


class AgentState(BaseModel):
    agent_id: str
    goal: Optional[str] = None
    active_tasks: List[TaskDef] = Field(default_factory=list)
    completed_tasks: List[TaskDef] = Field(default_factory=list)
    status: str = "idle"
    memory_refs: List[str] = Field(default_factory=list)


__all__ = [
    "TaskDef",
    "ExecutionMetrics",
    "AgentInput",
    "AgentState",
]
