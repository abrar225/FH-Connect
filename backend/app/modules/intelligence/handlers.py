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
from app.core.config import settings
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
