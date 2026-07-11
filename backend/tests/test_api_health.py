from fastapi.testclient import TestClient

from api.main import create_app


def test_health_endpoints(monkeypatch):
    # Ensure DATABASE_URL is set so create_app lifespan doesn't raise
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    app = create_app()
    client = TestClient(app)

    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data and "checks" in data

    r2 = client.get("/health/ready")
    # readiness may be unhealthy due to missing DB engine; ensure response is valid
    assert r2.status_code in (200, 503)
