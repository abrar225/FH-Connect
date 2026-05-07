import asyncio

from app.workers.queue import (
    ack_intent_event,
    complete_intent_event,
    dequeue_intent_event,
    fail_intent_event,
    should_process_intent_event,
)
from app.core.event_bus import bus, Event
from app.core.constants import EventTypes
from app.core.logging import get_logger

logger = get_logger("intent_worker")

async def process_intent_task(event: Event):
    """
    Background task logic to detect intent.
    This was moved from intelligence.handlers to run off the critical path.
    """
    from app.modules.intelligence.intent_llm import detect_intent
    from app.modules.draft.rules import process_intent

    payload = event.payload
    text = payload["text"]
    speaker = payload["speaker"]
    room_id = payload["room_id"]
    user_id = payload.get("user_id")
    active_users = payload.get("active_users", [])
    active_drafts = payload.get("active_drafts", [])

    MAX_RETRIES = 2
    for attempt in range(MAX_RETRIES):
        try:
            # Step 1: LLM intent detection (This takes time, hence the background worker)
            intent_result = await detect_intent(text, speaker, active_drafts, active_users, user_id=user_id)

            # Step 2: Rules engine
            action, data = process_intent(intent_result, text, room_id)
            break
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                logger.error(
                    f"Intent detection failed after {MAX_RETRIES} attempts: {e} "
                    f"[trace={event.trace_id[:8]}, room={room_id}]"
                )
                await bus.emit(Event(
                    event_type=EventTypes.INTENT_REJECTED,
                    trace_id=event.trace_id,
                    meeting_id=room_id,
                    payload={"reason": "llm_error", "error": str(e), "text": text},
                ))
                return
            logger.warning(f"Intent detection retry {attempt + 1}/{MAX_RETRIES} for [trace={event.trace_id[:8]}]")
            await asyncio.sleep(1) # simple backoff

    if not action:
        logger.debug(
            f"Intent rejected (low confidence or no action) "
            f"[trace={event.trace_id[:8]}, room={room_id}]"
        )
        await bus.emit(Event(
            event_type=EventTypes.INTENT_REJECTED,
            trace_id=event.trace_id,
            meeting_id=room_id,
            payload={"reason": "low_confidence_or_none", "text": text},
        ))
        return

    logger.info(
        f"Intent detected: {action} "
        f"[trace={event.trace_id[:8]}, room={room_id}]"
    )

    # Step 3: Emit intent.detected for Draft module
    if action == "CREATE":
        intent_payload = {
            "action": action,
            "draft_id": data.id,
            "room_id": data.room_id,
            "original_transcript": data.original_transcript,
            "title": data.title,
            "assignee": data.assignee,
            "deadline": data.deadline,
            "status": data.status,
        }
    else:
        # UPDATE or CANCEL
        intent_payload = {
            "action": action,
            "room_id": room_id,
            "original_transcript": text,
            "title": getattr(data, "title", None),
            "assignee": getattr(data, "assignee", None),
            "deadline": getattr(data, "deadline", None),
            "target_task_id": getattr(data, "target_task_id", None),
            "active_drafts": active_drafts,
        }

    await bus.emit(Event(
        event_type=EventTypes.INTENT_DETECTED,
        trace_id=event.trace_id,
        meeting_id=room_id,
        payload=intent_payload,
    ))


async def start_intent_worker():
    """
    Infinite loop that consumes tasks from the task_queue.
    """
    logger.info("Intent worker started, waiting for tasks...")
    while True:
        event = None
        stream_id = None
        try:
            event, stream_id = await dequeue_intent_event()
            if event is None:
                continue
            if not await should_process_intent_event(event):
                await ack_intent_event(stream_id)
                continue
            
            logger.info(f"Worker picked up intent task [trace={event.trace_id[:8]}]")
            await process_intent_task(event)
            await complete_intent_event(event, stream_id)
        except asyncio.CancelledError:
            logger.info("Intent worker cancelled.")
            break
        except Exception as e:
            logger.error(f"Error in intent worker loop: {e}", exc_info=True)
            try:
                await fail_intent_event(event, stream_id)
            except Exception:
                logger.error("Failed to mark intent task as failed", exc_info=True)
