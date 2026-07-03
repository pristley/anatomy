from __future__ import annotations

import asyncio
import logging
import os
import re
import socket
import base64
from typing import Any, Dict, Optional
from urllib.parse import urlparse, urlencode, urlunparse, parse_qsl
import ipaddress

import httpx

logger = logging.getLogger(__name__)


class APICallTool:
    name = "api_call"
    description = "Make HTTP requests to any REST API"

    params_schema = {
        "url": "str",
        "method": "GET|POST|PUT|DELETE|PATCH",
        "headers": "dict",
        "params": "dict",
        "body": "dict",
        "timeout": "int",
        "auth": "dict",
    }

    def __init__(self) -> None:
        self.whitelist = [d.strip().lower() for d in os.getenv("API_WHITELIST_DOMAINS", "").split(",") if d.strip()]
        self.max_response = int(os.getenv("API_MAX_RESPONSE_SIZE", str(1024 * 1024)))
        self.max_timeout = int(os.getenv("API_MAX_TIMEOUT", "30"))
        self.env = os.getenv("ENVIRONMENT", "development").lower()

    @staticmethod
    def _is_private_host(host: str) -> bool:
        try:
            # If host is an IP
            addr = ipaddress.ip_address(host)
            return addr.is_private or addr.is_loopback or addr.is_reserved
        except Exception:
            # Resolve DNS to IPs and check
            try:
                infos = socket.getaddrinfo(host, None)
                for fam, _, _, _, sockaddr in infos:
                    ip = sockaddr[0]
                    try:
                        addr = ipaddress.ip_address(ip)
                        if addr.is_private or addr.is_loopback or addr.is_reserved:
                            return True
                    except Exception:
                        continue
            except Exception:
                # If we cannot resolve, treat as private/unsafe
                return True
        return False

    def _validate_whitelist(self, host: str) -> bool:
        if not self.whitelist:
            # no whitelist configured -> allow all (but still block private IPs)
            return True
        host = host.lower()
        for domain in self.whitelist:
            if host == domain or host.endswith("." + domain):
                return True
        return False

    @staticmethod
    def _strip_html(text: str) -> str:
        # naive HTML -> text
        return re.sub(r"<[^>]+>", "", text)

    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        url = params.get("url")
        if not url:
            return {"error": "url is required", "status_code": None}

        try:
            parsed = urlparse(url)
            host = parsed.hostname or ""
        except Exception:
            return {"error": "invalid url", "status_code": None}

        if not self._validate_whitelist(host):
            return {"error": f"domain {host} not allowed", "status_code": None}

        if self._is_private_host(host):
            return {"error": "private IPs are not allowed", "status_code": None}

        method = (params.get("method") or "GET").upper()
        headers = dict((params.get("headers") or {}) or {})
        qparams = dict((params.get("params") or {}) or {})
        body = params.get("body")
        timeout = min(int(params.get("timeout", 10)), self.max_timeout)

        auth = params.get("auth") or {}
        # handle auth
        if auth:
            if auth.get("type") == "bearer" and auth.get("token"):
                headers.setdefault("Authorization", f"Bearer {auth.get('token')}")
            elif auth.get("type") == "basic" and auth.get("username") and auth.get("password"):
                cred = f"{auth.get('username')}:{auth.get('password')}"
                headers.setdefault("Authorization", "Basic " + base64.b64encode(cred.encode()).decode())
            elif auth.get("type") == "api_key":
                loc = auth.get("in", "header")
                key = auth.get("key")
                name = auth.get("name", "x-api-key")
                if key:
                    if loc == "header":
                        headers.setdefault(name, key)
                    else:
                        # query
                        qparams.setdefault(name, key)

        # rebuild URL with query params
        try:
            existing_q = dict(parse_qsl(parsed.query or ""))
            merged_q = {**existing_q, **qparams}
            rebuilt = parsed._replace(query=urlencode(merged_q))
            final_url = urlunparse(rebuilt)
        except Exception:
            final_url = url

        # Always verify TLS by default; allow disabling via API_ALLOW_INSECURE env var
        verify = not bool(os.getenv("API_ALLOW_INSECURE", ""))

        async with httpx.AsyncClient(verify=verify, timeout=timeout) as client:
            try:
                logger.info("api_call: %s %s", method, final_url)
                resp = await client.request(method, final_url, headers=headers, json=body if body is not None else None)
            except httpx.ReadTimeout:
                return {"error": "Request timed out", "status_code": None}
            except httpx.ConnectError:
                return {"error": "Connection failed", "status_code": None}
            except Exception as exc:
                logger.exception("api_call exception")
                return {"error": f"connection error: {exc}", "status_code": None}

        # Truncate response body for safety
        content_type = resp.headers.get("content-type", "")
        body_bytes = resp.content or b""
        if len(body_bytes) > self.max_response:
            truncated = True
            body_bytes = body_bytes[: self.max_response]
        else:
            truncated = False

        # parse based on content-type
        result_body: Any = None
        try:
            if "application/json" in content_type:
                result_body = resp.json()
            elif "text/html" in content_type or content_type.startswith("text/"):
                text = body_bytes.decode(errors="replace")
                if "text/html" in content_type:
                    text = self._strip_html(text)
                result_body = text[:1000]
            else:
                # fallback to text
                result_body = body_bytes.decode(errors="replace")[:10000]
        except Exception:
            result_body = body_bytes.decode(errors="replace")[:10000]

        out = {
            "status_code": resp.status_code,
            "headers": dict(resp.headers),
            "body": result_body,
            "truncated": truncated,
        }

        if 400 <= resp.status_code < 600:
            out["error"] = f"http error {resp.status_code}"

        return out


def get_tool_definition() -> Any:
    """Return a tool registration object compatible with available registries.

    Tries to return a `ToolDefinition` (tools.base) or `Tool` (core.tools.registry).
    """
    try:
        from backend.agent_framework.tools.base import ToolDefinition

        def execute_sync(params: Dict[str, Any]) -> Dict[str, Any]:
            # run async execute in event loop
            tool = APICallTool()
            try:
                return asyncio.get_event_loop().run_until_complete(tool.execute(params))
            except RuntimeError:
                # no running loop
                return asyncio.new_event_loop().run_until_complete(tool.execute(params))

        return ToolDefinition(name=APICallTool.name, description=APICallTool.description, params_schema=APICallTool.params_schema, execute_fn=execute_sync)
    except Exception:
        try:
            from backend.agent_framework.core.tools.registry import Tool

            def handler(params: Dict[str, Any]) -> Dict[str, Any]:
                tool = APICallTool()
                try:
                    return asyncio.get_event_loop().run_until_complete(tool.execute(params))
                except RuntimeError:
                    return asyncio.new_event_loop().run_until_complete(tool.execute(params))

            return Tool(name=APICallTool.name, description=APICallTool.description, params_schema=APICallTool.params_schema, handler=handler)
        except Exception:
            # Last resort: return class
            return APICallTool()


__all__ = ["APICallTool", "get_tool_definition"]
