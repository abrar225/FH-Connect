"""
modules/intelligence/handlers.py — Event handlers for the Intelligence domain.

Listens to: intent.requested (from Transcript module)
Emits:      intent.detected  → Draft module picks it up
            intent.rejected  → logged and dropped

This handler performs:
  1. Calls the LLM-based intent detection chain
  2. Applies confidence filtering
  3. Runs the rules engine to produce an action + payload
  4. Emits intent.detected with the structured result
"""

from app.core.event_bus import bus, Event
from app.core.constants import EventTypes
from app.core.database import db
from app.core.logging import get_logger

logger = get_logger("intelligence.handler")


@bus.on(EventTypes.INTENT_REQUESTED)
async def handle_intent_requested(event: Event):
    """
    Enqueues the intent request to the background worker.
    This moves the heavy LLM call off the critical path (Phase 3).
    """
    from app.workers.queue import enqueue_intent_event

    logger.info(
        f"Intent requested → enqueueing to worker "
        f"[trace={event.trace_id[:8]}, room={event.meeting_id}]"
    )

    try:
        queued = await enqueue_intent_event(event)
        if queued:
            return
        logger.warning(
            f"Backpressure applied: Intent queue full. Dropping intent request "
            f"[trace={event.trace_id[:8]}, room={event.meeting_id}]"
        )
    except Exception as exc:
        logger.error("Failed to enqueue intent request", exc_info=exc)


@bus.on(EventTypes.INTENT_CLARIFICATION_REQUIRED)
async def handle_intent_clarification_required(event: Event):
    import json

    payload = event.payload
    if not db.pool:
        return
    await db.pool.execute(
        """INSERT INTO intent_clarifications
           (room_id, source_transcript, proposed_action, proposed_payload, confidence, requested_by)
           VALUES ($1, $2, $3, $4::jsonb, $5, $6)""",
        payload["room_id"],
        payload["text"],
        payload.get("proposed_action") or "NONE",
        json.dumps(payload.get("proposed_payload") or {}),
        payload.get("confidence") or 0,
        payload.get("user_id"),
    )
