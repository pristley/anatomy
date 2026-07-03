import json
from typing import Any
from .context import request_id_var, correlation_id_var


def _format(obj: Any) -> str:
    try:
        if isinstance(obj, (dict, list)):
            return json.dumps(obj)
        return str(obj)
    except Exception:
        return repr(obj)


def _augment(msg: Any) -> str:
    rid = request_id_var.get() or ""
    cid = correlation_id_var.get() or ""
    base = _format(msg)
    try:
        # if msg is JSON-able dict, merge request id
        if isinstance(msg, dict):
            m = dict(msg)
            if rid:
                m["request_id"] = rid
            if cid:
                m["correlation_id"] = cid
            return json.dumps(m)
    except Exception:
        pass
    # fallback: append ids
    extras = {}
    if rid:
        extras["request_id"] = rid
    if cid:
        extras["correlation_id"] = cid
    if extras:
        return f"{base} | {json.dumps(extras)}"
    return base


def info(msg: Any):
    print(_augment(msg))


def warning(msg: Any):
    print(_augment(msg))


def exception(msg: Any):
    print(_augment(msg))


__all__ = ["info", "warning", "exception"]
