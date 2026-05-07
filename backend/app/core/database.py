import os
import asyncpg
from dotenv import load_dotenv
from app.core.logging import get_logger

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
logger = get_logger("database")

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        if not self.pool:
            if not DATABASE_URL:
                logger.warning("DATABASE_URL not configured. Database integrations disabled.")
                return

            logger.info("Connecting to database")
            self.pool = await asyncpg.create_pool(
                dsn=DATABASE_URL,
                min_size=1,
                max_size=10,
                # Supabase pgBouncer on port 6543 uses transaction mode
                # which breaks prepared statements, so disable them.
                statement_cache_size=0,
                command_timeout=60,
                server_settings={'statement_timeout': '60000'}
            )
            logger.info("Database connected")

    async def disconnect(self):
        if self.pool:
            logger.info("Disconnecting from database")
            await self.pool.close()

db = Database()
