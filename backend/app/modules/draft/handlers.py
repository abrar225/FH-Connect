"""
modules/draft/handlers.py — Event handlers for the Draft domain.

Listens to: intent.detected (from Intelligence module)
Emits:      draft.created / draft.updated / draft.cancelled
            → Notification module picks these up for broadcasting

This handler performs:
  1. Receives structured intent results
  2. For UPDATE/CANCEL without a target_task_id, performs fuzzy matching
  3. Persists the draft change to the database
  4. Emits broadcast events for the Notification module
"""

import json
from difflib import SequenceMatcher

from app.core.event_bus import bus, Event
from app.core.constants import EventTypes
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("draft.handler")


@bus.on(EventTypes.INTENT_DETECTED)
async def handle_intent_detected(event: Event):
    """
    Processes a detected intent into a draft database operation.
    Replaces the stateful correction logic + DB writes that were
    previously inlined in the /transcript API endpoint.
    """
    from app.core.database import db
    from app.modules.draft.models import TaskDraft

    if not db.pool:
        logger.warning(f"DB unavailable, dropping intent [trace={event.trace_id[:8]}]")
        return

    payload = event.payload
    action = payload["action"]
    room_id = payload["room_id"]

    # ── CREATE ────────────────────────────────────────────────────────────
    if action == "CREATE":
        draft = TaskDraft(
            id=payload.get("draft_id"),
            room_id=room_id,
            original_transcript=payload.get("original_transcript", ""),
            title=payload["title"],
            assignee=payload.get("assignee"),
            deadline=payload.get("deadline"),
            status=payload.get("status", "pending"),
        )

        await db.pool.execute(
            """
            INSERT INTO task_drafts (id, room_id, original_transcript, title, assignee, deadline, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            draft.id, draft.room_id, draft.original_transcript,
            draft.title, draft.assignee, draft.deadline, draft.status,
        )

        logger.info(f"Draft created: '{draft.title}' [id={draft.id[:8]}, trace={event.trace_id[:8]}]")

        await bus.emit(Event(
            event_type=EventTypes.DRAFT_CREATED,
            trace_id=event.trace_id,
            meeting_id=room_id,
            payload={"room_id": room_id, "draft_json": draft.model_dump_json()},
        ))
        return

    # ── UPDATE / CANCEL — resolve target_task_id if missing ───────────────
    target_task_id = payload.get("target_task_id")
    active_drafts = payload.get("active_drafts", [])
    title = payload.get("title")

    if not target_task_id:
        # Fuzzy match against active drafts
        best_match_id = None
        highest_ratio = settings.FUZZY_MATCH_THRESHOLD

        for draft in active_drafts:
            ratio = SequenceMatcher(None, title or "", draft.get("title", "")).ratio()
            if ratio > highest_ratio:
                highest_ratio = ratio
                best_match_id = draft["id"]

        if best_match_id:
            target_task_id = best_match_id
            logger.info(f"Fuzzy matched target: {best_match_id} (ratio={highest_ratio:.2f})")
        else:
            # Downgrade UPDATE → CREATE if we have enough info
            if action == "UPDATE" and title:
                logger.info(f"No fuzzy match, downgrading UPDATE → CREATE [trace={event.trace_id[:8]}]")
                draft = TaskDraft(
                    room_id=room_id,
                    original_transcript=payload.get("original_transcript", ""),
                    title=title,
                    assignee=payload.get("assignee"),
                    deadline=payload.get("deadline"),
                )
                await db.pool.execute(
                    """
                    INSERT INTO task_drafts (id, room_id, original_transcript, title, assignee, deadline, status)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    draft.id, draft.room_id, draft.original_transcript,
                    draft.title, draft.assignee, draft.deadline, draft.status,
                )
                await bus.emit(Event(
                    event_type=EventTypes.DRAFT_CREATED,
                    trace_id=event.trace_id,
                    meeting_id=room_id,
                    payload={"room_id": room_id, "draft_json": draft.model_dump_json()},
                ))
                return
            else:
                logger.debug(f"No target found for {action}, dropping [trace={event.trace_id[:8]}]")
                return

    # ── UPDATE ────────────────────────────────────────────────────────────
    if action == "UPDATE":
        await db.pool.execute(
            """
            UPDATE task_drafts
            SET title = COALESCE($1, title),
                assignee = COALESCE($2, assignee),
                deadline = COALESCE($3, deadline)
            WHERE id = $4 AND room_id = $5 AND status = 'pending'
            """,
            title, payload.get("assignee"), payload.get("deadline"),
            target_task_id, room_id,
        )

        row = await db.pool.fetchrow(
            "SELECT * FROM task_drafts WHERE id = $1 AND room_id = $2",
            target_task_id, room_id,
        )
        if row:
            updated_draft = TaskDraft(**dict(row))
            logger.info(f"Draft updated: {target_task_id[:8]} [trace={event.trace_id[:8]}]")
            await bus.emit(Event(
                event_type=EventTypes.DRAFT_UPDATED,
                trace_id=event.trace_id,
                meeting_id=room_id,
                payload={"room_id": room_id, "draft_json": updated_draft.model_dump_json()},
            ))
        return

    # ── CANCEL ────────────────────────────────────────────────────────────
    if action == "CANCEL":
        await db.pool.execute(
            "DELETE FROM task_drafts WHERE id = $1 AND room_id = $2 AND status = 'pending'",
            target_task_id, room_id,
        )
        logger.info(f"Draft cancelled: {target_task_id[:8]} [trace={event.trace_id[:8]}]")
        await bus.emit(Event(
            event_type=EventTypes.DRAFT_CANCELLED,
            trace_id=event.trace_id,
            meeting_id=room_id,
            payload={
                "room_id": room_id,
                "draft_json": json.dumps({"id": target_task_id, "action": "CANCEL"}),
            },
        ))
