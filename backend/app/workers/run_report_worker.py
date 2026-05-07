import asyncio

from dotenv import load_dotenv

from app.core.database import db
from app.core.logging import get_logger
from app.workers.report_queue import connect_report_queue, disconnect_report_queue
from app.workers.report_worker import start_report_worker

load_dotenv()

logger = get_logger("report_worker_process")


async def main() -> None:
    logger.info("Starting standalone report worker process.")
    await db.connect()
    await connect_report_queue()

    try:
        await start_report_worker()
    finally:
        await disconnect_report_queue()
        await db.disconnect()
        logger.info("Standalone report worker process stopped.")


if __name__ == "__main__":
    asyncio.run(main())
