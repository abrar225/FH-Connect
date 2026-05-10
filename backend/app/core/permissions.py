from enum import StrEnum
from typing import Any, Mapping

from fastapi import HTTPException

from app.core.auth import AuthUser
from app.core.database import db
from app.modules.audit.repository import record_audit_event
from app.modules.meeting.repository import get_meeting


class Capability(StrEnum):
    MEETING_JOIN = "meeting.join"
    MEETING_ADMIN = "meeting.admin"
    TASK_APPROVE = "task.approve"
    REPORT_READ = "report.read"
    REPORT_SHARE = "report.share"
    CONNECTOR_CONFIGURE = "connector.configure"
    CONNECTOR_EXECUTE = "connector.execute"


async def require_database() -> None:
    if not db.pool:
        raise HTTPException(status_code=503, detail="Database not configured")


async def _meeting_for_resource(resource: Mapping[str, Any]) -> dict:
    await require_database()
    room_id = str(resource.get("room_id") or "")
    if not room_id:
        raise HTTPException(status_code=400, detail="room_id is required")
    meeting = await get_meeting(room_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return meeting


async def _deny(user: AuthUser, capability: Capability, resource: Mapping[str, Any], detail: str = "Permission denied") -> None:
    try:
        await record_audit_event(
            action="permission.denied",
            actor_id=user.id,
            room_id=resource.get("room_id"),
            metadata={"capability": capability.value, "detail": detail},
        )
    except Exception:
        pass
    raise HTTPException(status_code=403, detail=detail)


async def require_capability(user: AuthUser, capability: Capability, resource: Mapping[str, Any]) -> dict | None:
    meeting_capabilities = {
        Capability.MEETING_JOIN,
        Capability.MEETING_ADMIN,
        Capability.TASK_APPROVE,
        Capability.REPORT_READ,
        Capability.REPORT_SHARE,
        Capability.CONNECTOR_EXECUTE,
    }
    meeting = await _meeting_for_resource(resource) if capability in meeting_capabilities else None

    admins = meeting.get("admins") if meeting else []
    admins = admins or []
    is_admin = bool(meeting and (user.id in admins or meeting.get("created_by") == user.id))

    if capability == Capability.MEETING_JOIN:
        if meeting and meeting.get("is_locked") and not is_admin:
            await _deny(user, capability, resource, "Meeting is locked")
        return meeting

    if capability in {
        Capability.MEETING_ADMIN,
        Capability.TASK_APPROVE,
        Capability.REPORT_READ,
        Capability.REPORT_SHARE,
        Capability.CONNECTOR_EXECUTE,
    }:
        if not is_admin:
            await _deny(user, capability, resource, "Admin access required")
        return meeting

    if capability == Capability.CONNECTOR_CONFIGURE:
        await require_database()
        return None

    await _deny(user, capability, resource)
    return None
