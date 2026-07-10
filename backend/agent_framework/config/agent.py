"""Agent configuration.

This module defines the `AgentConfig` dataclass which centralizes configuration
for Agent instances. All fields are documented on the dataclass.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class AgentConfig:
    """Configuration for an Agent instance.

    Attributes:
        model_name: LLM model to use
        max_iterations: Maximum task loop iterations
        max_tokens: Max tokens per request
        temperature: LLM temperature (0.0-1.0)
        timeout_ms: Execution timeout in milliseconds
        max_cost_usd: Maximum cost per query
        max_tokens_budget: Daily token budget
        enable_memory: Enable memory systems
        enable_guardrails: Enable safety guardrails
        enable_observability: Enable logging/metrics
        allow_subagents: Allow subagent spawning
        max_subagents: Maximum concurrent subagents
        extra: Custom options dict
    """
    model_name: str = "claude-3-5-sonnet-20241022"
    max_iterations: int = 10
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout_ms: int = 30000

    # Budget constraints
    max_cost_usd: float = 1.0
    max_tokens_budget: int = 100000

    # Behavior flags
    enable_memory: bool = True
    enable_guardrails: bool = True
    enable_observability: bool = True

    # Multi-agent
    allow_subagents: bool = True
    max_subagents: int = 10

    # Custom options
    extra: Dict[str, Any] = field(default_factory=dict)
