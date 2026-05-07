import json
from typing import Any, Dict, Optional

from app.core.database import db
from app.core.logging import get_logger

logger = get_logger("audit.repository")


async def record_audit_event(
    *,
    action: str,
    actor_id: str,
    room_id: Optional[str] = None,
    target_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    if not db.pool:
        logger.debug(f"Audit skipped without DB [action={action}, actor={actor_id}]")
        return

    try:
        await db.pool.execute(
            """
            INSERT INTO audit_logs (action, actor_id, room_id, target_id, metadata)
            VALUES ($1, $2, $3, $4, $5::jsonb)
            """,
            action,
            actor_id,
            room_id,
            target_id,
            json.dumps(metadata or {}),
        )
    except Exception as exc:
        logger.error(f"Failed to write audit event [action={action}]", exc_info=exc)
