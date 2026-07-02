from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, root_validator, validator
from datetime import datetime


class ExecutionMetrics(BaseModel):
    tokens_used: int = 0
    cost: float = 0.0
    latency_ms: int = 0
    layer_name: Optional[str] = None


class LayerResult(BaseModel):
    success: bool
    output: Optional[Any]
    metrics: Optional[ExecutionMetrics]
    error: Optional[str]


class TaskDef(BaseModel):
    id: str
    name: str
    dependencies: List[str] = Field(default_factory=list)
    action_type: str = "infer"
    parameters: Dict[str, Any] = Field(default_factory=dict)
    status: str = "pending"


class AgentInput(BaseModel):
    query: str
    user_id: Optional[str]
    context: Dict[str, Any] = Field(default_factory=dict)
    priority: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @validator("query")
    def query_not_empty(cls, v: str):
        if not v or not v.strip():
            raise ValueError("query must not be empty")
        return v


class AgentState(BaseModel):
    agent_id: Optional[str]
    goal: Optional[str]
    active_tasks: List[TaskDef] = Field(default_factory=list)
    completed_tasks: List[TaskDef] = Field(default_factory=list)
    status: str = "running"
    memory_refs: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @root_validator(skip_on_failure=True)
    def timestamps_present(cls, values):
        if "created_at" not in values or values["created_at"] is None:
            values["created_at"] = datetime.utcnow()
        values["updated_at"] = datetime.utcnow()
        return values
