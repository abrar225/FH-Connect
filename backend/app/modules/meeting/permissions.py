from app.core.auth import AuthUser
from app.core.database import db
from app.core.permissions import require_database
from app.modules.meeting.repository import get_meeting
from fastapi import HTTPException


async def require_admin(room_id: str, user: AuthUser) -> dict:
    await require_database()
    meeting = await get_meeting(room_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    admins = meeting.get("admins") or []
    if user.id not in admins and meeting.get("created_by") != user.id:
        raise HTTPException(status_code=403, detail="Admin access required")
    return meeting
