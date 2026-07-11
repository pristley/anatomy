import asyncio
from api.routes.memory import MemoryService


def test_memory_service_basic_flow():
    svc = MemoryService()
    # initial stats and recent should work even if episodic/semantic are None
    loop = asyncio.get_event_loop()
    res = loop.run_until_complete(svc.stats("agent-x"))
    assert isinstance(res, dict)

    # clear without confirm via API is separate; test clear internal
    res2 = loop.run_until_complete(svc.clear("agent-x"))
    assert isinstance(res2, dict)

    # export should return a StreamingResponse-like object; call export and ensure it returns
    resp = loop.run_until_complete(
        svc.export("agent-x", fmt="json", include=["content"])
    )
    # ensure StreamingResponse-like object
    from starlette.responses import StreamingResponse

    assert isinstance(resp, StreamingResponse)
