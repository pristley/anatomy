from fastapi import APIRouter, HTTPException, Request, Query, Body
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
import time
import uuid
import logging

router = APIRouter()

logger = logging.getLogger(__name__)


def _error_resp(message: str, request: Request, status_code: int = 400, details: Any = None):
    return HTTPException(status_code=status_code, detail={"error": message, "request_id": request.scope.get("request_id"), "status_code": status_code, "details": details})


class ToolService:
    def __init__(self) -> None:
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._agent_tools: Dict[str, List[str]] = {}
        self._stats: Dict[str, Dict[str, Any]] = {}
        # registry
        try:
            from backend.agent_framework.tools.base import ToolRegistry, ToolDefinition, ToolExecutor
            self._registry = ToolRegistry.get_default()
            self._executor = ToolExecutor(self._registry)
            self._ToolDefinition = ToolDefinition
        except Exception:
            self._registry = None
            self._executor = None
            self._ToolDefinition = None

    def list_tools(self, skip: int = 0, limit: int = 50, category: str = "all", search: Optional[str] = None, agent_id: Optional[str] = None):
        items = list(self._tools.values())
        if category != "all":
            items = [t for t in items if t.get("category") == category]
        if search:
            items = [t for t in items if search.lower() in (t.get("name") or "").lower() or search.lower() in (t.get("description") or "").lower()]
        if agent_id:
            tids = set(self._agent_tools.get(agent_id, []))
            items = [t for t in items if t["id"] in tids]
        total = len(items)
        return {"tools": items[skip: skip + limit], "total": total, "categories": list({t.get("category") for t in items})}

    def get_tool(self, tool_id: str) -> Dict[str, Any]:
        t = self._tools.get(tool_id)
        if not t:
            raise KeyError("not found")
        return t

    def register_custom(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        name = payload.get("name")
        if not name:
            raise ValueError("name required")
        # unique
        if any(t for t in self._tools.values() if t.get("name") == name):
            raise ValueError("name exists")
        # handler required
        handler_url = payload.get("handler_url")
        handler_code = payload.get("handler_code")
        if not handler_url and not handler_code:
            raise ValueError("handler_url or handler_code required")

        tid = str(uuid.uuid4())
        now = int(time.time())
        tool = {
            "id": tid,
            "name": name,
            "description": payload.get("description"),
            "category": "custom",
            "enabled": True,
            "input_schema": payload.get("input_schema"),
            "output_schema": payload.get("output_schema"),
            "handler_url": handler_url,
            "handler_code": handler_code,
            "timeout": payload.get("timeout", 10),
            "max_retries": payload.get("max_retries", 0),
            "tags": payload.get("tags") or [],
            "created_at": now,
            "archived": False,
        }
        self._tools[tid] = tool

        # register into runtime registry if available
        if self._registry and self._ToolDefinition:
            def execute_fn(p: Dict[str, Any]) -> Any:
                # simple sync executor: call handler_url if present, else exec handler_code
                if handler_url:
                    try:
                        import httpx
                        r = httpx.request("POST", handler_url, json=p, timeout=tool["timeout"])
                        try:
                            return r.json()
                        except Exception:
                            return r.text
                    except Exception as exc:
                        raise RuntimeError(str(exc))
                if handler_code:
                    # WARNING: executing arbitrary code — limited use for tests
                    local = {"params": p}
                    exec(handler_code, {}, local)
                    return local.get("result")

            td = self._ToolDefinition(name=tool["name"], description=tool.get("description", ""), params_schema=tool.get("input_schema"), execute_fn=execute_fn)
            try:
                self._registry.register(td)
            except Exception:
                pass

        self._stats[tid] = {"calls": 0, "errors": 0, "total_time_ms": 0}
        logger.info("tool.register", extra={"tool_id": tid, "name": name})
        return {"id": tid, "name": name, "status": "created", "created_at": now}

    def update_tool(self, tool_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        t = self._tools.get(tool_id)
        if not t:
            raise KeyError("not found")
        if t.get("category") != "custom":
            raise PermissionError("cannot modify builtin tool")
        for k in ("description", "input_schema", "output_schema", "handler_url", "handler_code", "timeout", "max_retries", "tags"):
            if k in payload:
                t[k] = payload[k]
        t["updated_at"] = int(time.time())
        return t

    def delete_tool(self, tool_id: str, permanent: bool = False) -> None:
        t = self._tools.get(tool_id)
        if not t:
            raise KeyError("not found")
        if t.get("category") != "custom":
            raise PermissionError("cannot delete builtin tool")
        if permanent:
            del self._tools[tool_id]
        else:
            t["archived"] = True

    def test_tool(self, tool_id: str, input_data: Any, timeout: Optional[int] = None) -> Dict[str, Any]:
        t = self._tools.get(tool_id)
        if not t:
            raise KeyError("not found")
        if not self._executor:
            # no executor available; run local handler if custom
            if t.get("handler_url"):
                import httpx
                try:
                    start = time.time()
                    r = httpx.post(t.get("handler_url"), json=input_data, timeout=timeout or t.get("timeout", 10))
                    elapsed = int((time.time() - start) * 1000)
                    try:
                        output = r.json()
                    except Exception:
                        output = r.text
                    return {"success": True, "output": output, "error": None, "execution_time_ms": elapsed, "logs": []}
                except Exception as exc:
                    return {"success": False, "output": None, "error": str(exc), "execution_time_ms": 0, "logs": []}
            raise RuntimeError("no executor available")

        # use ToolExecutor
        res = self._executor.execute(t.get("name"), params=input_data, timeout_sec=timeout or t.get("timeout", 10))
        # update stats
        sid = t.get("id")
        st = self._stats.setdefault(sid, {"calls": 0, "errors": 0, "total_time_ms": 0})
        st["calls"] += 1
        if res.get("status") != "ok":
            st["errors"] += 1
        st["total_time_ms"] += res.get("execution_time_ms", 0) or 0
        return {"success": res.get("status") == "ok", "output": res.get("output"), "error": res.get("error"), "execution_time_ms": res.get("execution_time_ms"), "logs": []}

    def get_schema(self, tool_id: str) -> Dict[str, Any]:
        t = self._tools.get(tool_id)
        if not t:
            raise KeyError("not found")
        return {"input": t.get("input_schema"), "output": t.get("output_schema"), "parameters": []}

    def add_tool_to_agent(self, agent_id: str, tool_id: str, enabled: bool = True) -> Dict[str, Any]:
        if tool_id not in self._tools:
            raise KeyError("not found")
        lst = self._agent_tools.setdefault(agent_id, [])
        if tool_id not in lst:
            lst.append(tool_id)
        return {"agent_id": agent_id, "tool_id": tool_id, "enabled": enabled}

    def list_agent_tools(self, agent_id: str, enabled_only: bool = False) -> List[Dict[str, Any]]:
        tids = self._agent_tools.get(agent_id, [])
        items = [self._tools[t] for t in tids if t in self._tools]
        if enabled_only:
            items = [i for i in items if i.get("enabled")]
        return items

    def remove_tool_from_agent(self, agent_id: str, tool_id: str) -> None:
        lst = self._agent_tools.get(agent_id, [])
        if tool_id in lst:
            lst.remove(tool_id)
        else:
            raise KeyError("not found")

    def stats_overview(self) -> Dict[str, Any]:
        total = len(self._tools)
        builtin = len([t for t in self._tools.values() if t.get("category") == "builtin"])
        custom = len([t for t in self._tools.values() if t.get("category") == "custom"])
        total_calls = sum(s.get("calls", 0) for s in self._stats.values())
        total_errors = sum(s.get("errors", 0) for s in self._stats.values())
        avg_success = 0.0
        if total_calls:
            avg_success = 1.0 - (total_errors / total_calls)
        return {"total_tools": total, "builtin_count": builtin, "custom_count": custom, "most_used": [], "most_reliable": [], "slowest": [], "total_calls": total_calls, "total_errors": total_errors, "avg_success_rate": avg_success}


_svc = ToolService()


@router.get("/")
async def list_tools(request: Request, skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=500), category: str = Query("all"), search: Optional[str] = Query(None), agent_id: Optional[str] = Query(None)):
    res = _svc.list_tools(skip=skip, limit=limit, category=category, search=search, agent_id=agent_id)
    return JSONResponse(content=res)


@router.get("/{tool_id}")
async def get_tool(request: Request, tool_id: str):
    try:
        t = _svc.get_tool(tool_id)
        return JSONResponse(content=t)
    except KeyError:
        raise _error_resp("not found", request, 404)


@router.post("/", status_code=201)
async def register_tool(request: Request, payload: Dict[str, Any] = Body(...)):
    try:
        res = _svc.register_custom(payload)
        return JSONResponse(content=res)
    except ValueError as ve:
        raise _error_resp(str(ve), request, 400)
    except Exception as exc:
        raise _error_resp("internal error", request, 500, details=str(exc))


@router.put("/{tool_id}")
async def update_tool(request: Request, tool_id: str, payload: Dict[str, Any] = Body(...)):
    try:
        t = _svc.update_tool(tool_id, payload)
        return JSONResponse(content=t)
    except KeyError:
        raise _error_resp("not found", request, 404)
    except PermissionError:
        raise _error_resp("forbidden", request, 403)
    except Exception as exc:
        raise _error_resp("internal error", request, 500, details=str(exc))


@router.delete("/{tool_id}")
async def delete_tool(request: Request, tool_id: str, permanent: bool = Query(False)):
    try:
        _svc.delete_tool(tool_id, permanent=permanent)
        return JSONResponse(status_code=204, content=None)
    except KeyError:
        raise _error_resp("not found", request, 404)
    except PermissionError:
        raise _error_resp("forbidden", request, 403)


@router.post("/{tool_id}/test")
async def test_tool(request: Request, tool_id: str, payload: Dict[str, Any] = Body(...)):
    try:
        input_data = payload.get("input")
        timeout = payload.get("timeout")
        res = _svc.test_tool(tool_id, input_data, timeout=timeout)
        return JSONResponse(content=res)
    except KeyError:
        raise _error_resp("not found", request, 404)
    except Exception as exc:
        raise _error_resp("internal error", request, 500, details=str(exc))


@router.get("/{tool_id}/schema")
async def get_schema(request: Request, tool_id: str):
    try:
        s = _svc.get_schema(tool_id)
        return JSONResponse(content=s)
    except KeyError:
        raise _error_resp("not found", request, 404)


@router.post("/agents/{agent_id}")
async def add_tool_to_agent(request: Request, agent_id: str, payload: Dict[str, Any] = Body(...)):
    tool_id = payload.get("tool_id")
    enabled = payload.get("enabled", True)
    try:
        res = _svc.add_tool_to_agent(agent_id, tool_id, enabled=enabled)
        return JSONResponse(status_code=201, content=res)
    except KeyError:
        raise _error_resp("not found", request, 404)


@router.get("/agents/{agent_id}")
async def list_agent_tools(request: Request, agent_id: str, enabled_only: bool = Query(False)):
    res = _svc.list_agent_tools(agent_id, enabled_only=enabled_only)
    return JSONResponse(content={"tools": res})


@router.delete("/agents/{agent_id}/{tool_id}")
async def remove_tool_from_agent(request: Request, agent_id: str, tool_id: str):
    try:
        _svc.remove_tool_from_agent(agent_id, tool_id)
        return JSONResponse(status_code=204, content=None)
    except KeyError:
        raise _error_resp("not found", request, 404)


@router.get("/stats")
async def tool_stats(request: Request):
    return JSONResponse(content=_svc.stats_overview())
