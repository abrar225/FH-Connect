import asyncio
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.database import db
from app.core.logging import get_logger
from app.modules.observability.metrics import connector_jobs_total
from app.workers.connector_queue import (
    ack_connector_job,
    dequeue_connector_job,
    promote_due_connector_jobs,
    release_connector_job_lock,
    schedule_connector_job,
    send_connector_dead_letter,
    should_process_connector_job,
)

logger = get_logger("connector_worker")


async def _execute_provider(job: dict) -> dict:
    provider = job["provider"]
    if provider == "slack":
        from app.modules.connectors.providers.slack import execute
    elif provider == "jira":
        from app.modules.connectors.providers.jira import execute
    elif provider in {"calendar", "google_calendar"}:
        from app.modules.connectors.providers.calendar import execute
    else:
        raise ValueError(f"Unsupported connector provider: {provider}")
    result = await execute(job)
    return result or {}


async def process_connector_job(job_id: str) -> None:
    if not db.pool:
        raise RuntimeError("Database not configured")
    job = await db.pool.fetchrow("SELECT * FROM connector_jobs WHERE id = $1", job_id)
    if not job:
        return
    job = dict(job)
    if job["status"] not in {"queued", "retrying"}:
        return
    if job.get("next_run_at") and job["next_run_at"] > datetime.now(timezone.utc):
        await schedule_connector_job(job_id, job["next_run_at"])
        return

    attempt = int(job.get("attempts") or 0) + 1
    await db.pool.execute(
        "UPDATE connector_jobs SET status = 'processing', attempts = $2, updated_at = timezone('utc'::text, now()) WHERE id = $1",
        job_id,
        attempt,
    )
    try:
        provider_result = await _execute_provider(job)
        await db.pool.execute(
            """UPDATE connector_jobs
               SET status = 'succeeded',
                   external_object_id = COALESCE($2, external_object_id),
                   external_object_url = COALESCE($3, external_object_url),
                   updated_at = timezone('utc'::text, now())
               WHERE id = $1""",
            job_id,
            provider_result.get("external_object_id"),
            provider_result.get("external_object_url"),
        )
        await db.pool.execute(
            "INSERT INTO connector_job_attempts (job_id, attempt_number, status) VALUES ($1, $2, 'succeeded')",
            job_id,
            attempt,
        )
        connector_jobs_total.labels(provider=job["provider"], action=job["action"], status="succeeded").inc()
    except Exception as exc:
        error_class = exc.__class__.__name__
        error_message = str(exc)
        await db.pool.execute(
            """INSERT INTO connector_job_attempts (job_id, attempt_number, status, error_class, error_message)
               VALUES ($1, $2, 'failed', $3, $4)""",
            job_id,
            attempt,
            error_class,
            error_message[:1000],
        )
        if attempt >= settings.CONNECTOR_MAX_ATTEMPTS:
            await db.pool.execute(
                "UPDATE connector_jobs SET status = 'dead_lettered', last_error = $2, updated_at = timezone('utc'::text, now()) WHERE id = $1",
                job_id,
                error_message[:1000],
            )
            await send_connector_dead_letter({**job, "attempts": attempt}, error_class, error_message)
            connector_jobs_total.labels(provider=job["provider"], action=job["action"], status="dead_lettered").inc()
            return

        delay = settings.CONNECTOR_BACKOFF_SECONDS[min(attempt - 1, len(settings.CONNECTOR_BACKOFF_SECONDS) - 1)]
        next_run_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
        await db.pool.execute(
            """UPDATE connector_jobs
               SET status = 'retrying', next_run_at = $2, last_error = $3, updated_at = timezone('utc'::text, now())
               WHERE id = $1""",
            job_id,
            next_run_at,
            error_message[:1000],
        )
        await schedule_connector_job(job_id, next_run_at)
        connector_jobs_total.labels(provider=job["provider"], action=job["action"], status="retrying").inc()


async def connector_schedule_loop():
    while True:
        try:
            await promote_due_connector_jobs()
            await asyncio.sleep(settings.CONNECTOR_SCHEDULER_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            break
        except Exception:
            logger.error("Connector scheduler error", exc_info=True)
            await asyncio.sleep(settings.CONNECTOR_SCHEDULER_INTERVAL_SECONDS)


async def start_connector_worker():
    logger.info("Connector worker started, waiting for jobs...")
    scheduler_task = asyncio.create_task(connector_schedule_loop())
    try:
        while True:
            job_id = None
            stream_id = None
            try:
                job_id, stream_id = await dequeue_connector_job()
                if not job_id:
                    continue
                if not await should_process_connector_job(job_id):
                    await ack_connector_job(stream_id)
                    continue
                await process_connector_job(job_id)
                await release_connector_job_lock(job_id)
                await ack_connector_job(stream_id)
            except Exception:
                logger.error("Connector worker error", exc_info=True)
                if job_id:
                    await release_connector_job_lock(job_id)
    except asyncio.CancelledError:
        raise
    finally:
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass
