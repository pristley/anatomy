import pytest
from fastapi.testclient import TestClient

from backend.api.main import app


client = TestClient(app)


def test_health_structure_and_headers():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert "status" in body
    assert body["status"] in {"healthy", "degraded", "unhealthy"}
    assert "timestamp" in body
    assert "uptime_seconds" in body
    assert isinstance(body["uptime_seconds"], int)
    assert "version" in body
    assert "checks" in body and isinstance(body["checks"], dict)

    # security headers present
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"
    assert r.headers.get("X-XSS-Protection") == "1; mode=block"


def test_readiness_returns_expected_status():
    r = client.get("/health/ready")
    # readiness may be 200 or 503 depending on environment; ensure allowed codes
    assert r.status_code in (200, 503)
