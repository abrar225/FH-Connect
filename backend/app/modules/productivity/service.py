import io
import base64
import hashlib
import json
import os
import secrets
import smtplib
import urllib.request
import zipfile
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field, field_validator, model_validator
from cryptography.fernet import Fernet

from app.core.auth import AuthUser, get_current_user, require_meeting_admin
from app.core.config import settings
from app.core.constants import EventTypes
from app.core.database import db
from app.core.event_bus import Event, bus
from app.core.ids import new_trace_id
from app.core.logging import get_logger
from app.modules.meeting.repository import create_meeting_record, get_meeting
from app.modules.meeting.permissions import require_database

router = APIRouter()
logger = get_logger("productivity.service")

InsightType = Literal["decision", "action_item", "risk", "question", "follow_up"]


class AgendaPayload(BaseModel):
    goals: List[str] = Field(default_factory=list)
    agenda_items: List[str] = Field(default_factory=list)
    expected_decisions: List[str] = Field(default_factory=list)
    attendees: List[str] = Field(default_factory=list)
    prep_docs: List[str] = Field(default_factory=list)


class AgendaGenerateRequest(BaseModel):
    topic: str = Field(default="Team meeting", max_length=240)
    attendees: List[str] = Field(default_factory=list)
    context: str = Field(default="", max_length=4000)


class ScheduleMeetingRequest(BaseModel):
    room_id: str = Field(min_length=3, max_length=80)
    title: str = Field(default="Scheduled Meeting", max_length=160)
    scheduled_for: Optional[str] = None
    agenda: Optional[AgendaPayload] = None


class InsightPatch(BaseModel):
    title: Optional[str] = None
    detail: Optional[str] = None
    owner: Optional[str] = None
    deadline: Optional[str] = None
    status: Optional[str] = None


class CopilotRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)


class ShareCreateRequest(BaseModel):
    expires_in_days: Optional[int] = Field(default=30, ge=1, le=365)
    allow_download: bool = True


class EmailReportRequest(BaseModel):
    recipients: List[str] = Field(min_length=1, max_length=25)
    message: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("recipients", mode="before")
    @classmethod
    def validate_email_format(cls, v: List[str]) -> List[str]:
        import re
        email_re = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        for addr in v:
            if not isinstance(addr, str) or not email_re.fullmatch(addr.strip()):
                raise ValueError(f"Invalid email address: {addr}")
        return [addr.strip() for addr in v]


class SettingsPayload(BaseModel):
    profile: Dict[str, Any] = Field(default_factory=dict)
    notification_preferences: Dict[str, Any] = Field(default_factory=dict)
    default_report_format: str = "markdown"
    ai_preferences: Dict[str, Any] = Field(default_factory=dict)
    security_preferences: Dict[str, Any] = Field(default_factory=dict)
    data_retention_days: int = Field(default=365, ge=30, le=3650)

    @model_validator(mode="before")
    @classmethod
    def coerce_json_dicts(cls, data: Any):
        if not isinstance(data, dict):
            return data
        normalized = dict(data)
        for key in ("profile", "notification_preferences", "ai_preferences", "security_preferences"):
            normalized[key] = _as_dict(normalized.get(key))
        return normalized


class IntegrationPayload(BaseModel):
    provider: str
    status: str = "disabled"
    config: Dict[str, Any] = Field(default_factory=dict)
    secret_ref: Optional[str] = None





def _as_dict(value: Any) -> dict:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def _normalize_settings_data(data: dict, api_key_status: Optional[dict] = None) -> dict:
    data["profile"] = _as_dict(data.get("profile"))
    data["notification_preferences"] = _as_dict(data.get("notification_preferences"))
    data["security_preferences"] = _as_dict(data.get("security_preferences"))
    ai_preferences = _as_dict(data.get("ai_preferences"))
    ai_preferences.pop("api_key", None)
    ai_preferences["api_key_status"] = api_key_status or {}
    data["ai_preferences"] = ai_preferences
    return data


def _ai_secret_cipher() -> Fernet:
    seed = (
        os.getenv("AI_KEY_ENCRYPTION_SECRET")
        or settings.SUPABASE_SERVICE_ROLE_KEY
        or settings.GEMINI_API_KEY
        or settings.GROQ_API_KEY
    )
    if not seed:
        if settings.ENVIRONMENT == "production":
            raise RuntimeError("Missing AI_KEY_ENCRYPTION_SECRET or equivalent in production")
        seed = "firehox-connect-local-development-secret"
    digest = hashlib.sha256(seed.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


async def _save_ai_provider_key(user_id: str, provider: str, api_key: str) -> dict:
    cleaned = api_key.strip()
    if not cleaned:
        return {}
    encrypted = _ai_secret_cipher().encrypt(cleaned.encode()).decode()
    key_last4 = cleaned[-4:]
    row = await db.pool.fetchrow(
        """INSERT INTO ai_provider_keys (user_id, provider, encrypted_api_key, key_last4)
           VALUES ($1, $2, $3, $4)
           ON CONFLICT (user_id, provider) DO UPDATE SET
             encrypted_api_key = EXCLUDED.encrypted_api_key,
             key_last4 = EXCLUDED.key_last4,
             updated_at = timezone('utc'::text, now())
           RETURNING provider, key_last4, updated_at""",
        user_id,
        provider,
        encrypted,
        key_last4,
    )
    return dict(row) if row else {}


async def _ai_key_status(user_id: str) -> dict:
    rows = await db.pool.fetch("SELECT provider, key_last4, updated_at FROM ai_provider_keys WHERE user_id = $1", user_id)
    return {row["provider"]: {"configured": True, "last4": row["key_last4"], "updated_at": row["updated_at"]} for row in rows}


async def get_user_ai_runtime_config(user_id: str) -> Optional[dict]:
    if not db.pool:
        return None
    settings_row = await db.pool.fetchrow("SELECT ai_preferences FROM user_settings WHERE user_id = $1", user_id)
    ai_preferences = _as_dict(settings_row["ai_preferences"]) if settings_row else {}
    provider = str(ai_preferences.get("provider") or "").lower().strip()
    if not provider:
        return None
    key_row = await db.pool.fetchrow(
        "SELECT encrypted_api_key FROM ai_provider_keys WHERE user_id = $1 AND provider = $2",
        user_id,
        provider,
    )
    if not key_row:
        return None
    try:
        api_key = _ai_secret_cipher().decrypt(key_row["encrypted_api_key"].encode()).decode()
    except Exception as exc:
        logger.error("Stored AI provider key could not be decrypted", extra={"user_id": user_id, "provider": provider}, exc_info=exc)
        raise HTTPException(status_code=500, detail="Internal configuration error: Failed to decrypt AI provider key")
    return {
        "provider": provider,
        "model": str(ai_preferences.get("custom_model") or ai_preferences.get("model") or "").strip(),
        "api_key": api_key,
    }


def _room_status(row: dict) -> str:
    if row.get("ended_at"):
        return "ended"
    if row.get("scheduled_for"):
        return "scheduled"
    return "live"


async def _ensure_personal_workspace(user: AuthUser) -> dict:
    await require_database()
    row = await db.pool.fetchrow("SELECT * FROM workspaces WHERE owner_id = $1 AND type = 'personal'", user.id)
    if row:
        return dict(row)
    created = await db.pool.fetchrow(
        """INSERT INTO workspaces (owner_id, name, type)
           VALUES ($1, $2, 'personal')
           ON CONFLICT DO NOTHING
           RETURNING *""",
        user.id,
        f"{user.name or user.email or 'My'} Workspace",
    )
    if created:
        return dict(created)
    row = await db.pool.fetchrow("SELECT * FROM workspaces WHERE owner_id = $1 AND type = 'personal'", user.id)
    return dict(row)


async def _fetch_report(room_id: str) -> dict:
    await require_database()
    row = await db.pool.fetchrow(
        "SELECT room_id, title, report_content, report_status, report_error, ended_at FROM meetings WHERE room_id = $1",
        room_id,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Meeting not found")
    if not row["report_content"]:
        raise HTTPException(status_code=404, detail="Report is not ready")
    return dict(row)


def _report_to_markdown(meeting: dict) -> str:
    content = meeting["report_content"]
    if isinstance(content, str):
        try:
            content = json.loads(content)
        except json.JSONDecodeError:
            return content
    tasks = content.get("tasks", []) if isinstance(content, dict) else []
    decisions = content.get("key_decisions", []) if isinstance(content, dict) else []
    lines = [
        f"# {meeting.get('title') or 'Meeting Report'}",
        "",
        "## Executive Summary",
        content.get("executive_summary", "") if isinstance(content, dict) else str(content),
        "",
        "## Key Decisions",
        *(f"- {item}" for item in decisions),
        "",
        "## Tasks",
        *(f"- {task.get('title', 'Task')} — {task.get('assignee') or 'Unassigned'}" for task in tasks),
        "",
        "## Meeting Minutes",
        content.get("meeting_minutes", "") if isinstance(content, dict) else "",
    ]
    return "\n".join(lines)


def _markdown_to_pdf_bytes(markdown: str) -> bytes:
    text = markdown.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 10 Tf 40 760 Td 14 TL ({text[:3500].replace(chr(10), ') Tj T* (')}) Tj ET"
    objects = [
        "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
        "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj",
        "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj",
        "4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj",
        f"5 0 obj << /Length {len(stream.encode())} >> stream\n{stream}\nendstream endobj",
    ]
    body = "%PDF-1.4\n" + "\n".join(objects) + "\n"
    offsets = [0]
    cursor = len("%PDF-1.4\n")
    for obj in objects:
        offsets.append(cursor)
        cursor += len(obj.encode()) + 1
    xref_pos = len(body.encode())
    xref = "xref\n0 6\n0000000000 65535 f \n" + "".join(f"{offset:010d} 00000 n \n" for offset in offsets[1:])
    trailer = f"trailer << /Size 6 /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF"
    return (body + xref + trailer).encode()


def _markdown_to_docx_bytes(markdown: str) -> bytes:
    escaped = markdown.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    paragraphs = "".join(f"<w:p><w:r><w:t>{line}</w:t></w:r></w:p>" for line in escaped.splitlines())
    document = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>{paragraphs}</w:body></w:document>"""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", """<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>""")
        docx.writestr("_rels/.rels", """<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>""")
        docx.writestr("word/document.xml", document)
    return buffer.getvalue()


def _heuristic_insights(text: str) -> List[dict]:
    lowered = text.lower()
    rules = [
        ("decision", ["decided", "decision", "we will", "approved"]),
        ("risk", ["risk", "blocked", "blocker", "concern", "issue"]),
        ("question", ["?", "question", "can we", "should we", "what about"]),
        ("follow_up", ["follow up", "circle back", "check with", "sync with"]),
        ("action_item", ["please", "todo", "action", "assign", "will do", " will ", "take care"]),
    ]
    insights = []
    for insight_type, markers in rules:
        if any(marker in lowered for marker in markers):
            insights.append({
                "type": insight_type,
                "title": text[:180],
                "detail": text,
                "confidence": 0.72,
            })
    return insights[:5]


async def persist_transcript_and_insights(payload: dict, actor_id: str) -> None:
    if not db.pool or not payload.get("is_final", True):
        return
    room_id = payload["room_id"]
    transcript_id = payload["id"]
    await db.pool.execute(
        """INSERT INTO meeting_transcripts (id, room_id, speaker, user_id, text, is_final)
           VALUES ($1, $2, $3, $4, $5, $6)
           ON CONFLICT (id) DO UPDATE SET text = EXCLUDED.text, is_final = EXCLUDED.is_final""",
        transcript_id,
        room_id,
        payload.get("speaker", "Unknown"),
        actor_id,
        payload["text"],
        payload.get("is_final", True),
    )
    for item in _heuristic_insights(payload["text"]):
        row = await db.pool.fetchrow(
            """INSERT INTO meeting_insights (room_id, type, title, detail, source_transcript_id, confidence, created_by)
               VALUES ($1, $2, $3, $4, $5, $6, $7)
               RETURNING *""",
            room_id,
            item["type"],
            item["title"],
            item["detail"],
            transcript_id,
            item["confidence"],
            actor_id,
        )
        await bus.emit(Event(
            event_type=EventTypes.INSIGHT_CREATED,
            trace_id=new_trace_id(),
            meeting_id=room_id,
            payload={"room_id": room_id, "insight": dict(row)},
        ))


async def compute_quality_score(room_id: str) -> dict:
    if not db.pool:
        return {}
    agenda = await db.pool.fetchrow("SELECT goals, agenda_items, expected_decisions FROM meeting_agendas WHERE room_id = $1", room_id)
    insights = await db.pool.fetch("SELECT type, owner, status FROM meeting_insights WHERE room_id = $1", room_id)
    transcripts = await db.pool.fetch("SELECT speaker, text FROM meeting_transcripts WHERE room_id = $1", room_id)
    decisions = sum(1 for row in insights if row["type"] == "decision")
    assigned = sum(1 for row in insights if row["type"] == "action_item" and row["owner"])
    unresolved_questions = sum(1 for row in insights if row["type"] == "question" and row["status"] != "resolved")
    agenda_items = len((agenda or {}).get("agenda_items") or []) if agenda else 0
    agenda_followed = 1.0 if agenda_items and len(transcripts) >= agenda_items else (0.5 if agenda_items else 0)
    participation: Dict[str, int] = {}
    for row in transcripts:
        participation[row["speaker"]] = participation.get(row["speaker"], 0) + len(row["text"].split())
    total_words = sum(participation.values()) or 1
    participation_pct = {speaker: round(words / total_words * 100, 1) for speaker, words in participation.items()}
    score = min(100, round((agenda_followed * 25) + min(decisions, 5) * 10 + min(assigned, 5) * 8 + max(0, 25 - unresolved_questions * 5), 1))
    row = await db.pool.fetchrow(
        """INSERT INTO meeting_quality_scores
           (room_id, score, agenda_followed, decisions_made, action_items_assigned, unresolved_questions, participation, time_per_topic)
           VALUES ($1, $2, $3, $4, $5, $6, $7, '{}'::jsonb)
           ON CONFLICT (room_id) DO UPDATE SET
             score = EXCLUDED.score,
             agenda_followed = EXCLUDED.agenda_followed,
             decisions_made = EXCLUDED.decisions_made,
             action_items_assigned = EXCLUDED.action_items_assigned,
             unresolved_questions = EXCLUDED.unresolved_questions,
             participation = EXCLUDED.participation
           RETURNING *""",
        room_id,
        score,
        agenda_followed,
        decisions,
        assigned,
        unresolved_questions,
        participation_pct,
    )
    await bus.emit(Event(
        event_type=EventTypes.QUALITY_SCORE_UPDATED,
        trace_id=new_trace_id(),
        meeting_id=room_id,
        payload={"room_id": room_id, "quality_score": dict(row)},
    ))
    return dict(row)


@router.get("/meetings")
async def list_meetings(
    limit: int = 50,
    offset: int = 0,
    current_user: AuthUser = Depends(get_current_user),
):
    await _ensure_personal_workspace(current_user)
    limit = min(limit, 100)
    rows = await db.pool.fetch(
        """SELECT *, report_content IS NOT NULL AS has_report
           FROM meetings
           WHERE created_by = $1 OR $1 = ANY(admins)
           ORDER BY COALESCE(scheduled_for, started_at, created_at) DESC
           LIMIT $2 OFFSET $3""",
        current_user.id, limit, offset,
    )
    return [{**dict(row), "status": _room_status(dict(row))} for row in rows]


@router.post("/meetings/schedule")
async def schedule_meeting(req: ScheduleMeetingRequest, current_user: AuthUser = Depends(get_current_user)):
    await _ensure_personal_workspace(current_user)
    await create_meeting_record(req.room_id, current_user.id, req.title)
    await db.pool.execute(
        "UPDATE meetings SET scheduled_for = $1, started_at = NULL WHERE room_id = $2",
        req.scheduled_for,
        req.room_id,
    )
    if req.agenda:
        await upsert_agenda(req.room_id, req.agenda, current_user)
    return {"status": "scheduled", "room_id": req.room_id}


@router.get("/meeting/{room_id}/agenda")
async def get_agenda(room_id: str, current_user: AuthUser = Depends(get_current_user)):
    await require_meeting_admin(room_id, current_user)
    row = await db.pool.fetchrow("SELECT * FROM meeting_agendas WHERE room_id = $1", room_id)
    return dict(row) if row else {"room_id": room_id, **AgendaPayload().model_dump()}


@router.put("/meeting/{room_id}/agenda")
async def upsert_agenda(room_id: str, req: AgendaPayload, current_user: AuthUser = Depends(get_current_user)):
    await require_meeting_admin(room_id, current_user)
    row = await db.pool.fetchrow(
        """INSERT INTO meeting_agendas (room_id, goals, agenda_items, expected_decisions, attendees, prep_docs, updated_by)
           VALUES ($1, $2, $3, $4, $5, $6, $7)
           ON CONFLICT (room_id) DO UPDATE SET
             goals = EXCLUDED.goals,
             agenda_items = EXCLUDED.agenda_items,
             expected_decisions = EXCLUDED.expected_decisions,
             attendees = EXCLUDED.attendees,
             prep_docs = EXCLUDED.prep_docs,
             updated_by = EXCLUDED.updated_by,
             updated_at = timezone('utc'::text, now())
           RETURNING *""",
        room_id,
        req.goals if req.goals is not None else [],
        req.agenda_items if req.agenda_items is not None else [],
        req.expected_decisions if req.expected_decisions is not None else [],
        req.attendees if req.attendees is not None else [],
        req.prep_docs if req.prep_docs is not None else [],
        current_user.id,
    )
    await bus.emit(Event(
        event_type=EventTypes.AGENDA_UPDATED,
        trace_id=new_trace_id(),
        meeting_id=room_id,
        payload={"room_id": room_id, "agenda": dict(row)},
    ))
    return dict(row)


@router.post("/meeting/{room_id}/agenda/generate")
async def generate_agenda(room_id: str, req: AgendaGenerateRequest, current_user: AuthUser = Depends(get_current_user)):
    await require_meeting_admin(room_id, current_user)
    topic = req.topic.strip() or "Team meeting"
    agenda = AgendaPayload(
        goals=[f"Align on {topic}", "Confirm owners and next steps", "Identify risks and open questions"],
        agenda_items=[f"Context and goals for {topic}", "Discussion and decisions", "Action ownership", "Risks and follow-ups"],
        expected_decisions=[f"Decision on next step for {topic}", "Owner and deadline for action items"],
        attendees=req.attendees,
        prep_docs=[req.context] if req.context else [],
    )
    return await upsert_agenda(room_id, agenda, current_user)


@router.get("/meeting/{room_id}/insights")
async def list_insights(room_id: str, current_user: AuthUser = Depends(get_current_user)):
    await require_meeting_admin(room_id, current_user)
    rows = await db.pool.fetch("SELECT * FROM meeting_insights WHERE room_id = $1 ORDER BY created_at DESC", room_id)
    return [dict(row) for row in rows]


@router.patch("/actions/{insight_id}")
async def patch_action(insight_id: str, req: InsightPatch, current_user: AuthUser = Depends(get_current_user)):
    await require_database()
    row = await db.pool.fetchrow("SELECT room_id FROM meeting_insights WHERE id = $1", insight_id)
    if not row:
        raise HTTPException(status_code=404, detail="Action not found")
    await require_meeting_admin(row["room_id"], current_user)
    updated = await db.pool.fetchrow(
        """UPDATE meeting_insights SET
             title = COALESCE($2, title),
             detail = COALESCE($3, detail),
             owner = COALESCE($4, owner),
             deadline = COALESCE($5, deadline),
             status = COALESCE($6, status),
             updated_at = timezone('utc'::text, now())
           WHERE id = $1
           RETURNING *""",
        insight_id,
        req.title,
        req.detail,
        req.owner,
        req.deadline,
        req.status,
    )
    await bus.emit(Event(
        event_type=EventTypes.INSIGHT_UPDATED,
        trace_id=new_trace_id(),
        meeting_id=updated["room_id"],
        payload={"room_id": updated["room_id"], "insight": dict(updated)},
    ))
    return dict(updated)


@router.get("/actions")
async def list_actions(
    limit: int = 50,
    offset: int = 0,
    current_user: AuthUser = Depends(get_current_user)
):
    await require_database()
    limit = min(limit, 100)
    
    rows = await db.pool.fetch(
        """SELECT mi.*, m.title AS meeting_title
           FROM meeting_insights mi
           JOIN meetings m ON m.room_id = mi.room_id
           WHERE mi.type = 'action_item' AND (m.created_by = $1 OR $1 = ANY(m.admins) OR mi.owner = $1)
           ORDER BY mi.created_at DESC
           LIMIT $2 OFFSET $3""",
        current_user.id, limit, offset
    )
    drafts = await db.pool.fetch(
        """SELECT td.id, td.room_id, 'draft' AS type, td.title, td.original_transcript AS detail,
                  td.assignee AS owner, td.deadline, td.status, td.created_at, m.title AS meeting_title
           FROM task_drafts td
           JOIN meetings m ON m.room_id = td.room_id
           WHERE m.created_by = $1 OR $1 = ANY(m.admins) OR td.assignee = $1
           ORDER BY td.created_at DESC
           LIMIT $2 OFFSET $3""",
        current_user.id, limit, offset
    )
    return [dict(row) for row in rows] + [dict(row) for row in drafts]


@router.post("/meeting/{room_id}/copilot")
async def ask_copilot(room_id: str, req: CopilotRequest, current_user: AuthUser = Depends(get_current_user)):
    await require_meeting_admin(room_id, current_user)
    agenda = await db.pool.fetchrow("SELECT * FROM meeting_agendas WHERE room_id = $1", room_id)
    transcripts = await db.pool.fetch("SELECT speaker, text FROM meeting_transcripts WHERE room_id = $1 ORDER BY spoken_at DESC LIMIT 50", room_id)
    insights = await db.pool.fetch("SELECT type, title, detail, owner, status FROM meeting_insights WHERE room_id = $1 ORDER BY created_at DESC LIMIT 50", room_id)
    q = req.question.lower()
    answer_parts = []
    if "commit" in q or "action" in q or "assigned" in q:
        actions = [dict(row) for row in insights if row["type"] == "action_item"]
        answer_parts.append("Action items: " + (json.dumps(actions[:8], default=str) if actions else "none captured yet."))
    if "decision" in q:
        decisions = [dict(row) for row in insights if row["type"] == "decision"]
        answer_parts.append("Decisions: " + (json.dumps(decisions[:8], default=str) if decisions else "none captured yet."))
    if "risk" in q:
        risks = [dict(row) for row in insights if row["type"] == "risk"]
        answer_parts.append("Risks: " + (json.dumps(risks[:8], default=str) if risks else "none captured yet."))
    if "question" in q or "pending" in q:
        questions = [dict(row) for row in insights if row["type"] == "question" and row["status"] != "resolved"]
        answer_parts.append("Open questions: " + (json.dumps(questions[:8], default=str) if questions else "none captured yet."))
    if "summar" in q or not answer_parts:
        recent = list(reversed([f"{row['speaker']}: {row['text']}" for row in transcripts[:10]]))
        answer_parts.append("Recent meeting context: " + (" ".join(recent) if recent else "No transcript captured yet."))
    return {
        "answer": "\n\n".join(answer_parts),
        "sources": {
            "agenda": dict(agenda) if agenda else None,
            "transcript_count": len(transcripts),
            "insight_count": len(insights),
        },
    }


@router.get("/recordings")
async def list_recordings(
    limit: int = 50,
    offset: int = 0,
    current_user: AuthUser = Depends(get_current_user),
):
    await require_database()
    limit = min(limit, 100)
    rows = await db.pool.fetch(
        """SELECT m.room_id, m.title, m.started_at, m.ended_at, COUNT(mt.id) AS transcript_count,
                  m.report_content IS NOT NULL AS has_report
           FROM meetings m
           LEFT JOIN meeting_transcripts mt ON mt.room_id = m.room_id
           WHERE m.created_by = $1 OR $1 = ANY(m.admins)
           GROUP BY m.room_id, m.title, m.started_at, m.ended_at, m.report_content
           HAVING COUNT(mt.id) > 0
           ORDER BY COALESCE(m.ended_at, m.started_at, m.created_at) DESC
           LIMIT $2 OFFSET $3""",
        current_user.id, limit, offset,
    )
    return [dict(row) for row in rows]


@router.get("/recordings/{room_id}/transcript")
async def recording_transcript(room_id: str, q: str = "", current_user: AuthUser = Depends(get_current_user)):
    await require_meeting_admin(room_id, current_user)
    if q:
        rows = await db.pool.fetch(
            "SELECT * FROM meeting_transcripts WHERE room_id = $1 AND text ILIKE $2 ORDER BY spoken_at",
            room_id,
            f"%{q}%",
        )
    else:
        rows = await db.pool.fetch("SELECT * FROM meeting_transcripts WHERE room_id = $1 ORDER BY spoken_at", room_id)
    return [dict(row) for row in rows]


@router.get("/reports")
async def list_reports(
    limit: int = 50,
    offset: int = 0,
    current_user: AuthUser = Depends(get_current_user),
):
    await require_database()
    limit = min(limit, 100)
    rows = await db.pool.fetch(
        """SELECT m.*, qs.score AS quality_score
           FROM meetings m
           LEFT JOIN meeting_quality_scores qs ON qs.room_id = m.room_id
           WHERE (m.created_by = $1 OR $1 = ANY(m.admins))
             AND (m.report_requested_at IS NOT NULL OR m.report_content IS NOT NULL OR m.report_status = 'failed')
           ORDER BY COALESCE(m.ended_at, m.report_requested_at, m.created_at) DESC
           LIMIT $2 OFFSET $3""",
        current_user.id, limit, offset,
    )
    return [dict(row) for row in rows]


@router.get("/reports/{room_id}/download")
async def download_report(room_id: str, format: str = Query("markdown"), current_user: AuthUser = Depends(get_current_user)):
    await require_meeting_admin(room_id, current_user)
    meeting = await _fetch_report(room_id)
    markdown = _report_to_markdown(meeting)
    filename = f"Meeting_Report_{room_id}"
    if format == "pdf":
        return Response(_markdown_to_pdf_bytes(markdown), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={filename}.pdf"})
    if format == "docx":
        return Response(_markdown_to_docx_bytes(markdown), media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", headers={"Content-Disposition": f"attachment; filename={filename}.docx"})
    return Response(markdown, media_type="text/markdown", headers={"Content-Disposition": f"attachment; filename={filename}.md"})


@router.post("/reports/{room_id}/share")
async def create_report_share(room_id: str, req: ShareCreateRequest, current_user: AuthUser = Depends(get_current_user)):
    await require_meeting_admin(room_id, current_user)
    await _fetch_report(room_id)
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=req.expires_in_days or 30)
    row = await db.pool.fetchrow(
        """INSERT INTO report_shares (room_id, token, created_by, expires_at, allow_download)
           VALUES ($1, $2, $3, $4, $5)
           RETURNING id, room_id, token, expires_at, allow_download, created_at""",
        room_id,
        token,
        current_user.id,
        expires_at,
        req.allow_download,
    )
    return dict(row)


@router.delete("/reports/share/{share_id}")
async def revoke_report_share(share_id: str, current_user: AuthUser = Depends(get_current_user)):
    row = await db.pool.fetchrow("SELECT room_id FROM report_shares WHERE id = $1", share_id)
    if not row:
        raise HTTPException(status_code=404, detail="Share not found")
    await require_meeting_admin(row["room_id"], current_user)
    await db.pool.execute("UPDATE report_shares SET revoked_at = timezone('utc'::text, now()) WHERE id = $1", share_id)
    return {"status": "revoked"}


@router.get("/public/reports/{token}")
async def public_report(token: str):
    await require_database()
    row = await db.pool.fetchrow(
        """SELECT rs.allow_download, m.room_id, m.title, m.report_content
           FROM report_shares rs
           JOIN meetings m ON m.room_id = rs.room_id
           WHERE rs.token = $1 AND rs.revoked_at IS NULL AND (rs.expires_at IS NULL OR rs.expires_at > timezone('utc'::text, now()))""",
        token,
    )
    if not row:
        raise HTTPException(status_code=404, detail="Share not found")
    return dict(row)


@router.post("/reports/{room_id}/email")
async def email_report(room_id: str, req: EmailReportRequest, current_user: AuthUser = Depends(get_current_user)):
    await require_meeting_admin(room_id, current_user)
    meeting = await _fetch_report(room_id)
    markdown = _report_to_markdown(meeting)
    import os
    import httpx
    import aiosmtplib
    webhook = os.getenv("EMAIL_WEBHOOK_URL")
    if webhook:
        # SSRF protection: reject internal/private URLs
        from urllib.parse import urlparse
        parsed = urlparse(webhook)
        if parsed.scheme not in ("https",):
            raise HTTPException(status_code=500, detail="Email webhook must use HTTPS")
        hostname = parsed.hostname or ""
        if hostname in ("localhost", "127.0.0.1", "0.0.0.0", "::1") or hostname.startswith("10.") or hostname.startswith("192.168.") or hostname.startswith("169.254.") or hostname.startswith("172."):
            raise HTTPException(status_code=500, detail="Email webhook cannot target internal addresses")
        logger.info(f"Sending report via webhook [room={room_id}, recipients={len(req.recipients)}]")
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(webhook, json={"room_id": room_id, "recipients": req.recipients, "message": req.message, "report": markdown})
            res.raise_for_status()
        return {"status": "sent", "provider": "webhook"}
    smtp_host = os.getenv("SMTP_HOST")
    if smtp_host:
        message = EmailMessage()
        message["Subject"] = f"Meeting report: {meeting.get('title') or room_id}"
        message["From"] = os.getenv("SMTP_FROM", "reports@firehox.local")
        message["To"] = ", ".join(req.recipients)
        message.set_content((req.message + "\n\n" if req.message else "") + markdown)
        await aiosmtplib.send(message, hostname=smtp_host, port=int(os.getenv("SMTP_PORT", "25")))
        return {"status": "sent", "provider": "smtp"}
    return {"status": "configured_required", "provider": "none"}


@router.get("/settings")
async def get_settings(current_user: AuthUser = Depends(get_current_user)):
    await _ensure_personal_workspace(current_user)
    row = await db.pool.fetchrow("SELECT * FROM user_settings WHERE user_id = $1", current_user.id)
    if row:
        data = dict(row)
        return _normalize_settings_data(data, await _ai_key_status(current_user.id))
    defaults = SettingsPayload(profile={"name": current_user.name, "email": current_user.email})
    created = await db.pool.fetchrow(
        """INSERT INTO user_settings
           (user_id, profile, notification_preferences, default_report_format, ai_preferences, security_preferences, data_retention_days)
           VALUES ($1, $2::jsonb, $3::jsonb, $4, $5::jsonb, $6::jsonb, $7)
           RETURNING *""",
        current_user.id,
        defaults.profile,
        defaults.notification_preferences,
        defaults.default_report_format,
        defaults.ai_preferences,
        defaults.security_preferences,
        defaults.data_retention_days,
    )
    data = dict(created)
    return _normalize_settings_data(data, await _ai_key_status(current_user.id))


@router.put("/settings")
async def update_settings(req: SettingsPayload, current_user: AuthUser = Depends(get_current_user)):
    await _ensure_personal_workspace(current_user)
    ai_preferences = dict(req.ai_preferences or {})
    provider = str(ai_preferences.get("provider") or "").lower().strip()
    api_key = str(ai_preferences.pop("api_key", "") or "")
    ai_preferences.pop("api_key_status", None)
    trace_id = new_trace_id()
    try:
        if provider and api_key:
            await _save_ai_provider_key(current_user.id, provider, api_key)
        row = await db.pool.fetchrow(
            """INSERT INTO user_settings
               (user_id, profile, notification_preferences, default_report_format, ai_preferences, security_preferences, data_retention_days)
               VALUES ($1, $2::jsonb, $3::jsonb, $4, $5::jsonb, $6::jsonb, $7)
               ON CONFLICT (user_id) DO UPDATE SET
                 profile = EXCLUDED.profile,
                 notification_preferences = EXCLUDED.notification_preferences,
                 default_report_format = EXCLUDED.default_report_format,
                 ai_preferences = EXCLUDED.ai_preferences,
                 security_preferences = EXCLUDED.security_preferences,
                 data_retention_days = EXCLUDED.data_retention_days,
                 updated_at = timezone('utc'::text, now())
               RETURNING *""",
            current_user.id,
            req.profile,
            req.notification_preferences,
            req.default_report_format,
            ai_preferences,
            req.security_preferences,
            req.data_retention_days,
        )
    except Exception as exc:
        logger.error(
            "Failed to save user settings",
            exc_info=exc,
            extra={"trace_id": trace_id, "user_id": current_user.id},
        )
        raise HTTPException(status_code=500, detail=f"Settings save failed. Reference: {trace_id}") from exc
    data = dict(row)
    return _normalize_settings_data(data, await _ai_key_status(current_user.id))


@router.get("/integrations")
async def list_integrations(current_user: AuthUser = Depends(get_current_user)):
    await _ensure_personal_workspace(current_user)
    rows = await db.pool.fetch("SELECT * FROM integrations WHERE user_id = $1 ORDER BY provider", current_user.id)
    return [dict(row) for row in rows]


@router.post("/integrations")
async def upsert_integration(req: IntegrationPayload, current_user: AuthUser = Depends(get_current_user)):
    await _ensure_personal_workspace(current_user)
    provider = req.provider.lower()
    allowed = {"slack", "linear", "jira", "google_calendar", "gmail", "google_drive"}
    if provider not in allowed:
        raise HTTPException(status_code=400, detail="Unsupported integration provider")
    row = await db.pool.fetchrow(
        """INSERT INTO integrations (user_id, provider, status, config, secret_ref)
           VALUES ($1, $2, $3, $4, $5)
           ON CONFLICT (user_id, provider) DO UPDATE SET
             status = EXCLUDED.status,
             config = EXCLUDED.config,
             secret_ref = EXCLUDED.secret_ref,
             updated_at = timezone('utc'::text, now())
           RETURNING *""",
        current_user.id,
        provider,
        req.status,
        req.config,
        req.secret_ref,
    )
    return dict(row)

@router.get("/integrations/dead-letters")
async def get_dead_letters(current_user: AuthUser = Depends(get_current_user)):
    await require_database()
    workspace = await _ensure_personal_workspace(current_user)
    rows = await db.pool.fetch(
        """SELECT id, provider, action, payload, status, last_error, updated_at 
           FROM connector_jobs 
           WHERE workspace_id = $1 AND status = 'dead_lettered'
           ORDER BY updated_at DESC""",
        workspace["id"]
    )
    return {"dead_letters": [dict(r) for r in rows]}


@router.post("/integrations/{job_id}/retry")
async def retry_dead_letter(job_id: str, current_user: AuthUser = Depends(get_current_user)):
    await require_database()
    workspace = await _ensure_personal_workspace(current_user)
    row = await db.pool.fetchrow(
        "SELECT id FROM connector_jobs WHERE id = $1 AND workspace_id = $2 AND status = 'dead_lettered'",
        job_id, workspace["id"]
    )
    if not row:
        raise HTTPException(status_code=404, detail="Dead letter job not found")
        
    from datetime import datetime, timezone
    await db.pool.execute(
        "UPDATE connector_jobs SET status = 'queued', attempts = 0, next_run_at = timezone('utc'::text, now()), updated_at = timezone('utc'::text, now()) WHERE id = $1",
        job_id
    )
    
    from app.workers.connector_queue import schedule_connector_job
    await schedule_connector_job(job_id, datetime.now(timezone.utc))
    
    return {"status": "success", "message": "Job queued for retry"}



@router.post("/integrations/{provider}/test")
async def test_integration(provider: str, current_user: AuthUser = Depends(get_current_user)):
    await _ensure_personal_workspace(current_user)
    row = await db.pool.fetchrow("SELECT * FROM integrations WHERE user_id = $1 AND provider = $2", current_user.id, provider.lower())
    if not row:
        raise HTTPException(status_code=404, detail="Integration not configured")
    config = row["config"] or {}
    webhook = config.get("webhook_url")
    if webhook:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(webhook, json={"text": "FireHox Connect integration test"})
            res.raise_for_status()
        return {"status": "ok", "provider": provider}
    return {"status": "configured", "provider": provider, "external_call": "skipped"}


@router.delete("/meeting/{room_id}")
async def delete_meeting(room_id: str, current_user: AuthUser = Depends(get_current_user)):
    await require_meeting_admin(room_id, current_user)
    await db.pool.execute("DELETE FROM meetings WHERE room_id = $1", room_id)
    return {"status": "deleted", "room_id": room_id}


@router.delete("/actions/{insight_id}")
async def delete_action(insight_id: str, current_user: AuthUser = Depends(get_current_user)):
    await require_database()
    row = await db.pool.fetchrow("SELECT room_id FROM meeting_insights WHERE id = $1", insight_id)
    if not row:
        raise HTTPException(status_code=404, detail="Action not found")
    await require_meeting_admin(row["room_id"], current_user)
    await db.pool.execute("DELETE FROM meeting_insights WHERE id = $1", insight_id)
    return {"status": "deleted", "id": insight_id}


@router.delete("/recordings/{room_id}")
async def delete_recording(room_id: str, current_user: AuthUser = Depends(get_current_user)):
    await require_meeting_admin(room_id, current_user)
    await db.pool.execute("DELETE FROM meeting_transcripts WHERE room_id = $1", room_id)
    await db.pool.execute("DELETE FROM meetings WHERE room_id = $1", room_id)
    return {"status": "deleted", "room_id": room_id}


@router.delete("/reports/{room_id}")
async def delete_report(room_id: str, current_user: AuthUser = Depends(get_current_user)):
    await require_meeting_admin(room_id, current_user)
    await db.pool.execute(
        "UPDATE meetings SET report_content = NULL, report_status = NULL, report_requested_at = NULL, report_error = NULL WHERE room_id = $1",
        room_id,
    )
    return {"status": "deleted", "room_id": room_id}
