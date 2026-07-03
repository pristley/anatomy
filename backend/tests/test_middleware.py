import os
import jwt
import pytest
from fastapi.testclient import TestClient

from backend.api.main import app

client = TestClient(app)


def _make_token(sub: str, secret: str = "test-secret", alg: str = "HS256"):
    return jwt.encode({"sub": sub}, secret, algorithm=alg)


@pytest.fixture(autouse=True)
def set_jwt_env(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    yield


def test_auth_bypasses_public_endpoint():
    r = client.get("/health")
    assert r.status_code == 200


def test_auth_rejects_without_token():
    r = client.get("/agents/")
    assert r.status_code == 401


def test_auth_accepts_valid_jwt():
    token = _make_token("user-123", secret="test-secret")
    headers = {"Authorization": f"Bearer {token}"}
    r = client.get("/agents/", headers=headers)
    # the in-memory agents route allows listing but requires auth; if auth passes, 200
    assert r.status_code == 200
