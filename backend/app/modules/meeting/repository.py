from typing import Any, Dict, List, Optional

from app.core.database import db


async def get_meeting(room_id: str) -> Optional[Dict[str, Any]]:
    if not db.pool:
        return None
    row = await db.pool.fetchrow(
        """SELECT room_id, created_by, admins, is_locked, report_status, report_error,
                  report_requested_at, ended_at, report_content
           FROM meetings WHERE room_id = $1""",
        room_id,
    )
    return dict(row) if row else None


async def create_meeting_record(room_id: str, created_by: str, title: str) -> Dict[str, Any]:
    if not db.pool:
        raise RuntimeError("Database not configured")

    async with db.pool.acquire() as conn:
        existing = await conn.fetchrow("SELECT room_id, created_by, admins, is_locked FROM meetings WHERE room_id = $1", room_id)
        if existing:
            return {"status": "exists", **dict(existing)}

        admins = [created_by]
        await conn.execute(
            """INSERT INTO meetings (room_id, created_by, title, admins, started_at, is_locked)
               VALUES ($1, $2, $3, $4, NOW(), false)""",
            room_id,
            created_by,
            title,
            admins,
        )
        return {
            "status": "created",
            "room_id": room_id,
            "created_by": created_by,
            "admins": admins,
            "is_locked": False,
        }


async def set_room_lock(room_id: str, locked: bool) -> None:
    await db.pool.execute("UPDATE meetings SET is_locked = $1 WHERE room_id = $2", locked, room_id)


async def set_admins(room_id: str, admins: List[str]) -> None:
    await db.pool.execute("UPDATE meetings SET admins = $1 WHERE room_id = $2", admins, room_id)


async def save_meeting_report(room_id: str, report_json: str) -> None:
    await db.pool.execute(
        """UPDATE meetings
           SET report_content = $1,
               report_status = 'completed',
               report_error = NULL,
               ended_at = timezone('utc'::text, now())
           WHERE room_id = $2""",
        report_json,
        room_id,
    )


async def set_report_status(room_id: str, status: str, error: Optional[str] = None) -> None:
    if status == "queued":
        await db.pool.execute(
            """UPDATE meetings
               SET report_status = $1,
                   report_error = NULL,
                   report_requested_at = timezone('utc'::text, now())
               WHERE room_id = $2""",
            status,
            room_id,
        )
        return

    await db.pool.execute(
        "UPDATE meetings SET report_status = $1, report_error = $2 WHERE room_id = $3",
        status,
        error,
        room_id,
    )


async def get_report_status(room_id: str) -> Optional[Dict[str, Any]]:
    if not db.pool:
        return None
    row = await db.pool.fetchrow(
        """SELECT room_id, report_status, report_error, report_requested_at, ended_at,
                  report_content IS NOT NULL AS has_report
           FROM meetings WHERE room_id = $1""",
        room_id,
    )
    return dict(row) if row else None
