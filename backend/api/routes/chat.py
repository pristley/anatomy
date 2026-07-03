from fastapi import APIRouter, Request, HTTPException, Body, Query, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from typing import AsyncGenerator, Dict, List, Any, Optional
import json
import uuid
import time
import asyncio
import logging
import json
from datetime import datetime
from sqlalchemy.orm import Session

router = APIRouter()

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self) -> None:
        # messages stored as: agent_id -> {message_id: message_dict}
        self._store: Dict[str, Dict[str, Dict[str, Any]]] = {}
        # track websocket connections per agent
        self._ws_connections: Dict[str, List[WebSocket]] = {}

    def _now(self) -> int:
        return int(time.time())

    def _ensure_agent(self, agent_id: str) -> None:
        if agent_id not in self._store:
            self._store[agent_id] = {}

    def list_messages(self, agent_id: str, skip: int = 0, limit: int = 50, before: int | None = None, after: int | None = None, role: str | None = None):
        self._ensure_agent(agent_id)
        msgs = list(self._store[agent_id].values())
        # filter
        if role:
            msgs = [m for m in msgs if m.get("role") == role]
        if before:
            msgs = [m for m in msgs if m.get("created_at", 0) < before]
        if after:
            msgs = [m for m in msgs if m.get("created_at", 0) > after]
        # exclude deleted
        msgs = [m for m in msgs if not m.get("deleted")]
        msgs.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        total = len(msgs)
        return {"messages": msgs[skip: skip + limit], "total": total, "skip": skip, "limit": limit}

    def get_message(self, agent_id: str, message_id: str) -> Dict[str, Any]:
        self._ensure_agent(agent_id)
        m = self._store[agent_id].get(message_id)
        if not m or m.get("deleted"):
            raise KeyError("not found")
        return m

    def delete_message(self, agent_id: str, message_id: str) -> None:
        self._ensure_agent(agent_id)
        m = self._store[agent_id].get(message_id)
        if not m:
            raise KeyError("not found")
        m["deleted"] = True

    def add_feedback(self, agent_id: str, message_id: str, rating: int, feedback: str | None = None, tags: List[str] | None = None) -> Dict[str, Any]:
        m = self.get_message(agent_id, message_id)
        m.setdefault("feedback", {})
        m["feedback"]["rating"] = int(rating)
        if feedback:
            m["feedback"]["feedback"] = feedback
        if tags:
            m["feedback"]["tags"] = tags
        return m

    def store_user_message(self, agent_id: str, content: str, metadata: Dict[str, Any] | None = None, db: Optional[Session] = None) -> Dict[str, Any]:
        self._ensure_agent(agent_id)
        mid = str(uuid.uuid4())
        msg = {
            "message_id": mid,
            "agent_id": agent_id,
            "role": "user",
            "content": content,
            "metadata": metadata or {},
            "execution_metadata": {},
            "created_at": self._now(),
            "deleted": False,
        }
        if db:
            # persist to DB Message.payload as JSON
            try:
                from agent_framework.database import models as db_models
            except Exception:
                try:
                    from database import models as db_models
                except Exception:
                    db_models = None
            if db_models:
                record = db_models.Message(id=mid, agent_id=agent_id, payload=json.dumps(msg), timestamp=datetime.utcnow())
                db.add(record)
                db.commit()
            # also keep in-memory for quick access
        self._store[agent_id][mid] = msg
        return msg

    def store_assistant_message(self, agent_id: str, content: str, execution_metadata: Dict[str, Any] | None = None, db: Optional[Session] = None) -> Dict[str, Any]:
        self._ensure_agent(agent_id)
        mid = str(uuid.uuid4())
        msg = {
            "message_id": mid,
            "agent_id": agent_id,
            "role": "assistant",
            "content": content,
            "metadata": {},
            "execution_metadata": execution_metadata or {},
            "created_at": self._now(),
            "deleted": False,
        }
        if db:
            try:
                from agent_framework.database import models as db_models
            except Exception:
                try:
                    from database import models as db_models
                except Exception:
                    db_models = None
            if db_models:
                record = db_models.Message(id=mid, agent_id=agent_id, payload=json.dumps(msg), timestamp=datetime.utcnow())
                db.add(record)
                db.commit()
        self._store[agent_id][mid] = msg
        return msg

    async def stream_response(self, agent_id: str, content: str):
        """Async generator that yields SSE-formatted events for a simulated pipeline."""
        # Simulate layers and token deltas
        # layer_started
        yield {"event": "layer_started", "data": {"layer": "understanding"}}
        await asyncio.sleep(0.01)
        yield {"event": "layer_completed", "data": {"layer": "understanding"}}
        await asyncio.sleep(0.01)

        yield {"event": "tool_started", "data": {"tool": "kb_lookup"}}
        await asyncio.sleep(0.01)
        yield {"event": "tool_completed", "data": {"tool": "kb_lookup", "result_count": 0}}
        await asyncio.sleep(0.01)

        # token deltas
        parts = [content[i : i + 20] for i in range(0, len(content), 20)] or [content]
        for p in parts:
            yield {"event": "token_delta", "data": {"delta": p}}
            await asyncio.sleep(0.005)

        # response delta
        yield {"event": "response_delta", "data": {"text": content}}
        await asyncio.sleep(0.01)

        yield {"event": "response_complete", "data": {"message_id": str(uuid.uuid4())}}
        # done event handled by caller

    async def broadcast_ws(self, agent_id: str, message: Dict[str, Any]):
        conns = self._ws_connections.get(agent_id, [])
        if not conns:
            return
        text = json.dumps(message)
        to_remove = []
        for ws in conns:
            try:
                await ws.send_text(text)
            except Exception:
                to_remove.append(ws)
        for r in to_remove:
            try:
                conns.remove(r)
            except Exception:
                pass


_chat_service = ChatService()


def _sse_format(event: Dict[str, Any]) -> str:
    # SSE format: data: {json}\n\n  (optional event:) not used to keep it simple
    return f"data: {json.dumps(event)}\n\n"


# DB dependency wrapper (optional)
def _get_db_gen():
    try:
        from agent_framework.database.session import get_db
    except Exception:
        try:
            from database.session import get_db
        except Exception:
            get_db = None
    return get_db

_real_get_db = _get_db_gen()
def _db_dep():
    if _real_get_db:
        yield from _real_get_db()
    else:
        yield None


@router.post("/")
async def send_message(agent_id: str, request: Request, payload: Dict[str, Any] = Body(...), db: Optional[Session] = Depends(_db_dep)):
    content = payload.get("content")
    stream = bool(payload.get("stream", False))
    metadata = payload.get("metadata")
    if not content:
        raise HTTPException(status_code=400, detail="missing content")

    # store user message
    user_msg = _chat_service.store_user_message(agent_id, content, metadata=metadata, db=db)

    # sync response
    if not stream:
        # produce assistant reply (placeholder logic)
        reply_text = f"echo: {content}"
        exec_meta = {"pipeline": ["understanding", "tooling", "generation"], "tokens": len(reply_text.split())}
        assistant_msg = _chat_service.store_assistant_message(agent_id, reply_text, execution_metadata=exec_meta, db=db)
        # return combined object
        return JSONResponse(content={
            "message_id": assistant_msg["message_id"],
            "agent_response": assistant_msg["content"],
            "execution_metadata": assistant_msg["execution_metadata"],
            "agent_state": {"status": "idle"},
            "created_at": assistant_msg["created_at"],
        })

    # stream=True: return SSE
    async def sse_gen():
        try:
            async for ev in _chat_service.stream_response(agent_id, f"echo: {content}"):
                yield _sse_format(ev)
            yield "event: done\n\n"
        except asyncio.CancelledError:
            # client disconnected
            return

    return StreamingResponse(sse_gen(), media_type="text/event-stream")


@router.get("/")
async def list_messages(agent_id: str, skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200), before: int | None = None, after: int | None = None, role: str | None = None):
    res = _chat_service.list_messages(agent_id, skip=skip, limit=limit, before=before, after=after, role=role)
    return res


@router.get("/{message_id}")
async def get_message(agent_id: str, message_id: str):
    try:
        m = _chat_service.get_message(agent_id, message_id)
        return m
    except KeyError:
        raise HTTPException(status_code=404, detail="not found")


@router.delete("/{message_id}", status_code=204)
async def delete_message(agent_id: str, message_id: str):
    try:
        _chat_service.delete_message(agent_id, message_id)
        return ""
    except KeyError:
        raise HTTPException(status_code=404, detail="not found")


@router.post("/{message_id}/feedback")
async def feedback(agent_id: str, message_id: str, payload: Dict[str, Any] = Body(...)):
    rating = int(payload.get("rating", 0))
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=400, detail="rating must be 1-5")
    feedback_text = payload.get("feedback")
    tags = payload.get("tags")
    try:
        m = _chat_service.add_feedback(agent_id, message_id, rating, feedback=feedback_text, tags=tags)
        return m
    except KeyError:
        raise HTTPException(status_code=404, detail="not found")


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, agent_id: str):
    await websocket.accept()
    # limit connections per agent
    conns = _chat_service._ws_connections.setdefault(agent_id, [])
    if len(conns) >= 10:
        await websocket.close(code=1008)
        return
    conns.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # expect JSON message with content
            try:
                payload = json.loads(data)
                content = payload.get("content")
            except Exception:
                await websocket.send_text(json.dumps({"error": "invalid message"}))
                continue
            # store user message
            user_msg = _chat_service.store_user_message(agent_id, content, metadata=payload.get("metadata"), db=None)
            # broadcast an assistant reply
            reply_text = f"echo: {content}"
            exec_meta = {"pipeline": ["ws_echo"], "tokens": len(reply_text.split())}
            assistant_msg = _chat_service.store_assistant_message(agent_id, reply_text, execution_metadata=exec_meta, db=None)
            await websocket.send_text(json.dumps({"event": "response", "message": assistant_msg}))
    except WebSocketDisconnect:
        try:
            conns.remove(websocket)
        except Exception:
            pass
