"""
main.py — Application factory for FH-Connect Backend.

Responsibilities:
  1. Initialize the FastAPI application
  2. Connect to the database on startup
  3. Register all event handlers (wiring the Event Bus)
  4. Include all HTTP/WS routers
  5. Provide a health/debug root endpoint
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.core.config import settings
from app.core.database import db
from app.core.event_bus import bus
from app.core.logging import get_logger
from app.core.middleware import RequestGuardMiddleware
from app.gateway.http.router import api_router

load_dotenv()

logger = get_logger("main")


def _register_event_handlers():
    """
    Import all handler modules to trigger their @bus.on() decorators.

    This is the central wiring point. Each import causes the handler
    functions to register themselves with the Event Bus.
    Adding or removing a handler module here is safe and isolated.
    """
    import app.modules.transcript.handlers    # transcript.received → intent.requested
    import app.modules.intelligence.handlers  # intent.requested → intent.detected
    import app.modules.draft.handlers         # intent.detected → draft.created/updated/cancelled
    import app.modules.notification.handlers  # draft.* → WebSocket broadcast

    logger.info("Event handlers registered:")
    for event_type, handlers in bus.list_subscriptions().items():
        for h in handlers:
            logger.info(f"  {event_type} → {h}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    await db.connect()
    from app.core.init_db import create_tables
    await create_tables()
    await bus.connect()
    from app.workers.queue import connect_intent_queue
    from app.workers.report_queue import connect_report_queue
    await connect_intent_queue()
    await connect_report_queue()
    _register_event_handlers()
    
    import asyncio
    if settings.RUN_EMBEDDED_WORKERS:
        # Development/local mode can run the worker inside the API process.
        # Production should set RUN_EMBEDDED_WORKERS=false and run dedicated workers.
        from app.workers.intent_worker import start_intent_worker
        from app.workers.report_worker import start_report_worker
        app.state.intent_worker_task = asyncio.create_task(start_intent_worker())
        app.state.report_worker_task = asyncio.create_task(start_report_worker())
        logger.info("Embedded workers enabled.")
    else:
        logger.info("Embedded workers disabled; expecting separate worker processes.")
    
    logger.info("Application ready.")
    yield
    # ── Teardown ──────────────────────────────────────────────────────────
    for worker_task_name in ("intent_worker_task", "report_worker_task"):
        worker_task = getattr(app.state, worker_task_name, None)
        if not worker_task:
            continue
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass
            
    await bus.disconnect()
    from app.workers.queue import disconnect_intent_queue
    from app.workers.report_queue import disconnect_report_queue
    await disconnect_intent_queue()
    await disconnect_report_queue()
    await db.disconnect()
    logger.info("Application shut down.")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url=None if settings.ENVIRONMENT == "production" else "/docs",
        redoc_url=None if settings.ENVIRONMENT == "production" else "/redoc",
        openapi_url=None if settings.ENVIRONMENT == "production" else "/openapi.json",
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestGuardMiddleware)

    app.include_router(api_router)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled request error", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    # ── Root health check ─────────────────────────────────────────────────
    @app.get("/")
    async def root():
        return {
            "name": settings.APP_NAME,
            "status": "ready",
            "version": settings.APP_VERSION,
            "database": "connected" if db.pool else "disconnected",
        }

    # ── Debug: Event Bus introspection ────────────────────────────────────
    @app.get("/debug/event-bus")
    async def debug_event_bus():
        """Returns all registered event subscriptions and stats."""
        return {
            "subscriptions": bus.list_subscriptions(),
            "processed_event_count": bus.processed_count,
        }

    return app


app = create_app()
