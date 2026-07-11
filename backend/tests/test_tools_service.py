from api.routes.tools import ToolService


def test_tool_service_register_and_manage():
    svc = ToolService()
    # register custom with handler_code
    payload = {"name": "adder", "handler_code": "result = params.get('a',0)+params.get('b',0)"}
    res = svc.register_custom(payload)
    tid = res["id"]
    # get tool
    t = svc.get_tool(tid)
    assert t["name"] == "adder"

    # schema & test
    schema = svc.get_schema(tid)
    assert "input" in schema

    test_res = svc.test_tool(tid, {"a": 1, "b": 2})
    assert test_res["success"]

    # add to agent and list
    svc.add_tool_to_agent("agent-x", tid)
    lst = svc.list_agent_tools("agent-x")
    assert any(i["id"] == tid for i in lst)

    # remove
    svc.remove_tool_from_agent("agent-x", tid)

    # delete permanent after marking as custom
    svc.delete_tool(tid, permanent=True)
    try:
        svc.get_tool(tid)
        assert False, "expected KeyError"
    except KeyError:
        pass
