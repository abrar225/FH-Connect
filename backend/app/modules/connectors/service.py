import hashlib
import json
from typing import Any, Optional

import asyncpg
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.auth import AuthUser, get_current_user
from app.core.database import db
from app.core.permissions import Capability, require_capability
from app.modules.audit.repository import record_audit_event
from app.workers.connector_queue import enqueue_connector_job

router = APIRouter()


class ConnectorJobRequest(BaseModel):
    provider: str
    action: str
    room_id: Optional[str] = None
    payload: dict[str, Any] = Field(default_factory=dict)


@router.post("/connectors/jobs")
async def create_connector_job(req: ConnectorJobRequest, current_user: AuthUser = Depends(get_current_user)):
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not configured")
    if req.room_id:
        await require_capability(current_user, Capability.CONNECTOR_EXECUTE, {"room_id": req.room_id})
    else:
        await require_capability(current_user, Capability.CONNECTOR_CONFIGURE, {})

    payload_json = json.dumps(req.payload, sort_keys=True, separators=(",", ":"))
    idempotency_material = json.dumps({
        "provider": req.provider.lower(),
        "action": req.action,
        "room_id": req.room_id,
        "payload": req.payload,
    }, sort_keys=True, separators=(",", ":"))
    payload_hash = hashlib.sha256(payload_json.encode()).hexdigest()
    idempotency_key = hashlib.sha256(idempotency_material.encode()).hexdigest()
    existing = await db.pool.fetchrow(
        """SELECT id, status FROM connector_jobs
           WHERE provider = $1 AND action = $2 AND idempotency_key = $3""",
        req.provider.lower(),
        req.action,
        idempotency_key,
    )
    if existing:
        return {"id": str(existing["id"]), "status": existing["status"], "idempotent": True}

    try:
        row = await db.pool.fetchrow(
            """INSERT INTO connector_jobs (provider, action, room_id, actor_id, payload, payload_hash, idempotency_key)
               VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7)
               RETURNING id, status""",
            req.provider.lower(),
            req.action,
            req.room_id,
            current_user.id,
            payload_json,
            payload_hash,
            idempotency_key,
        )
    except asyncpg.UniqueViolationError:
        existing = await db.pool.fetchrow(
            """SELECT id, status FROM connector_jobs
               WHERE provider = $1 AND action = $2 AND idempotency_key = $3""",
            req.provider.lower(),
            req.action,
            idempotency_key,
        )
        if existing:
            return {"id": str(existing["id"]), "status": existing["status"], "idempotent": True}
        raise
    queued = await enqueue_connector_job(str(row["id"]))
    if not queued:
        raise HTTPException(status_code=503, detail="Connector queue is full")
    await record_audit_event(
        action="connector.job_queued",
        actor_id=current_user.id,
        room_id=req.room_id,
        target_id=str(row["id"]),
        metadata={"provider": req.provider.lower(), "action": req.action, "payload_hash": payload_hash},
    )
    return {"id": str(row["id"]), "status": row["status"], "idempotent": False}
