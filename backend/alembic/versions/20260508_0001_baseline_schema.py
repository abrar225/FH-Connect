"""baseline schema

Revision ID: 20260508_0001
Revises:
Create Date: 2026-05-08
"""

from alembic import op

revision = "20260508_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT,
        name TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
    );
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
    CREATE INDEX IF NOT EXISTS idx_task_drafts_room_status ON task_drafts (room_id, status, created_at DESC);
    CREATE TABLE IF NOT EXISTS audit_logs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        action TEXT NOT NULL,
        actor_id TEXT NOT NULL,
        room_id TEXT,
        target_id TEXT,
        metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
    );
    CREATE INDEX IF NOT EXISTS idx_audit_logs_room_created ON audit_logs (room_id, created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_audit_logs_actor_created ON audit_logs (actor_id, created_at DESC);
    CREATE TABLE IF NOT EXISTS workspaces (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        owner_id TEXT NOT NULL,
        name TEXT NOT NULL,
        type TEXT NOT NULL DEFAULT 'personal',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
    );
    CREATE UNIQUE INDEX IF NOT EXISTS idx_workspaces_owner_personal ON workspaces (owner_id) WHERE type = 'personal';
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
    CREATE INDEX IF NOT EXISTS idx_meeting_transcripts_room_spoken ON meeting_transcripts (room_id, spoken_at);
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
    CREATE INDEX IF NOT EXISTS idx_meeting_insights_room_type ON meeting_insights (room_id, type, status);
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
    CREATE TABLE IF NOT EXISTS ai_provider_keys (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id TEXT NOT NULL,
        provider TEXT NOT NULL,
        encrypted_api_key TEXT NOT NULL,
        key_last4 TEXT,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
        UNIQUE(user_id, provider)
    );
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
    CREATE INDEX IF NOT EXISTS idx_report_shares_room ON report_shares (room_id, created_at DESC);
    """)


def downgrade() -> None:
    op.execute("""
    DROP TABLE IF EXISTS report_shares;
    DROP TABLE IF EXISTS ai_provider_keys;
    DROP TABLE IF EXISTS integrations;
    DROP TABLE IF EXISTS meeting_quality_scores;
    DROP TABLE IF EXISTS meeting_insights;
    DROP TABLE IF EXISTS meeting_transcripts;
    DROP TABLE IF EXISTS meeting_agendas;
    DROP TABLE IF EXISTS user_settings;
    DROP TABLE IF EXISTS workspaces;
    DROP TABLE IF EXISTS audit_logs;
    DROP TABLE IF EXISTS task_drafts;
    DROP TABLE IF EXISTS meetings;
    DROP TABLE IF EXISTS users;
    """)
