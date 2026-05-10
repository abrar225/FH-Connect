from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json

from app.core.database import db
from app.core.event_bus import bus, Event
from app.core.constants import EventTypes
from app.core.ids import new_trace_id
from app.core.logging import get_logger
from app.core.auth import AuthUser, get_current_user
from app.core.permissions import Capability, require_capability
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


class ClarificationAction(BaseModel):
    id: str
    room_id: str
    title: Optional[str] = None
    assignee: Optional[str] = None
    deadline: Optional[str] = None

@router.get("/approval", response_model=List[DraftResponse])
async def list_pending_drafts(room_id: str, current_user: AuthUser = Depends(get_current_user)):
    """
    Lists task drafts in 'pending' status for a given room.
    """
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not connected")

    records = await db.pool.fetch(
        "SELECT * FROM task_drafts WHERE status = 'pending' AND room_id = $1 ORDER BY created_at DESC",
        room_id,
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
    Uses an atomic UPDATE ... RETURNING to prevent race conditions.
    """
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    await require_capability(current_user, Capability.TASK_APPROVE, {"room_id": action.room_id})

    # Atomic: only update if still 'pending', return the updated row
    if action.assignee:
        row = await db.pool.fetchrow(
            """UPDATE task_drafts SET status = 'approved', assignee = $2
               WHERE id = $1 AND room_id = $3 AND status = 'pending'
               RETURNING *""",
            action.id, action.assignee, action.room_id,
        )
    else:
        row = await db.pool.fetchrow(
            """UPDATE task_drafts SET status = 'approved'
               WHERE id = $1 AND room_id = $2 AND status = 'pending'
               RETURNING *""",
            action.id, action.room_id,
        )

    if not row:
        # Either draft doesn't exist or was already approved/rejected
        existing = await db.pool.fetchrow(
            "SELECT status FROM task_drafts WHERE id = $1 AND room_id = $2",
            action.id, action.room_id,
        )
        if not existing:
            raise HTTPException(status_code=404, detail="Draft not found")
        return {"status": "already_processed", "message": f"Draft {action.id} is already {existing['status']}."}

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

    await bus.emit(Event(
        event_type=EventTypes.DRAFT_APPROVED,
        trace_id=new_trace_id(),
        meeting_id=room_id,
        payload={"room_id": room_id, "broadcast_json": broadcast_json},
    ))
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
    Uses an atomic UPDATE ... RETURNING to prevent race conditions.
    """
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    await require_capability(current_user, Capability.TASK_APPROVE, {"room_id": action.room_id})

    # Atomic: only update if still 'pending', return the updated row
    row = await db.pool.fetchrow(
        """UPDATE task_drafts SET status = 'rejected'
           WHERE id = $1 AND room_id = $2 AND status = 'pending'
           RETURNING *""",
        action.id, action.room_id,
    )

    if not row:
        existing = await db.pool.fetchrow(
            "SELECT status FROM task_drafts WHERE id = $1 AND room_id = $2",
            action.id, action.room_id,
        )
        if not existing:
            raise HTTPException(status_code=404, detail="Draft not found")
        return {"status": "already_processed", "message": f"Draft {action.id} is already {existing['status']}."}

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

    await bus.emit(Event(
        event_type=EventTypes.DRAFT_REJECTED,
        trace_id=new_trace_id(),
        meeting_id=room_id,
        payload={"room_id": room_id, "broadcast_json": broadcast_json},
    ))
    await record_audit_event(
        action="draft.rejected",
        actor_id=current_user.id,
        room_id=room_id,
        target_id=action.id,
    )
    logger.info(f"Broadcasted REJECTION for draft {action.id} to room {room_id}")
        
    return {"status": "success", "message": f"Draft {action.id} rejected."}


@router.post("/approval/clarifications/accept")
async def accept_clarification(action: ClarificationAction, current_user: AuthUser = Depends(get_current_user)):
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    await require_capability(current_user, Capability.TASK_APPROVE, {"room_id": action.room_id})

    row = await db.pool.fetchrow(
        "SELECT * FROM intent_clarifications WHERE id = $1 AND room_id = $2 AND status = 'pending'",
        action.id,
        action.room_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Clarification not found")

    proposed_payload = row["proposed_payload"]
    if isinstance(proposed_payload, str):
        proposed_payload = json.loads(proposed_payload)
    if proposed_payload.get("action") != "CREATE":
        raise HTTPException(status_code=400, detail="Only create-task clarifications can be accepted")

    draft = {
        "id": new_trace_id(),
        "room_id": action.room_id,
        "original_transcript": row["source_transcript"],
        "title": action.title or proposed_payload.get("title") or "Untitled task",
        "assignee": action.assignee if action.assignee is not None else proposed_payload.get("assignee"),
        "deadline": action.deadline if action.deadline is not None else proposed_payload.get("deadline"),
        "status": "pending",
    }
    await db.pool.execute(
        """INSERT INTO task_drafts (id, room_id, original_transcript, title, assignee, deadline, status)
           VALUES ($1, $2, $3, $4, $5, $6, 'pending')""",
        draft["id"],
        draft["room_id"],
        draft["original_transcript"],
        draft["title"],
        draft["assignee"],
        draft["deadline"],
    )
    await db.pool.execute(
        """UPDATE intent_clarifications
           SET status = 'accepted', resolved_by = $2, resolved_at = timezone('utc'::text, now())
           WHERE id = $1""",
        action.id,
        current_user.id,
    )

    await bus.emit(Event(
        event_type=EventTypes.DRAFT_CREATED,
        trace_id=new_trace_id(),
        meeting_id=action.room_id,
        payload={"room_id": action.room_id, "draft_json": json.dumps(draft)},
    ))
    await bus.emit(Event(
        event_type=EventTypes.DRAFT_APPROVED,
        trace_id=new_trace_id(),
        meeting_id=action.room_id,
        payload={"room_id": action.room_id, "broadcast_json": json.dumps({
            "type": "clarification_status",
            "room_id": action.room_id,
            "id": action.id,
            "status": "accepted",
        })},
    ))
    await record_audit_event(
        action="intent_clarification.accepted",
        actor_id=current_user.id,
        room_id=action.room_id,
        target_id=action.id,
        metadata={"draft_id": draft["id"]},
    )
    return {"status": "success", "draft": draft}


@router.post("/approval/clarifications/reject")
async def reject_clarification(action: ClarificationAction, current_user: AuthUser = Depends(get_current_user)):
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not connected")
    await require_capability(current_user, Capability.TASK_APPROVE, {"room_id": action.room_id})

    result = await db.pool.execute(
        """UPDATE intent_clarifications
           SET status = 'rejected', resolved_by = $3, resolved_at = timezone('utc'::text, now())
           WHERE id = $1 AND room_id = $2 AND status = 'pending'""",
        action.id,
        action.room_id,
        current_user.id,
    )
    if result.endswith("0"):
        raise HTTPException(status_code=404, detail="Clarification not found")

    await bus.emit(Event(
        event_type=EventTypes.DRAFT_REJECTED,
        trace_id=new_trace_id(),
        meeting_id=action.room_id,
        payload={"room_id": action.room_id, "broadcast_json": json.dumps({
            "type": "clarification_status",
            "room_id": action.room_id,
            "id": action.id,
            "status": "rejected",
        })},
    ))
    await record_audit_event(
        action="intent_clarification.rejected",
        actor_id=current_user.id,
        room_id=action.room_id,
        target_id=action.id,
    )
    return {"status": "success"}
