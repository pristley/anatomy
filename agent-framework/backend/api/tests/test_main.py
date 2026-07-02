from fastapi.testclient import TestClient
from api.main import app


def test_health_and_agents():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"

    r2 = client.get("/api/agents/")
    assert r2.status_code == 200
    assert isinstance(r2.json(), list)

    # create an agent
    r3 = client.post("/api/agents/", json={"name": "test-agent"})
    assert r3.status_code == 201
    j = r3.json()
    assert j["name"] == "test-agent"
    assert "id" in j

    agent_id = j["id"]

    # post a message to the agent
    r4 = client.post(f"/api/agents/{agent_id}/messages", json={"text": "hello"})
    assert r4.status_code == 201
    m = r4.json()
    assert m["payload"]["text"] == "hello"

    # delete the agent
    r5 = client.delete(f"/api/agents/{agent_id}")
    assert r5.status_code == 204

    # ensure it's gone
    r6 = client.get(f"/api/agents/{agent_id}")
    assert r6.status_code == 404
