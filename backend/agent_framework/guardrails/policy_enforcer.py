"""Policy enforcer guardrail."""

from __future__ import annotations

from typing import Dict, Any, Tuple, List

DEFAULT_POLICIES = [
    {
        "name": "no_data_deletion",
        "action_types": ["delete", "drop", "remove"],
        "allowed": False,
    },
    {
        "name": "no_system_access",
        "action_types": ["exec", "shell", "system"],
        "allowed": False,
    },
    {
        "name": "no_external_calls",
        "action_types": ["external_call", "api_call", "http_request"],
        "allowed": False,
    },
]


class PolicyEnforcer:
    def __init__(self, policies: List[Dict[str, Any]] | None = None) -> None:
        self.policies = policies or DEFAULT_POLICIES

    def load_from_config(self, cfg: List[Dict[str, Any]]) -> None:
        self.policies = cfg

    def check(
        self, action_type: str, user_id: str
    ) -> Tuple[bool, Dict[str, Any] | None]:
        at = (action_type or "").lower()
        for p in self.policies:
            for pattern in p.get("action_types", []):
                if pattern in at:
                    return p.get("allowed", False), p
        return True, None


__all__ = ["PolicyEnforcer", "DEFAULT_POLICIES"]
