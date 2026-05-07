from fastapi import HTTPException

from app.core.auth import AuthUser
from app.core.database import db
from app.modules.meeting.repository import get_meeting


async def require_database() -> None:
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not configured")


async def require_admin(room_id: str, user: AuthUser) -> dict:
    await require_database()
    meeting = await get_meeting(room_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")

    admins = meeting.get("admins") or []
    if user.id not in admins:
        raise HTTPException(status_code=403, detail="Admin access required")

    return meeting
