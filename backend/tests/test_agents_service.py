from api.routes.agents import AgentService, AgentCreate, AgentUpdate


def test_agent_service_crud_flow():
    svc = AgentService()
    owner = "user-1"
    payload = AgentCreate(name="agent1", description="desc")
    obj = svc.create_agent(owner, payload)
    aid = obj["id"]
    assert obj["name"] == "agent1"

    listed = svc.list_agents(owner)
    assert any(a["id"] == aid for a in listed["agents"])

    got = svc.get_agent(aid)
    assert got["name"] == "agent1"

    # update
    up = AgentUpdate(name="agent2", description="new")
    updated = svc.update_agent(aid, owner, up)
    assert updated["name"] == "agent2"

    # patch status
    patched = svc.patch_status(aid, owner, "running")
    assert patched["status"] == "running"

    # reset
    reset = svc.reset_agent(aid, owner)
    assert isinstance(reset, dict)

    # clone
    clone = svc.clone_agent(aid, owner)
    assert clone["name"].endswith("_clone")

    # delete permanent
    svc.delete_agent(aid, owner, permanent=True)
    try:
        svc.get_agent(aid)
        assert False
    except KeyError:
        pass
