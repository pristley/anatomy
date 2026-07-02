from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid
from datetime import datetime

router = APIRouter()


class AgentCreate(BaseModel):
    name: str
    model: str | None = None


AGENTS: list[dict] = []


def _find_agent(agent_id: str) -> dict | None:
    for a in AGENTS:
        if a["id"] == agent_id:
            return a
    return None


@router.get('/')
def list_agents():
    return AGENTS


@router.post('/', status_code=201)
def create_agent(payload: AgentCreate):
    agent = {"id": str(uuid.uuid4()), "name": payload.name, "model": payload.model or "default", "status": "idle", "messages": []}
    AGENTS.append(agent)
    return agent


@router.get('/{agent_id}')
def get_agent(agent_id: str):
    a = _find_agent(agent_id)
    if not a:
        raise HTTPException(status_code=404, detail="agent not found")
    return a


@router.delete('/{agent_id}', status_code=204)
def delete_agent(agent_id: str):
    a = _find_agent(agent_id)
    if not a:
        raise HTTPException(status_code=404, detail="agent not found")
    AGENTS.remove(a)
    return


@router.post('/{agent_id}/messages', status_code=201)
def post_agent_message(agent_id: str, payload: dict):
    a = _find_agent(agent_id)
    if not a:
        raise HTTPException(status_code=404, detail="agent not found")
    msg = {"id": str(uuid.uuid4()), "timestamp": datetime.utcnow().isoformat() + "Z", "payload": payload}
    a.setdefault("messages", []).append(msg)
    return msg
