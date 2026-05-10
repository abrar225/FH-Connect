import os
import asyncpg
import json
from contextlib import asynccontextmanager
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
            async def init(conn):
                await conn.set_type_codec('jsonb', encoder=json.dumps, decoder=json.loads, schema='pg_catalog')
                await conn.set_type_codec('json', encoder=json.dumps, decoder=json.loads, schema='pg_catalog')

            self.pool = await asyncpg.create_pool(
                dsn=DATABASE_URL,
                min_size=1,
                max_size=10,
                statement_cache_size=0,
                command_timeout=60,
                server_settings={'statement_timeout': '60000'},
                init=init
            )
            logger.info("Database connected")

    async def disconnect(self):
        if self.pool:
            logger.info("Disconnecting from database")
            await self.pool.close()

    @asynccontextmanager
    async def transaction(self):
        """
        Provides a transaction context manager.
        Usage:
            async with db.transaction() as conn:
                await conn.execute(...)
        """
        if not self.pool:
            from app.core.exceptions import DatabaseUnavailableError
            raise DatabaseUnavailableError("Database pool not initialized")
        
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                yield conn

db = Database()
