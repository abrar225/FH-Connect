"""
modules/transcript/handlers.py — Event handlers for the Transcript domain.

Listens to: transcript.received (from the Gateway)
Emits:      transcript.validated → intent.requested

This handler performs:
  1. Basic validation (non-empty text, has room_id)
  2. RBAC check (is the speaker an admin?)
  3. Emits intent.requested for the Intelligence module to pick up
"""

from app.core.event_bus import bus, Event
from app.core.constants import EventTypes
from app.core.logging import get_logger
from app.modules.intelligence.intent_preprocessor import detect_deterministic_intent

logger = get_logger("transcript.handler")


@bus.on(EventTypes.TRANSCRIPT_RECEIVED)
async def handle_transcript_received(event: Event):
    """
    Validates an incoming transcript chunk and forwards it for intent detection.
    This handler replaces the validation logic that was previously
    inlined in the /transcript API endpoint.
    """
    from app.core.database import db

    payload = event.payload
    text = payload.get("text", "").strip()
    speaker = payload.get("speaker", "Unknown")
    user_id = payload.get("user_id", "")
    room_id = payload.get("room_id", "")
    active_users = payload.get("active_users", [])

    # ── Step 1: Basic validation ──────────────────────────────────────────
    if not text or not room_id or not user_id:
        logger.debug(f"Transcript dropped: missing fields [trace={event.trace_id[:8]}]")
        return

    if payload.get("is_final", True):
        try:
            from app.modules.productivity.service import persist_transcript_and_insights
            await persist_transcript_and_insights(payload, user_id)
        except Exception as exc:
            logger.error("Failed to persist transcript productivity data", exc_info=exc)

    # ── Step 2: RBAC — only admins can generate tasks ─────────────────────
    if db.pool:
        meeting_record = await db.pool.fetchrow(
            "SELECT admins FROM meetings WHERE room_id = $1",
            room_id,
        )
        admins = meeting_record["admins"] if meeting_record and meeting_record["admins"] else []
        if admins and user_id not in admins:
            suggestion = detect_deterministic_intent(text, speaker, active_users=active_users)
            if suggestion and payload.get("is_final", True):
                await bus.emit(Event(
                    event_type=EventTypes.INTENT_CLARIFICATION_REQUIRED,
                    trace_id=event.trace_id,
                    meeting_id=room_id,
                    payload={
                        "room_id": room_id,
                        "text": text,
                        "speaker": speaker,
                        "user_id": user_id,
                        "proposed_action": suggestion.intent.action,
                        "proposed_payload": suggestion.intent.model_dump(),
                        "confidence": min(suggestion.intent.confidence, 0.84),
                        "status": "participant_suggestion",
                    },
                ))
            logger.debug(f"Transcript accepted from non-admin participant without executable task intent [trace={event.trace_id[:8]}]")
            return

    # ── Step 3: Fetch active drafts for context ───────────────────────────
    active_drafts = []
    if db.pool:
        rows = await db.pool.fetch(
            "SELECT id, title, assignee FROM task_drafts WHERE status = 'pending' AND room_id = $1",
            room_id,
        )
        active_drafts = [dict(r) for r in rows]

    logger.info(
        f"Transcript validated → requesting intent  "
        f"[room={room_id}, speaker={speaker}, trace={event.trace_id[:8]}]"
    )

    # ── Step 4: Emit validated event for the Intelligence module ───────────
    # We only request AI processing for final sentences!
    is_final = payload.get("is_final", True)
    if is_final:
        await bus.emit(Event(
            event_type=EventTypes.INTENT_REQUESTED,
            trace_id=event.trace_id,
            meeting_id=room_id,
            payload={
                "text": text,
                "speaker": speaker,
                "user_id": user_id,
                "room_id": room_id,
                "active_users": active_users,
                "active_drafts": active_drafts,
            },
        ))
