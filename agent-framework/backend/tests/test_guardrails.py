import pytest
import time

from agent_framework.guardrails.policy_enforcer import PolicyEnforcer
from agent_framework.guardrails.content_filter import filter_content
from agent_framework.guardrails.base import BudgetEnforcer, RateLimiter
from agent_framework.guardrails.orchestrator import GuardrailOrchestrator


def test_policy_enforcer_blocks_deletion():
    p = PolicyEnforcer()
    allowed, policy = p.check("delete", "user1")
    assert not allowed


def test_content_filter_detects_pii():
    text = "Contact me at alice@example.com"
    safe, violations = filter_content(text)
    assert not safe
    assert any(v["type"] == "pii_email" for v in violations)


def test_budget_enforcer_blocks_expensive():
    b = BudgetEnforcer()
    b.set_budget("u1", 1.0)
    ok = b.check_budget("u1", 2.0)
    assert not ok


def test_rate_limiter_blocks_excessive():
    r = RateLimiter(max_per_minute=2)
    assert r.check_rate_limit("u1")
    assert r.check_rate_limit("u1")
    assert not r.check_rate_limit("u1")


def test_orchestrator_runs_all_checks():
    g = GuardrailOrchestrator()
    # set low budget
    g.budget.set_budget("agent1", 0.0)
    state = {"agent_id": "agent1"}
    action = {"tool": "delete", "params": {"q": "secret@ex.com"}}
    allowed, failed = g.check_all(state, action, cost=10.0)
    assert not allowed
    assert len(failed) >= 1
