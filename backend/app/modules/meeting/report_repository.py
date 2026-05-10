from app.core.database import db
from app.modules.draft.models import TaskDraft
from app.modules.intelligence.summary_llm import TranscriptionLine


async def load_report_inputs(room_id: str) -> tuple[list[TranscriptionLine], list[TaskDraft]]:
    if not db.pool:
        raise RuntimeError("Database not configured")

    transcript_rows = await db.pool.fetch(
        """SELECT id, text, speaker, spoken_at
           FROM meeting_transcripts
           WHERE room_id = $1 AND is_final = true
           ORDER BY spoken_at ASC""",
        room_id,
    )
    transcripts = [
        TranscriptionLine(
            id=str(row["id"]),
            text=row["text"],
            speaker=row["speaker"],
            timestamp=str(row["spoken_at"]),
        )
        for row in transcript_rows
    ]
    if not transcripts:
        raise ValueError("No final transcripts captured for this meeting")

    draft_rows = await db.pool.fetch(
        """SELECT id, room_id, original_transcript, title, assignee, deadline, status, created_at
           FROM task_drafts
           WHERE room_id = $1 AND status = 'approved'
           ORDER BY created_at ASC""",
        room_id,
    )
    drafts = [TaskDraft(**{**dict(row), "id": str(row["id"])}) for row in draft_rows]
    return transcripts, drafts


async def list_room_transcripts(room_id: str) -> list[dict]:
    if not db.pool:
        return []
    rows = await db.pool.fetch(
        """SELECT id, room_id, speaker, user_id, text, is_final, spoken_at, created_at
           FROM meeting_transcripts
           WHERE room_id = $1
           ORDER BY spoken_at ASC""",
        room_id,
    )
    return [dict(row) for row in rows]


async def list_room_drafts(room_id: str) -> list[dict]:
    if not db.pool:
        return []
    rows = await db.pool.fetch(
        """SELECT id, room_id, original_transcript, title, assignee, deadline, status, created_at
           FROM task_drafts
           WHERE room_id = $1
           ORDER BY created_at ASC""",
        room_id,
    )
    return [dict(row) for row in rows]
