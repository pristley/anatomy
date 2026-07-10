"""Mock database query tool."""

from __future__ import annotations

from typing import List, Dict


def query_db(sql: str, db_type: str = "sqlite") -> List[Dict]:
    # naive mocked responses based on SQL content
    sql_lower = sql.strip().lower()
    if "select" in sql_lower:
        return [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
    return []


__all__ = ["query_db"]
