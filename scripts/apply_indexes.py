import asyncio
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../backend/.env'))

async def create_indexes():
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        # Try finding in parent directory if the above failed
        load_dotenv()
        DATABASE_URL = os.getenv("DATABASE_URL")
        
    if not DATABASE_URL:
        print("Required DATABASE_URL not found in environment.")
        return

    print("Connecting to database to create indexes...")
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # Create composite index on task_drafts
        print("Creating idx_task_drafts_room_created...")
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_task_drafts_room_created 
            ON task_drafts (room_id, created_at DESC);
        """)
        
        # Create index on meetings created_by
        print("Creating idx_meetings_created_by...")
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_meetings_created_by 
            ON meetings (created_by);
        """)
        print("✅ Indexes created or already exist.")
    except Exception as e:
        print(f"❌ Failed to create indexes: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_indexes())
