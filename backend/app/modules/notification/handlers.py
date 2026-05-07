"""
modules/notification/handlers.py — Event handlers for the Notification domain.

Listens to: draft.created, draft.updated, draft.cancelled
Does:       Converts internal events into frontend-safe WS payloads
            and broadcasts to the relevant room via the WebSocket manager.

This module is the ONLY module that touches the WebSocket manager for
business-related broadcasts. This enforces Rule 1 (WS layer has zero
business logic) and Rule 6 (feature removal is safe — if you remove
the notification module, broadcasts simply stop; nothing crashes).
"""

from app.core.event_bus import bus, Event
from app.core.constants import EventTypes
from app.core.logging import get_logger

logger = get_logger("notification.handler")


@bus.on(EventTypes.TRANSCRIPT_RECEIVED)
async def handle_transcript_received_broadcast(event: Event):
    """Broadcast raw transcripts (interim and final) to all room participants so they see live captions."""
    from app.gateway.ws.manager import manager
    import json

    room_id = event.payload["room_id"]
    broadcast_json = json.dumps({
        "type": "transcript",
        "id": event.payload.get("id"),
        "text": event.payload["text"],
        "speaker": event.payload["speaker"],
        "is_final": event.payload.get("is_final", True),
        "timestamp": event.payload.get("timestamp")
    })

    await manager.broadcast(room_id, broadcast_json)

@bus.on(EventTypes.DRAFT_CREATED)
async def handle_draft_created(event: Event):
    """Broadcast a newly created draft to all room participants."""
    from app.gateway.ws.manager import manager

    room_id = event.payload["room_id"]
    draft_json = event.payload["draft_json"]

    await manager.broadcast(room_id, draft_json)
    logger.info(f"Broadcasted DRAFT_CREATED to room {room_id} [trace={event.trace_id[:8]}]")


@bus.on(EventTypes.DRAFT_UPDATED)
async def handle_draft_updated(event: Event):
    """Broadcast an updated draft to all room participants."""
    from app.gateway.ws.manager import manager

    room_id = event.payload["room_id"]
    draft_json = event.payload["draft_json"]

    await manager.broadcast(room_id, draft_json)
    logger.info(f"Broadcasted DRAFT_UPDATED to room {room_id} [trace={event.trace_id[:8]}]")


@bus.on(EventTypes.DRAFT_CANCELLED)
async def handle_draft_cancelled(event: Event):
    """Broadcast a draft cancellation to all room participants."""
    from app.gateway.ws.manager import manager

    room_id = event.payload["room_id"]
    cancel_json = event.payload["draft_json"]

    await manager.broadcast(room_id, cancel_json)
    logger.info(f"Broadcasted DRAFT_CANCELLED to room {room_id} [trace={event.trace_id[:8]}]")


@bus.on(EventTypes.PULSE_GENERATED)
async def handle_pulse_generated(event: Event):
    """Broadcast a meeting pulse update to all room participants."""
    from app.gateway.ws.manager import manager

    room_id = event.payload["room_id"]
    pulse_json = event.payload["pulse_json"]

    manager.set_latest_pulse(room_id, pulse_json)
    await manager.broadcast(room_id, pulse_json)
    logger.info(f"Broadcasted PULSE to room {room_id} [trace={event.trace_id[:8]}]")


# ── Meeting Admin Broadcasts ──────────────────────────────────────────────────

@bus.on(EventTypes.MEETING_LOCK_UPDATED)
async def handle_meeting_lock_updated(event: Event):
    """Broadcast a room lock state change to all participants."""
    from app.gateway.ws.manager import manager

    room_id = event.payload["room_id"]
    broadcast_json = event.payload["broadcast_json"]

    await manager.broadcast(room_id, broadcast_json)
    logger.info(f"Broadcasted LOCK_UPDATE to room {room_id} [trace={event.trace_id[:8]}]")


@bus.on(EventTypes.MEETING_ADMIN_UPDATED)
async def handle_meeting_admin_updated(event: Event):
    """Broadcast an admin roster change to all participants."""
    from app.gateway.ws.manager import manager

    room_id = event.payload["room_id"]
    broadcast_json = event.payload["broadcast_json"]

    await manager.broadcast(room_id, broadcast_json)
    logger.info(f"Broadcasted ADMIN_UPDATE to room {room_id} [trace={event.trace_id[:8]}]")


@bus.on(EventTypes.AGENDA_UPDATED)
async def handle_agenda_updated(event: Event):
    from app.gateway.ws.manager import manager
    import json

    await manager.broadcast(event.payload["room_id"], json.dumps({
        "type": "agenda_updated",
        "agenda": event.payload["agenda"],
    }, default=str))


@bus.on(EventTypes.INSIGHT_CREATED)
async def handle_insight_created(event: Event):
    from app.gateway.ws.manager import manager
    import json

    await manager.broadcast(event.payload["room_id"], json.dumps({
        "type": "insight_created",
        "insight": event.payload["insight"],
    }, default=str))


@bus.on(EventTypes.INSIGHT_UPDATED)
async def handle_insight_updated(event: Event):
    from app.gateway.ws.manager import manager
    import json

    await manager.broadcast(event.payload["room_id"], json.dumps({
        "type": "insight_updated",
        "insight": event.payload["insight"],
    }, default=str))


@bus.on(EventTypes.QUALITY_SCORE_UPDATED)
async def handle_quality_score_updated(event: Event):
    from app.gateway.ws.manager import manager
    import json

    await manager.broadcast(event.payload["room_id"], json.dumps({
        "type": "quality_score_updated",
        "quality_score": event.payload["quality_score"],
    }, default=str))


@bus.on(EventTypes.REPORT_STATUS_UPDATED)
async def handle_report_status_updated(event: Event):
    from app.gateway.ws.manager import manager
    import json

    await manager.broadcast(event.payload["room_id"], json.dumps({
        "type": "report_status",
        "status": event.payload["status"],
        "error": event.payload.get("error"),
    }, default=str))
