"""
core/event_bus.py — Asynchronous Event Bus (Supports Redis)

This is the central nervous system of the modular monolith.
Modules publish events here. Other modules subscribe to event types
they care about. No module ever imports another module's service directly.

Design Decisions:
- Phase 2 implementation: purely in-process using asyncio.
- Phase 4 implementation: Upgraded to optionally use Redis for Pub/Sub
  and idempotency caching across multiple gateway instances.
- Handlers are fire-and-forget by default (errors are logged, not re-raised)
  to ensure one failing handler never blocks or crashes others.
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.core.config import settings

try:
    import redis.asyncio as redis
except ImportError:
    redis = None

logger = get_logger("event_bus")


# ─── Event Envelope ──────────────────────────────────────────────────────────

class Event(BaseModel):
    """
    Standard event envelope. Every event flowing through the system
    carries this metadata for tracing and idempotency.
    """
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    meeting_id: str = ""
    event_type: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    payload: Dict[str, Any] = {}


# ─── Handler Type ─────────────────────────────────────────────────────────────

# A handler is an async function that receives an Event and returns nothing.
EventHandler = Callable[[Event], Coroutine[Any, Any, None]]


# ─── Event Bus Implementation ────────────────────────────────────────────────

class EventBus:
    def __init__(self) -> None:
        self._handlers: Dict[str, List[EventHandler]] = {}
        # Local fallback cache
        self._processed_events: Set[str] = set()
        self._max_processed_cache: int = 10_000
        
        # Redis state
        self._redis = None
        self._pubsub = None
        self._listen_task = None
        self._channel = "fh_events"

    async def connect(self):
        """Connect to Redis if configured, otherwise use local mode."""
        if settings.REDIS_URL and redis:
            try:
                self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
                self._pubsub = self._redis.pubsub()
                await self._pubsub.subscribe(self._channel)
                self._listen_task = asyncio.create_task(self._listen_redis())
                logger.info("Event Bus connected to Redis for Pub/Sub")
            except Exception as e:
                logger.error(f"Failed to connect to Redis Event Bus: {e}. Falling back to local.")
                self._redis = None
        else:
            logger.info("Event Bus running in local-only mode (No Redis)")

    async def disconnect(self):
        """Clean up Redis connections."""
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
        if self._pubsub:
            await self._pubsub.unsubscribe(self._channel)
            await self._pubsub.close()
        if self._redis:
            await self._redis.aclose()

    async def _listen_redis(self):
        """Background task to listen for events from Redis."""
        try:
            async for message in self._pubsub.listen():
                if message["type"] == "message":
                    event_data = json.loads(message["data"])
                    event = Event(**event_data)
                    await self._handle_local(event, from_redis=True)
        except asyncio.CancelledError:
            logger.info("Redis listener cancelled")
        except Exception as e:
            logger.error(f"Redis listen error: {e}", exc_info=True)

    # ── Subscribe ─────────────────────────────────────────────────────────

    def on(self, event_type: str):
        def decorator(func: EventHandler) -> EventHandler:
            self.subscribe(event_type, func)
            return func
        return decorator

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.info(f"Handler '{handler.__qualname__}' subscribed to '{event_type}'")

    # ── Publish / Emit ────────────────────────────────────────────────────

    async def emit(self, event: Event) -> None:
        from app.core.constants import EventTypes
        # Events that need to cross instance boundaries (WS broadcasts)
        BROADCAST_EVENTS = {
            EventTypes.DRAFT_CREATED,
            EventTypes.DRAFT_UPDATED,
            EventTypes.DRAFT_CANCELLED,
            EventTypes.PULSE_GENERATED,
            EventTypes.MEETING_LOCK_UPDATED,
            EventTypes.MEETING_ADMIN_UPDATED,
            EventTypes.AGENDA_UPDATED,
            EventTypes.INSIGHT_CREATED,
            EventTypes.INSIGHT_UPDATED,
            EventTypes.REPORT_STATUS_UPDATED,
            EventTypes.QUALITY_SCORE_UPDATED,
        }

        # Local fallback Idempotency Check
        if event.event_id in self._processed_events:
            logger.debug(f"Duplicate event skipped via local cache: {event.event_id} ({event.event_type})")
            return

        self._processed_events.add(event.event_id)
        if len(self._processed_events) > self._max_processed_cache:
            evict_count = self._max_processed_cache // 2
            self._processed_events = set(list(self._processed_events)[evict_count:])

        if self._redis and event.event_type in BROADCAST_EVENTS:
            # Redis Idempotency Check
            cache_key = f"event:{event.event_id}"
            is_new = await self._redis.set(cache_key, "1", ex=3600, nx=True)
            if not is_new:
                logger.debug(f"Duplicate event skipped via Redis: {event.event_id} ({event.event_type})")
                return
            
            # Publish to Redis channel (which our own listener will pick up)
            logger.debug(f"Publishing to Redis: {event.event_type} [event={event.event_id[:8]}]")
            await self._redis.publish(self._channel, event.model_dump_json())
        else:
            # Process locally
            await self._handle_local(event, from_redis=False)

    async def _handle_local(self, event: Event, from_redis: bool = False):
        """Invoke all local handlers for the event."""
        handlers = self._handlers.get(event.event_type, [])
        if not handlers:
            logger.debug(f"No handlers for event type '{event.event_type}' (event_id={event.event_id})")
            return

        source = "Redis" if from_redis else "Local"
        logger.info(
            f"Handling '{event.event_type}' via {source} → {len(handlers)} handler(s) "
            f"[trace={event.trace_id[:8]}, event={event.event_id[:8]}]"
        )

        results = await asyncio.gather(
            *[self._safe_invoke(handler, event) for handler in handlers],
            return_exceptions=True,
        )

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(
                    f"Handler '{handlers[i].__qualname__}' failed for "
                    f"'{event.event_type}': {result}",
                    exc_info=result,
                )

    async def _safe_invoke(self, handler: EventHandler, event: Event) -> None:
        try:
            await handler(event)
        except Exception as e:
            raise

    # ── Introspection ─────────────────────────────────────────────────────

    def list_subscriptions(self) -> Dict[str, List[str]]:
        return {
            event_type: [h.__qualname__ for h in handlers]
            for event_type, handlers in self._handlers.items()
        }

    @property
    def processed_count(self) -> int:
        return len(self._processed_events)

# ─── Singleton ────────────────────────────────────────────────────────────────

bus = EventBus()
