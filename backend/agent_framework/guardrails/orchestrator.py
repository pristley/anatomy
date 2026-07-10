"""Run all guardrails in sequence and aggregate results."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from agent_framework.guardrails.base import BudgetEnforcer, RateLimiter
from agent_framework.guardrails.policy_enforcer import PolicyEnforcer
from agent_framework.guardrails.content_filter import filter_content
from agent_framework.observability import logger


class GuardrailOrchestrator:
    def __init__(self) -> None:
        self.policy = PolicyEnforcer()
        self.budget = BudgetEnforcer()
        self.rate = RateLimiter()

    def check_all(
        self, state: Dict[str, Any], action: Dict[str, Any], cost: float = 0.0
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        failed: List[Dict[str, Any]] = []

        action_type = (action.get("tool") or action.get("action_type") or "").lower()

        # policy check
        allowed, policy = self.policy.check(action_type, state.get("agent_id"))
        logger.info(f"guardrail: policy check {action_type} -> {allowed} {policy}")
        if not allowed:
            failed.append({"guardrail": "policy", "reason": policy})

        # content check: inspect params that are strings
        params = action.get("params") or {}
        for k, v in params.items():
            if isinstance(v, str):
                safe, violations = filter_content(v)
                logger.info(
                    f"guardrail: content check field={k} safe={safe} violations={violations}"
                )
                if not safe:
                    failed.append(
                        {"guardrail": "content", "field": k, "violations": violations}
                    )

        # budget
        if not self.budget.check_budget(state.get("agent_id"), cost):
            logger.info(
                f"guardrail: budget exceeded for {state.get('agent_id')} cost={cost}"
            )
            failed.append({"guardrail": "budget", "reason": "insufficient funds"})

        # rate limiter
        if not self.rate.check_rate_limit(state.get("agent_id")):
            logger.info(f"guardrail: rate limit hit for {state.get('agent_id')}")
            failed.append({"guardrail": "rate", "reason": "rate limit exceeded"})

        allowed_overall = len(failed) == 0
        return allowed_overall, failed


__all__ = ["GuardrailOrchestrator"]
