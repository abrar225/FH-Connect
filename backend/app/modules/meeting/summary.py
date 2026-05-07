"""
modules/meeting/summary.py — HTTP API endpoints for meeting pulse and reports.

The pulse broadcast now goes through the Event Bus instead of
directly importing the WebSocket manager, respecting the
architecture rules.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from app.modules.intelligence.summary_llm import generate_summary, MeetingPulse, TranscriptionLine
from app.modules.draft.models import TaskDraft
from app.core.event_bus import bus, Event
from app.core.constants import EventTypes
from app.core.ids import new_trace_id
from app.core.logging import get_logger
from app.core.auth import AuthUser, get_current_user, require_meeting_admin
from app.modules.audit.repository import record_audit_event
from app.modules.meeting.repository import get_report_status, set_report_status
from app.workers.report_queue import enqueue_report_event
import json
import os
import asyncio
from langchain_core.prompts import ChatPromptTemplate
from pydantic import Field
from app.core.config import settings
from app.modules.intelligence.intent_llm import get_structured_llm
from app.modules.productivity.service import get_user_ai_runtime_config
from app.workers.queue import intent_queue_metrics

router = APIRouter()
logger = get_logger("meeting.summary")


class SummaryRequest(BaseModel):
    transcripts: List[str]
    room_id: Optional[str] = None  # Optional room_id to broadcast pulse


class FinalReportRequest(BaseModel):
    room_id: str
    transcripts: List[TranscriptionLine]
    approved_tasks: List[TaskDraft]


class FinalReportAccepted(BaseModel):
    status: str
    room_id: str
    trace_id: str


class ReportStatusResponse(BaseModel):
    room_id: str
    status: str
    has_report: bool
    report_error: Optional[str] = None
    report_requested_at: Optional[str] = None
    ended_at: Optional[str] = None


class HealthCheckItem(BaseModel):
    ok: bool
    label: str
    detail: str


class MeetingAIHealthResponse(BaseModel):
    room_id: str
    overall: str
    message: str
    checks: dict[str, HealthCheckItem]


class AIHealthProbe(BaseModel):
    ok: bool = Field(description="Whether the health probe succeeded")


async def _probe_llm(user_id: str) -> HealthCheckItem:
    has_system_key = bool(settings.GEMINI_API_KEY or settings.GROQ_API_KEY)
    user_config = await get_user_ai_runtime_config(user_id)
    provider = user_config.get("provider") if user_config else ("system" if has_system_key else "none")
    model = user_config.get("model") if user_config else (settings.GEMINI_PRIMARY_MODEL if settings.GEMINI_API_KEY else settings.GROQ_PRIMARY_MODEL)

    if not user_config and not has_system_key:
        return HealthCheckItem(
            ok=False,
            label="AI provider",
            detail="No user AI API key or system AI API key is configured.",
        )

    try:
        model_chain = get_structured_llm(AIHealthProbe, user_config)
        if model_chain is None:
            return HealthCheckItem(ok=False, label="AI provider", detail="No usable AI model is configured.")
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Return a JSON object matching the schema with ok=true."),
            ("user", "Health check only."),
        ])
        result = await asyncio.wait_for((prompt | model_chain).ainvoke({}), timeout=8)
        if not getattr(result, "ok", False):
            raise RuntimeError("AI health probe returned a negative result")
        return HealthCheckItem(
            ok=True,
            label="AI provider",
            detail=f"{provider} model {model} is reachable.",
        )
    except Exception:
        logger.warning("AI health probe failed", exc_info=True, extra={"user_id": user_id})
        return HealthCheckItem(
            ok=False,
            label="AI provider",
            detail=f"{provider} model {model} could not be reached. Check API key, quota, and model access.",
        )


@router.get("/meeting/{room_id}/ai-health", response_model=MeetingAIHealthResponse)
async def meeting_ai_health(room_id: str, current_user: AuthUser = Depends(get_current_user)):
    """
    Preflight health for the live meeting AI pipeline.
    This intentionally returns product-safe status details, not raw provider errors.
    """
    has_transcription_token = bool(os.getenv("DEEPGRAM_TEMP_KEY") or settings.DEEPGRAM_API_KEY)
    checks: dict[str, HealthCheckItem] = {
        "auth": HealthCheckItem(ok=True, label="Authentication", detail="Supabase session verified."),
        "backend": HealthCheckItem(ok=True, label="Backend", detail="Backend API is reachable."),
        "transcription": HealthCheckItem(
            ok=has_transcription_token,
            label="Transcription",
            detail="Deepgram token is configured." if has_transcription_token else "Deepgram API key or temporary token is not configured.",
        ),
    }

    try:
        queue = await intent_queue_metrics()
        queue_alerts = queue.get("alerts") or {}
        queue_ok = not queue.get("error") and not queue_alerts.get("pending_backlog") and not queue_alerts.get("failed_jobs")
        checks["intent_worker"] = HealthCheckItem(
            ok=bool(queue_ok),
            label="Task extraction worker",
            detail="Intent queue is ready." if queue_ok else "Intent queue has backlog, failures, or unavailable metrics.",
        )
    except Exception:
        logger.warning("Intent queue health check failed", exc_info=True)
        checks["intent_worker"] = HealthCheckItem(
            ok=False,
            label="Task extraction worker",
            detail="Intent worker or queue is unavailable.",
        )

    checks["ai_provider"] = await _probe_llm(current_user.id)

    failed = [item for item in checks.values() if not item.ok]
    overall = "ready" if not failed else "unavailable"
    message = "AI meeting pipeline is ready." if not failed else failed[0].detail
    return MeetingAIHealthResponse(room_id=room_id, overall=overall, message=message, checks=checks)


@router.post("/summary", response_model=MeetingPulse)
async def get_summary(req: SummaryRequest, current_user: AuthUser = Depends(get_current_user)):
    """
    Accepts a list of transcripts and returns a real-time summary.
    If room_id is provided, emits a pulse.generated event for broadcasting.
    """
    summary = await generate_summary(req.transcripts, user_id=current_user.id)

    # Broadcast pulse via event bus (notification module handles WS)
    if req.room_id:
        await require_meeting_admin(req.room_id, current_user)
        pulse_message = json.dumps({
            "type": "pulse",
            "status": summary.status,
            "speaker_perspectives": summary.speaker_perspectives,
        })

        await bus.emit(Event(
            event_type=EventTypes.PULSE_GENERATED,
            trace_id=new_trace_id(),
            meeting_id=req.room_id,
            payload={
                "room_id": req.room_id,
                "pulse_json": pulse_message,
            },
        ))

    return summary


@router.post("/meeting/end", response_model=FinalReportAccepted, status_code=status.HTTP_202_ACCEPTED)
async def end_meeting(req: FinalReportRequest, current_user: AuthUser = Depends(get_current_user)):
    """
    Accepts the full state of the meeting and queues the final report.
    The report worker performs the expensive LLM call and saves the result.
    """
    await require_meeting_admin(req.room_id, current_user)

    trace_id = new_trace_id()
    queued = await enqueue_report_event(Event(
        event_type=EventTypes.MEETING_ENDED,
        trace_id=trace_id,
        meeting_id=req.room_id,
        payload={
            "room_id": req.room_id,
            "actor_id": current_user.id,
            "transcripts": [line.model_dump() for line in req.transcripts],
            "approved_tasks": [task.model_dump() for task in req.approved_tasks],
        },
    ))
    if not queued:
        raise HTTPException(status_code=503, detail="Report queue is full")

    await set_report_status(req.room_id, "queued")
    await bus.emit(Event(
        event_type=EventTypes.REPORT_STATUS_UPDATED,
        trace_id=trace_id,
        meeting_id=req.room_id,
        payload={"room_id": req.room_id, "status": "queued", "error": None},
    ))
    await record_audit_event(
        action="meeting.end_requested",
        actor_id=current_user.id,
        room_id=req.room_id,
        metadata={"transcript_count": len(req.transcripts), "task_count": len(req.approved_tasks)},
    )
    return FinalReportAccepted(status="queued", room_id=req.room_id, trace_id=trace_id)


@router.get("/meeting/{room_id}/report/status", response_model=ReportStatusResponse)
async def report_status(room_id: str, current_user: AuthUser = Depends(get_current_user)):
    await require_meeting_admin(room_id, current_user)
    status_row = await get_report_status(room_id)
    if not status_row:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return ReportStatusResponse(
        room_id=room_id,
        status=status_row.get("report_status") or "none",
        has_report=bool(status_row.get("has_report")),
        report_error=status_row.get("report_error"),
        report_requested_at=str(status_row["report_requested_at"]) if status_row.get("report_requested_at") else None,
        ended_at=str(status_row["ended_at"]) if status_row.get("ended_at") else None,
    )
