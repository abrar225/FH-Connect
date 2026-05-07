from fastapi import APIRouter, HTTPException
from app.core.database import db
from app.core.config import settings
from app.workers.queue import intent_queue_metrics
from app.workers.report_queue import report_queue_metrics

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/queues")
async def queue_health():
    return {
        "intent": await intent_queue_metrics(),
        "report": await report_queue_metrics(),
    }


@router.get("/debug/meeting/{room_id}")
async def debug_meeting(room_id: str):
    """Temporary diagnostic endpoint - remove in production"""
    if settings.ENVIRONMENT == "production":
        raise HTTPException(status_code=404, detail="Not found")
    if not db.pool:
        return {"error": "Database not connected"}
    async with db.pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT room_id, created_by, admins, is_locked FROM meetings WHERE room_id = $1",
            room_id
        )
        if not row:
            return {"error": "Meeting not found"}
        return dict(row)
