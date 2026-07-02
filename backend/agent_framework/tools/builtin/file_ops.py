"""Basic file operations tool (dev only)."""
from __future__ import annotations

import os
from typing import Any


def read_file(path: str) -> str:
    # simple safety: prevent absolute paths and traversal
    if os.path.isabs(path) or ".." in path:
        raise ValueError("unsafe path")
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def write_file(path: str, content: str) -> bool:
    if os.path.isabs(path) or ".." in path:
        raise ValueError("unsafe path")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return True


__all__ = ["read_file", "write_file"]
