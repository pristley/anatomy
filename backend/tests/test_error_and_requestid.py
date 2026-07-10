import re
from fastapi import APIRouter
from fastapi.testclient import TestClient
from backend.api.main import app


def _mount_test_routes():
    router = APIRouter()

    @router.get("/health/test/value_error")
    async def raise_value():
        raise ValueError("bad input")

    @router.get("/health/test/key_error")
    async def raise_key():
        raise KeyError("missing")

    @router.get("/health/test/exception")
    async def raise_exc():
        raise Exception("boom")

    app.include_router(router)


def test_request_id_propagation_and_error_mapping():
    _mount_test_routes()
    client = TestClient(app)

    # 1) Provided X-Request-ID should be preserved in header and body
    headers = {"X-Request-ID": "req-123"}
    r = client.get("/health/test/value_error", headers=headers)
    assert r.status_code == 400
    assert r.headers.get("X-Request-ID") == "req-123"
    body = r.json()
    assert body.get("request_id") == "req-123"

    # 2) KeyError maps to 404 and body contains request_id header
    r2 = client.get("/health/test/key_error")
    assert r2.status_code == 404
    body2 = r2.json()
    assert "request_id" in body2

    # 3) Generic exception maps to 500 and request_id is present
    r3 = client.get("/health/test/exception")
    assert r3.status_code == 500
    body3 = r3.json()
    assert "request_id" in body3

    # 4) When no X-Request-ID provided, middleware generates a uuid-like value
    pattern = re.compile(r"^[0-9a-fA-F\-]{20,40}$")
    rid = body3.get("request_id")
    assert isinstance(rid, str) and pattern.match(rid)
