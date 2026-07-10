"""Layer 10: Observability & structured logging."""

from __future__ import annotations

import json
from contextlib import ContextDecorator
from datetime import datetime
from typing import Any


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


class Logger:
    @staticmethod
    def _format(
        layer: str, status: str, data: Any | None = None, metrics: dict | None = None
    ) -> dict:
        payload = {
            "timestamp": _now_iso(),
            "layer": layer,
            "status": status,
            "input_size": None,
            "output_size": None,
            "cost": None,
        }
        if data is not None:
            try:
                s = str(data)
                payload["input_size"] = len(s)
            except Exception:
                payload["input_size"] = None

        if metrics is not None:
            payload.update(metrics)

        return payload

    @staticmethod
    def log_layer_start(layer_name: str, data: Any | None = None) -> None:
        print(json.dumps(Logger._format(layer_name, "start", data)))

    @staticmethod
    def log_layer_end(
        layer_name: str, data: Any | None = None, metrics: dict | None = None
    ) -> None:
        print(json.dumps(Logger._format(layer_name, "end", data, metrics)))


class LogContext(ContextDecorator):
    def __init__(self, layer_name: str, data: Any | None = None) -> None:
        self.layer_name = layer_name
        self.data = data

    def __enter__(self):
        Logger.log_layer_start(self.layer_name, self.data)
        return self

    def __exit__(self, exc_type, exc, tb):
        metrics = None
        # status not needed here; keep metrics for error reporting
        if exc is not None:
            metrics = {"error": str(exc)}
        Logger.log_layer_end(self.layer_name, self.data, metrics)
        return False  # do not suppress exceptions


__all__ = ["Logger", "LogContext"]
