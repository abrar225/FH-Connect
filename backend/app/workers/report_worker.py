import asyncio

from app.core.logging import get_logger
from app.core.constants import EventTypes
from app.core.event_bus import Event, bus
from app.core.ids import new_trace_id
from app.modules.audit.repository import record_audit_event
from app.modules.draft.models import TaskDraft
from app.modules.intelligence.summary_llm import TranscriptionLine, generate_final_report
from app.modules.meeting.repository import save_meeting_report, set_report_status
from app.workers.report_queue import (
    ack_report_event,
    complete_report_event,
    dequeue_report_event,
    fail_report_event,
    should_process_report_event,
)

logger = get_logger("report_worker")


async def process_report_task(event):
    payload = event.payload
    room_id = payload["room_id"]
    actor_id = payload.get("actor_id")
    transcripts = [TranscriptionLine.model_validate(item) for item in payload.get("transcripts", [])]
    approved_tasks = [TaskDraft.model_validate(item) for item in payload.get("approved_tasks", [])]

    await set_report_status(room_id, "processing")
    await bus.emit(Event(
        event_type=EventTypes.REPORT_STATUS_UPDATED,
        trace_id=event.trace_id or new_trace_id(),
        meeting_id=room_id,
        payload={"room_id": room_id, "status": "processing", "error": None},
    ))
    report = await generate_final_report(transcripts, approved_tasks, user_id=actor_id)
    await save_meeting_report(room_id, report.model_dump_json())
    await bus.emit(Event(
        event_type=EventTypes.REPORT_STATUS_UPDATED,
        trace_id=event.trace_id or new_trace_id(),
        meeting_id=room_id,
        payload={"room_id": room_id, "status": "completed", "error": None},
    ))
    try:
        from app.modules.productivity.service import compute_quality_score
        await compute_quality_score(room_id)
    except Exception:
        logger.error("Failed to compute meeting quality score", exc_info=True)
    await record_audit_event(
        action="meeting.ended",
        actor_id=actor_id,
        room_id=room_id,
        metadata={"transcript_count": len(transcripts), "task_count": len(approved_tasks)},
    )


async def start_report_worker():
    logger.info("Report worker started, waiting for tasks...")
    while True:
        event = None
        stream_id = None
        try:
            event, stream_id = await dequeue_report_event()
            if event is None:
                continue
            if not await should_process_report_event(event):
                await ack_report_event(stream_id)
                continue

            logger.info(f"Worker picked up report task [trace={event.trace_id[:8]}, room={event.meeting_id}]")
            await process_report_task(event)
            await complete_report_event(event, stream_id)
        except asyncio.CancelledError:
            logger.info("Report worker cancelled.")
            break
        except Exception as exc:
            logger.error(f"Error in report worker loop: {exc}", exc_info=True)
            if event:
                room_id = event.payload.get("room_id") or event.meeting_id
                if room_id:
                    try:
                        await set_report_status(room_id, "failed", "Report generation failed")
                        await bus.emit(Event(
                            event_type=EventTypes.REPORT_STATUS_UPDATED,
                            trace_id=getattr(event, "trace_id", None) or new_trace_id(),
                            meeting_id=room_id,
                            payload={"room_id": room_id, "status": "failed", "error": "Report generation failed"},
                        ))
                    except Exception:
                        logger.error("Failed to update report status after worker error", exc_info=True)
            try:
                await fail_report_event(event, stream_id)
            except Exception:
                logger.error("Failed to mark report task as failed", exc_info=True)
