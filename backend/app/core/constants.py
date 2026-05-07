"""
core/constants.py — Event type constants.

All event type strings are defined here as constants.
This prevents typos and gives a single reference for all event types
flowing through the Event Bus.
"""


class EventTypes:
    """Standard event type constants used across all modules."""

    # ── Transcript Domain ─────────────────────────────────────────────────
    TRANSCRIPT_RECEIVED = "transcript.received"
    TRANSCRIPT_VALIDATED = "transcript.validated"

    # ── Intelligence Domain ───────────────────────────────────────────────
    INTENT_REQUESTED = "intent.requested"
    INTENT_DETECTED = "intent.detected"
    INTENT_REJECTED = "intent.rejected"

    # ── Draft Domain ──────────────────────────────────────────────────────
    DRAFT_CREATED = "draft.created"
    DRAFT_UPDATED = "draft.updated"
    DRAFT_CANCELLED = "draft.cancelled"

    # ── Approval Domain ───────────────────────────────────────────────────
    DRAFT_APPROVED = "draft.approved"
    DRAFT_REJECTED = "draft.rejected"

    # ── Notification Domain ───────────────────────────────────────────────
    DRAFT_BROADCAST_REQUESTED = "draft.broadcast.requested"

    # ── Meeting Domain ────────────────────────────────────────────────────
    MEETING_CREATED = "meeting.created"
    MEETING_LOCKED = "meeting.locked"
    MEETING_LOCK_UPDATED = "meeting.lock_updated"
    MEETING_ADMIN_UPDATED = "meeting.admin_updated"
    MEETING_ENDED = "meeting.ended"
    AGENDA_UPDATED = "agenda.updated"
    INSIGHT_CREATED = "insight.created"
    INSIGHT_UPDATED = "insight.updated"
    REPORT_STATUS_UPDATED = "report.status_updated"
    QUALITY_SCORE_UPDATED = "quality_score.updated"

    # ── Participant Domain ────────────────────────────────────────────────
    PARTICIPANT_JOINED = "participant.joined"
    PARTICIPANT_LEFT = "participant.left"

    # ── Pulse / Summary ───────────────────────────────────────────────────
    PULSE_GENERATED = "pulse.generated"
