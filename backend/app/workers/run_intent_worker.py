import asyncio

from dotenv import load_dotenv

from app.core.database import db
from app.core.event_bus import bus
from app.core.logging import get_logger
from app.workers.intent_worker import start_intent_worker
from app.workers.queue import connect_intent_queue, disconnect_intent_queue

load_dotenv()

logger = get_logger("intent_worker_process")


def _register_worker_event_handlers() -> None:
    """
    Worker-side event wiring.

    The worker consumes intent requests directly from the queue, then emits
    intent.detected into the same modular event bus pipeline used by the API.
    """
    import app.modules.draft.handlers
    import app.modules.notification.handlers


async def main() -> None:
    logger.info("Starting standalone intent worker process.")
    await db.connect()
    await bus.connect()
    await connect_intent_queue()
    _register_worker_event_handlers()

    try:
        await start_intent_worker()
    finally:
        await disconnect_intent_queue()
        await bus.disconnect()
        await db.disconnect()
        logger.info("Standalone intent worker process stopped.")


if __name__ == "__main__":
    asyncio.run(main())
