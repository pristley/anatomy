from fastapi import APIRouter, HTTPException, Depends, Request, Query, Body
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
import uuid
import re
import time
import logging
import json
from datetime import datetime
from sqlalchemy.orm import Session

router = APIRouter()

logger = logging.getLogger(__name__)


def _error_resp(message: str, request: Request, status_code: int = 400, details: Any = None):
    return HTTPException(status_code=status_code, detail={"error": message, "request_id": request.scope.get("request_id"), "status_code": status_code, "details": details})


class AgentCreate(BaseModel):
    name: str = Field(..., pattern=r"^\w+$")
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @validator("name")
    def name_must_be_valid(cls, v: str) -> str:
        if not re.match(r"^\w+$", v):
            raise ValueError("name must be alphanumeric or underscore")
        return v


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None, pattern=r"^\w+$")
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class AgentOut(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    config: Dict[str, Any]
    status: Optional[str] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None
    owner_id: Optional[str] = None
    stats: Optional[Dict[str, Any]] = None


class AgentService:
    """Business logic for agent CRUD. Uses a DB session if provided, otherwise in-memory store."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        # simple in-memory store: id -> agent dict
        if not hasattr(self, "_store"):
            self._store: Dict[str, Dict[str, Any]] = {}
        # config cache: agent_id -> (config, ts)
        self._config_cache: Dict[str, Any] = {}
        self._config_cache_ts: Dict[str, float] = {}

    def _now_ts(self) -> int:
        return int(time.time())

    def _import_models(self):
        try:
            from agent_framework.database import models as m
        except Exception:
            try:
                from database import models as m
            except Exception:
                m = None
        return m

    def _agent_to_dict(self, a) -> Dict[str, Any]:
        # SQLAlchemy Agent -> dict
        if not a:
            return None
        try:
            cfg = json.loads(a.config) if a.config else {}
        except Exception:
            cfg = {}
        try:
            stats = json.loads(a.stats) if a.stats else {}
        except Exception:
            stats = {}
        return {
            "id": a.id,
            "name": a.name,
            "description": a.description,
            "config": cfg,
            "status": a.status,
            "created_at": int(a.created_at.timestamp()) if a.created_at else None,
            "updated_at": int(a.updated_at.timestamp()) if hasattr(a, 'updated_at') and a.updated_at else None,
            "owner_id": a.owner_id,
            "stats": stats,
            "archived": bool(a.archived) if hasattr(a, 'archived') else False,
        }

    def create_agent(self, owner_id: str, payload: AgentCreate) -> Dict[str, Any]:
        # DB-backed path
        if self.db:
            models = self._import_models()
            if not models:
                raise RuntimeError("DB models not available")
            aid = str(uuid.uuid4())
            now = datetime.utcnow()
            ag = models.Agent(
                id=aid,
                name=payload.name,
                description=payload.description,
                config=json.dumps(payload.config or {}),
                owner_id=owner_id,
                status="idle",
                created_at=now,
                updated_at=now,
                archived=False,
                stats=json.dumps({}),
            )
            self.db.add(ag)
            self.db.commit()
            self.db.refresh(ag)
            logger.info("agent.create", extra={"agent_id": aid, "owner_id": owner_id})
            return self._agent_to_dict(ag)

        # fallback in-memory
        for a in self._store.values():
            if a["name"] == payload.name:
                raise ValueError("name exists")
        aid = str(uuid.uuid4())
        now = self._now_ts()
        obj = {
            "id": aid,
            "name": payload.name,
            "description": payload.description,
            "config": payload.config or {},
            "status": "idle",
            "created_at": now,
            "updated_at": now,
            "owner_id": owner_id,
            "stats": {},
            "archived": False,
        }
        self._store[aid] = obj
        logger.info("agent.create", extra={"agent_id": aid, "owner_id": owner_id})
        return obj

    def list_agents(self, owner_id: str, skip: int = 0, limit: int = 20, status: Optional[str] = None, search: Optional[str] = None):
        if self.db:
            models = self._import_models()
            q = self.db.query(models.Agent).filter(models.Agent.owner_id == owner_id, models.Agent.archived == False)
            if status:
                q = q.filter(models.Agent.status == status)
            if search:
                like = f"%{search}%"
                q = q.filter(models.Agent.name.ilike(like) | (models.Agent.description.ilike(like)))
            total = q.count()
            items = q.offset(skip).limit(limit).all()
            return {"agents": [self._agent_to_dict(a) for a in items], "total": total, "skip": skip, "limit": limit}

        items = [v for v in self._store.values() if v.get("owner_id") == owner_id and not v.get("archived")]
        if status:
            items = [i for i in items if i.get("status") == status]
        if search:
            items = [i for i in items if search.lower() in i.get("name", "").lower() or (i.get("description") and search.lower() in i.get("description").lower())]
        total = len(items)
        return {"agents": items[skip: skip + limit], "total": total, "skip": skip, "limit": limit}

    def get_agent(self, agent_id: str) -> Dict[str, Any]:
        if self.db:
            models = self._import_models()
            ag = self.db.query(models.Agent).get(agent_id)
            if not ag or getattr(ag, 'archived', False):
                raise KeyError("not found")
            return self._agent_to_dict(ag)

        ag = self._store.get(agent_id)
        if not ag or ag.get("archived"):
            raise KeyError("not found")
        return ag

    def update_agent(self, agent_id: str, owner_id: str, payload: AgentUpdate) -> Dict[str, Any]:
        if self.db:
            models = self._import_models()
            ag = self.db.query(models.Agent).get(agent_id)
            if not ag or getattr(ag, 'archived', False):
                raise KeyError("not found")
            if ag.owner_id != owner_id:
                raise PermissionError("forbidden")
            # uniqueness
            if payload.name:
                exists = self.db.query(models.Agent).filter(models.Agent.name == payload.name, models.Agent.id != agent_id).first()
                if exists:
                    raise ValueError("name exists")
                ag.name = payload.name
            if payload.description is not None:
                ag.description = payload.description
            if payload.config is not None:
                ag.config = json.dumps(payload.config)
                # invalidate cache: best-effort
                self._config_cache_ts.pop(agent_id, None)
            if payload.status is not None:
                ag.status = payload.status
            ag.updated_at = datetime.utcnow()
            self.db.add(ag)
            self.db.commit()
            self.db.refresh(ag)
            logger.info("agent.update", extra={"agent_id": agent_id, "owner_id": owner_id})
            return self._agent_to_dict(ag)

        ag = self._store.get(agent_id)
        if not ag or ag.get("archived"):
            raise KeyError("not found")
        if ag.get("owner_id") != owner_id:
            raise PermissionError("forbidden")
        if payload.name and any(a for a in self._store.values() if a["name"] == payload.name and a["id"] != agent_id):
            raise ValueError("name exists")
        if payload.name:
            ag["name"] = payload.name
        if payload.description is not None:
            ag["description"] = payload.description
        if payload.config is not None:
            ag["config"] = payload.config
            # invalidate cache
            self._config_cache_ts.pop(agent_id, None)
        if payload.status is not None:
            ag["status"] = payload.status
        ag["updated_at"] = self._now_ts()
        logger.info("agent.update", extra={"agent_id": agent_id, "owner_id": owner_id})
        return ag

    def delete_agent(self, agent_id: str, owner_id: str, permanent: bool = False) -> None:
        if self.db:
            models = self._import_models()
            ag = self.db.query(models.Agent).get(agent_id)
            if not ag:
                raise KeyError("not found")
            if ag.owner_id != owner_id:
                raise PermissionError("forbidden")
            if permanent:
                self.db.delete(ag)
                self.db.commit()
                logger.info("agent.delete.permanent", extra={"agent_id": agent_id, "owner_id": owner_id})
                return
            ag.archived = True
            ag.updated_at = datetime.utcnow()
            self.db.add(ag)
            self.db.commit()
            logger.info("agent.delete.soft", extra={"agent_id": agent_id, "owner_id": owner_id})
            return

        ag = self._store.get(agent_id)
        if not ag:
            raise KeyError("not found")
        if ag.get("owner_id") != owner_id:
            raise PermissionError("forbidden")
        if permanent:
            del self._store[agent_id]
            logger.info("agent.delete.permanent", extra={"agent_id": agent_id, "owner_id": owner_id})
            return
        # soft delete
        ag["archived"] = True
        ag["updated_at"] = self._now_ts()
        logger.info("agent.delete.soft", extra={"agent_id": agent_id, "owner_id": owner_id})

    def patch_status(self, agent_id: str, owner_id: str, status: str) -> Dict[str, Any]:
        if self.db:
            models = self._import_models()
            ag = self.db.query(models.Agent).get(agent_id)
            if not ag:
                raise KeyError("not found")
            if ag.owner_id != owner_id:
                raise PermissionError("forbidden")
            ag.status = status
            ag.updated_at = datetime.utcnow()
            self.db.add(ag)
            self.db.commit()
            logger.info("agent.status", extra={"agent_id": agent_id, "owner_id": owner_id, "status": status})
            return self._agent_to_dict(ag)

        ag = self._store.get(agent_id)
        if not ag:
            raise KeyError("not found")
        if ag.get("owner_id") != owner_id:
            raise PermissionError("forbidden")
        ag["status"] = status
        ag["updated_at"] = self._now_ts()
        logger.info("agent.status", extra={"agent_id": agent_id, "owner_id": owner_id, "status": status})
        return ag

    def reset_agent(self, agent_id: str, owner_id: str) -> Dict[str, Any]:
        if self.db:
            models = self._import_models()
            ag = self.db.query(models.Agent).get(agent_id)
            if not ag:
                raise KeyError("not found")
            if ag.owner_id != owner_id:
                raise PermissionError("forbidden")
            ag.stats = json.dumps({})
            ag.updated_at = datetime.utcnow()
            self.db.add(ag)
            self.db.commit()
            logger.info("agent.reset", extra={"agent_id": agent_id, "owner_id": owner_id})
            return self._agent_to_dict(ag)

        ag = self._store.get(agent_id)
        if not ag:
            raise KeyError("not found")
        if ag.get("owner_id") != owner_id:
            raise PermissionError("forbidden")
        ag["stats"] = {}
        ag["updated_at"] = self._now_ts()
        logger.info("agent.reset", extra={"agent_id": agent_id, "owner_id": owner_id})
        # placeholder: clear memory if integrated
        return ag

    def clone_agent(self, agent_id: str, owner_id: str) -> Dict[str, Any]:
        if self.db:
            models = self._import_models()
            src = self.db.query(models.Agent).get(agent_id)
            if not src:
                raise KeyError("not found")
            new_id = str(uuid.uuid4())
            now = datetime.utcnow()
            clone = models.Agent(
                id=new_id,
                name=f"{src.name}_clone",
                description=src.description,
                config=src.config,
                owner_id=owner_id,
                status=src.status,
                created_at=now,
                updated_at=now,
                archived=False,
                stats=src.stats,
            )
            self.db.add(clone)
            self.db.commit()
            self.db.refresh(clone)
            logger.info("agent.clone", extra={"src": agent_id, "new": new_id, "owner_id": owner_id})
            return self._agent_to_dict(clone)

        src = self._store.get(agent_id)
        if not src:
            raise KeyError("not found")
        # create copy with new id
        new_id = str(uuid.uuid4())
        now = self._now_ts()
        clone = dict(src)
        clone["id"] = new_id
        clone["name"] = f"{src.get('name')}_clone"
        clone["owner_id"] = owner_id
        clone["created_at"] = now
        clone["updated_at"] = now
        clone["stats"] = {}
        self._store[new_id] = clone
        logger.info("agent.clone", extra={"src": agent_id, "new": new_id, "owner_id": owner_id})
        return clone

    def get_config_cached(self, agent_id: str, ttl: int = 60):
        now = time.time()
        ts = self._config_cache_ts.get(agent_id, 0)
        if now - ts < ttl and agent_id in self._config_cache:
            return self._config_cache[agent_id]
        if self.db:
            models = self._import_models()
            ag = self.db.query(models.Agent).get(agent_id)
            if not ag:
                raise KeyError("not found")
            try:
                cfg = json.loads(ag.config) if ag.config else {}
            except Exception:
                cfg = {}
            self._config_cache[agent_id] = cfg
            self._config_cache_ts[agent_id] = now
            return cfg
        ag = self._store.get(agent_id)
        if not ag:
            raise KeyError("not found")
        cfg = ag.get("config", {})
        self._config_cache[agent_id] = cfg
        self._config_cache_ts[agent_id] = now
        return cfg


def get_current_user(request: Request) -> str:
    # AuthMiddleware stores `user_id` in request.scope
    return request.scope.get("user_id")


def get_db_session():
    # Try to import project's DB session generator
    try:
        from agent_framework.database.session import get_db
    except Exception:
        try:
            from database.session import get_db
        except Exception:
            get_db = None
    return get_db


# Wrap the backend session generator so FastAPI can depend on it even when absent
_real_get_db = get_db_session()
def _db_dep():
    if _real_get_db:
        yield from _real_get_db()
    else:
        yield None


# instantiate a default service (in-memory)
_default_service = AgentService()


@router.post("/", response_model=AgentOut, status_code=201)
async def create_agent(request: Request, payload: AgentCreate, user_id: str = Depends(get_current_user), db: Optional[Session] = Depends(_db_dep)):
    if not user_id:
        raise _error_resp("unauthorized", request, 401)
    try:
        svc = AgentService(db=db) if db else _default_service
        obj = svc.create_agent(user_id, payload)
        return obj
    except ValueError as ve:
        raise _error_resp(str(ve), request, 409)
    except Exception as exc:
        raise _error_resp("internal error", request, 500, details=str(exc))


@router.get("/", response_model=Dict)
async def list_agents(request: Request, skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), status: Optional[str] = None, search: Optional[str] = None, user_id: str = Depends(get_current_user), db: Optional[Session] = Depends(_db_dep)):
    if not user_id:
        raise _error_resp("unauthorized", request, 401)
    svc = AgentService(db=db) if db else _default_service
    res = svc.list_agents(user_id, skip=skip, limit=limit, status=status, search=search)
    return res


@router.get("/{agent_id}", response_model=AgentOut)
async def get_agent(request: Request, agent_id: str, user_id: str = Depends(get_current_user), db: Optional[Session] = Depends(_db_dep)):
    if not user_id:
        raise _error_resp("unauthorized", request, 401)
    svc = AgentService(db=db) if db else _default_service
    try:
        ag = svc.get_agent(agent_id)
        if ag.get("owner_id") != user_id:
            raise PermissionError("forbidden")
        return ag
    except KeyError:
        raise _error_resp("not found", request, 404)
    except PermissionError:
        raise _error_resp("forbidden", request, 403)


@router.put("/{agent_id}", response_model=AgentOut)
async def update_agent(request: Request, agent_id: str, payload: AgentUpdate, user_id: str = Depends(get_current_user), db: Optional[Session] = Depends(_db_dep)):
    if not user_id:
        raise _error_resp("unauthorized", request, 401)
    svc = AgentService(db=db) if db else _default_service
    try:
        ag = svc.update_agent(agent_id, user_id, payload)
        return ag
    except KeyError:
        raise _error_resp("not found", request, 404)
    except PermissionError:
        raise _error_resp("forbidden", request, 403)
    except ValueError as ve:
        raise _error_resp(str(ve), request, 400)
    except Exception as exc:
        raise _error_resp("internal error", request, 500, details=str(exc))


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(request: Request, agent_id: str, permanent: bool = Query(False), user_id: str = Depends(get_current_user), db: Optional[Session] = Depends(_db_dep)):
    if not user_id:
        raise _error_resp("unauthorized", request, 401)
    svc = AgentService(db=db) if db else _default_service
    try:
        svc.delete_agent(agent_id, user_id, permanent=permanent)
        return ""
    except KeyError:
        raise _error_resp("not found", request, 404)
    except PermissionError:
        raise _error_resp("forbidden", request, 403)
    except Exception as exc:
        raise _error_resp("internal error", request, 500, details=str(exc))


@router.patch("/{agent_id}/status", response_model=AgentOut)
async def patch_status(request: Request, agent_id: str, status_payload: Dict[str, str] = Body(...), user_id: str = Depends(get_current_user), db: Optional[Session] = Depends(_db_dep)):
    if not user_id:
        raise _error_resp("unauthorized", request, 401)
    status = status_payload.get("status")
    if not status:
        raise _error_resp("status required", request, 400)
    svc = AgentService(db=db) if db else _default_service
    try:
        ag = svc.patch_status(agent_id, user_id, status)
        return ag
    except KeyError:
        raise _error_resp("not found", request, 404)
    except PermissionError:
        raise _error_resp("forbidden", request, 403)


@router.post("/{agent_id}/reset", response_model=AgentOut)
async def reset_agent(request: Request, agent_id: str, user_id: str = Depends(get_current_user), db: Optional[Session] = Depends(_db_dep)):
    if not user_id:
        raise _error_resp("unauthorized", request, 401)
    svc = AgentService(db=db) if db else _default_service
    try:
        ag = svc.reset_agent(agent_id, user_id)
        return ag
    except KeyError:
        raise _error_resp("not found", request, 404)
    except PermissionError:
        raise _error_resp("forbidden", request, 403)


@router.post("/{agent_id}/clone", response_model=AgentOut)
async def clone_agent(request: Request, agent_id: str, user_id: str = Depends(get_current_user), db: Optional[Session] = Depends(_db_dep)):
    if not user_id:
        raise _error_resp("unauthorized", request, 401)
    svc = AgentService(db=db) if db else _default_service
    try:
        clone = svc.clone_agent(agent_id, user_id)
        return clone
    except KeyError:
        raise _error_resp("not found", request, 404)
    except PermissionError:
        raise _error_resp("forbidden", request, 403)
