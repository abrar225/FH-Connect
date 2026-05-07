import asyncio
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

async def create_tables():
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("Required DATABASE_URL not found. Skipping table creation.")
        return

    print("Connecting to Supabase to create tables...")
    # Cannot use prepared statements easily over pgBouncer, but simple CREATE TABLE is fine
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT,
            name TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
        );
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS meetings (
            room_id TEXT PRIMARY KEY,
            created_by TEXT NOT NULL,
            title TEXT NOT NULL DEFAULT 'Instant Meeting',
            admins TEXT[] DEFAULT '{}',
            started_at TIMESTAMP WITH TIME ZONE,
            scheduled_for TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
            is_locked BOOLEAN DEFAULT false,
            report_content JSONB,
            report_status TEXT DEFAULT 'none',
            report_error TEXT,
            report_requested_at TIMESTAMP WITH TIME ZONE,
            ended_at TIMESTAMP WITH TIME ZONE
        );
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS task_drafts (
            id UUID PRIMARY KEY,
            original_transcript TEXT NOT NULL,
            title TEXT NOT NULL,
            assignee TEXT,
            deadline TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            room_id TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
        );
        """)

        # Ensure meetings table has all required columns
        migrations = [
            "ALTER TABLE meetings ADD COLUMN IF NOT EXISTS report_content JSONB;",
            "ALTER TABLE meetings ADD COLUMN IF NOT EXISTS report_status TEXT DEFAULT 'none';",
            "ALTER TABLE meetings ADD COLUMN IF NOT EXISTS report_error TEXT;",
            "ALTER TABLE meetings ADD COLUMN IF NOT EXISTS report_requested_at TIMESTAMP WITH TIME ZONE;",
            "ALTER TABLE meetings ADD COLUMN IF NOT EXISTS ended_at TIMESTAMP WITH TIME ZONE;",
            "ALTER TABLE meetings ADD COLUMN IF NOT EXISTS admins TEXT[] DEFAULT '{}';",
            "ALTER TABLE meetings ADD COLUMN IF NOT EXISTS is_locked BOOLEAN DEFAULT false;",
            "ALTER TABLE meetings ADD COLUMN IF NOT EXISTS scheduled_for TIMESTAMP WITH TIME ZONE;",
            "ALTER TABLE meetings ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now());",
        ]
        for sql in migrations:
            try:
                await conn.execute(sql)
            except Exception as e:
                print(f"⚠️ Migration skipped: {e}")

        # Ensure task_drafts has room_id column
        try:
            await conn.execute("ALTER TABLE task_drafts ADD COLUMN IF NOT EXISTS room_id TEXT;")
        except Exception as e:
            print(f"⚠️ task_drafts migration skipped: {e}")

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            action TEXT NOT NULL,
            actor_id TEXT NOT NULL,
            room_id TEXT,
            target_id TEXT,
            metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
        );
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_room_created ON audit_logs (room_id, created_at DESC);")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_actor_created ON audit_logs (actor_id, created_at DESC);")

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS workspaces (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            owner_id TEXT NOT NULL,
            name TEXT NOT NULL,
            type TEXT NOT NULL DEFAULT 'personal',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
        );
        """)
        await conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_workspaces_owner_personal ON workspaces (owner_id) WHERE type = 'personal';")

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id TEXT PRIMARY KEY,
            profile JSONB NOT NULL DEFAULT '{}'::jsonb,
            notification_preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
            default_report_format TEXT NOT NULL DEFAULT 'markdown',
            ai_preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
            security_preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
            data_retention_days INTEGER NOT NULL DEFAULT 365,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
        );
        """)
        for sql in [
            "ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS profile JSONB NOT NULL DEFAULT '{}'::jsonb;",
            "ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS notification_preferences JSONB NOT NULL DEFAULT '{}'::jsonb;",
            "ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS default_report_format TEXT NOT NULL DEFAULT 'markdown';",
            "ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS ai_preferences JSONB NOT NULL DEFAULT '{}'::jsonb;",
            "ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS security_preferences JSONB NOT NULL DEFAULT '{}'::jsonb;",
            "ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS data_retention_days INTEGER NOT NULL DEFAULT 365;",
            "ALTER TABLE user_settings ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now());",
        ]:
            try:
                await conn.execute(sql)
            except Exception as e:
                print(f"⚠️ user_settings migration skipped: {e}")

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS meeting_agendas (
            room_id TEXT PRIMARY KEY,
            goals JSONB NOT NULL DEFAULT '[]'::jsonb,
            agenda_items JSONB NOT NULL DEFAULT '[]'::jsonb,
            expected_decisions JSONB NOT NULL DEFAULT '[]'::jsonb,
            attendees JSONB NOT NULL DEFAULT '[]'::jsonb,
            prep_docs JSONB NOT NULL DEFAULT '[]'::jsonb,
            updated_by TEXT,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
        );
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS meeting_transcripts (
            id TEXT PRIMARY KEY,
            room_id TEXT NOT NULL,
            speaker TEXT NOT NULL,
            user_id TEXT,
            text TEXT NOT NULL,
            is_final BOOLEAN NOT NULL DEFAULT true,
            spoken_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
        );
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_meeting_transcripts_room_spoken ON meeting_transcripts (room_id, spoken_at);")

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS meeting_insights (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            room_id TEXT NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            detail TEXT,
            owner TEXT,
            deadline TEXT,
            status TEXT NOT NULL DEFAULT 'open',
            source_transcript_id TEXT,
            confidence REAL NOT NULL DEFAULT 0.75,
            created_by TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
        );
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_meeting_insights_room_type ON meeting_insights (room_id, type, status);")

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS meeting_quality_scores (
            room_id TEXT PRIMARY KEY,
            score REAL NOT NULL DEFAULT 0,
            agenda_followed REAL NOT NULL DEFAULT 0,
            decisions_made INTEGER NOT NULL DEFAULT 0,
            action_items_assigned INTEGER NOT NULL DEFAULT 0,
            unresolved_questions INTEGER NOT NULL DEFAULT 0,
            participation JSONB NOT NULL DEFAULT '{}'::jsonb,
            time_per_topic JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
        );
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS integrations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id TEXT NOT NULL,
            provider TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'disabled',
            config JSONB NOT NULL DEFAULT '{}'::jsonb,
            secret_ref TEXT,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
            UNIQUE(user_id, provider)
        );
        """)
        for sql in [
            "ALTER TABLE integrations ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'disabled';",
            "ALTER TABLE integrations ADD COLUMN IF NOT EXISTS config JSONB NOT NULL DEFAULT '{}'::jsonb;",
            "ALTER TABLE integrations ADD COLUMN IF NOT EXISTS secret_ref TEXT;",
            "ALTER TABLE integrations ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now());",
        ]:
            try:
                await conn.execute(sql)
            except Exception as e:
                print(f"⚠️ integrations migration skipped: {e}")

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS ai_provider_keys (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id TEXT NOT NULL,
            provider TEXT NOT NULL,
            encrypted_api_key TEXT NOT NULL,
            key_last4 TEXT,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
            UNIQUE(user_id, provider)
        );
        """)
        for sql in [
            "ALTER TABLE ai_provider_keys ADD COLUMN IF NOT EXISTS key_last4 TEXT;",
            "ALTER TABLE ai_provider_keys ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now());",
        ]:
            try:
                await conn.execute(sql)
            except Exception as e:
                print(f"⚠️ ai_provider_keys migration skipped: {e}")

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS report_shares (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            room_id TEXT NOT NULL,
            token TEXT NOT NULL UNIQUE,
            created_by TEXT NOT NULL,
            expires_at TIMESTAMP WITH TIME ZONE,
            revoked_at TIMESTAMP WITH TIME ZONE,
            allow_download BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
        );
        """)
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_report_shares_room ON report_shares (room_id, created_at DESC);")

        print("✅ Tables created or already exist.")
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_tables())
