from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json

from app.core.database import db
from app.core.event_bus import bus, Event
from app.core.ids import new_trace_id
from app.core.logging import get_logger
from app.core.auth import AuthUser, get_current_user, require_meeting_admin
from app.modules.audit.repository import record_audit_event

router = APIRouter()
logger = get_logger("approval.service")

class DraftResponse(BaseModel):
    id: str
    room_id: str
    original_transcript: str
    title: str
    assignee: Optional[str] = None
    deadline: Optional[str] = None
    status: str

class ApprovalAction(BaseModel):
    id: str
    room_id: str
    assignee: Optional[str] = None

@router.get("/approval", response_model=List[DraftResponse])
async def list_pending_drafts(room_id: Optional[str] = None, current_user: AuthUser = Depends(get_current_user)):
    """
    Lists task drafts in 'pending' status, optionally filtered by room_id.
    """
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    if not room_id:
        raise HTTPException(status_code=400, detail="room_id is required")
    
    if room_id:
        records = await db.pool.fetch(
            "SELECT * FROM task_drafts WHERE status = 'pending' AND room_id = $1 ORDER BY created_at DESC",
            room_id
        )
    else:
        records = await db.pool.fetch(
            "SELECT * FROM task_drafts WHERE status = 'pending' ORDER BY created_at DESC"
        )
        
    return [
        DraftResponse(
            id=str(r["id"]),
            room_id=r["room_id"],
            original_transcript=r["original_transcript"],
            title=r["title"],
            assignee=r["assignee"],
            deadline=r["deadline"],
            status=r["status"]
        ) for r in records
    ]

@router.post("/approval/approve")
async def approve_draft(action: ApprovalAction, current_user: AuthUser = Depends(get_current_user)):
    """
    Approves a draft by updating its status to 'approved'.
    Broadcasts the status change to ALL participants in the room via WebSocket.
    """
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    await require_meeting_admin(action.room_id, current_user)
        
    if action.assignee:
        await db.pool.execute(
            "UPDATE task_drafts SET status = 'approved', assignee = $2 WHERE id = $1 AND room_id = $3",
            action.id, 
            action.assignee,
            action.room_id,
        )
    else:
        await db.pool.execute(
            "UPDATE task_drafts SET status = 'approved' WHERE id = $1 AND room_id = $2",
            action.id,
            action.room_id,
        )

    # Fetch the updated draft to get room_id and full data for broadcast
    row = await db.pool.fetchrow("SELECT * FROM task_drafts WHERE id = $1 AND room_id = $2", action.id, action.room_id)
    if not row:
        raise HTTPException(status_code=404, detail="Draft not found")

    # Broadcast the approval to ALL participants in the room
    room_id = row["room_id"]
    broadcast_json = json.dumps({
        "type": "draft_status",
        "id": str(row["id"]),
        "room_id": room_id,
        "title": row["title"],
        "assignee": row["assignee"],
        "deadline": row["deadline"],
        "status": "approved",
        "original_transcript": row["original_transcript"],
    })

    from app.gateway.ws.manager import manager
    await manager.broadcast(room_id, broadcast_json)
    await record_audit_event(
        action="draft.approved",
        actor_id=current_user.id,
        room_id=room_id,
        target_id=action.id,
        metadata={"assignee": row["assignee"]},
    )
    logger.info(f"Broadcasted APPROVAL for draft {action.id} to room {room_id}")
        
    return {"status": "success", "message": f"Draft {action.id} approved."}

@router.post("/approval/reject")
async def reject_draft(action: ApprovalAction, current_user: AuthUser = Depends(get_current_user)):
    """
    Rejects a draft by updating its status to 'rejected'.
    Broadcasts the status change to ALL participants in the room via WebSocket.
    """
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    await require_meeting_admin(action.room_id, current_user)

    # Fetch the draft BEFORE rejecting to get room_id
    row = await db.pool.fetchrow("SELECT * FROM task_drafts WHERE id = $1 AND room_id = $2", action.id, action.room_id)
    if not row:
        raise HTTPException(status_code=404, detail="Draft not found")

    await db.pool.execute("UPDATE task_drafts SET status = 'rejected' WHERE id = $1 AND room_id = $2", action.id, action.room_id)

    # Broadcast the rejection to ALL participants in the room
    room_id = row["room_id"]
    broadcast_json = json.dumps({
        "type": "draft_status",
        "id": str(row["id"]),
        "room_id": room_id,
        "title": row["title"],
        "assignee": row["assignee"],
        "deadline": row["deadline"],
        "status": "rejected",
        "original_transcript": row["original_transcript"],
    })

    from app.gateway.ws.manager import manager
    await manager.broadcast(room_id, broadcast_json)
    await record_audit_event(
        action="draft.rejected",
        actor_id=current_user.id,
        room_id=room_id,
        target_id=action.id,
    )
    logger.info(f"Broadcasted REJECTION for draft {action.id} to room {room_id}")
        
    return {"status": "success", "message": f"Draft {action.id} rejected."}
