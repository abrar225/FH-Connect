"""production hardening tables

Revision ID: 20260508_0002
Revises: 20260508_0001
Create Date: 2026-05-08
"""

from alembic import op

revision = "20260508_0002"
down_revision = "20260508_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE IF NOT EXISTS audio_worker_leases (
        room_id TEXT PRIMARY KEY,
        instance_id TEXT NOT NULL,
        fencing_token TEXT NOT NULL,
        lease_expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
        last_renewed_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
        created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
    );
    CREATE TABLE IF NOT EXISTS intent_clarifications (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        room_id TEXT NOT NULL,
        source_transcript TEXT NOT NULL,
        proposed_action TEXT NOT NULL,
        proposed_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
        confidence REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        requested_by TEXT,
        resolved_by TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
        resolved_at TIMESTAMP WITH TIME ZONE
    );
    CREATE INDEX IF NOT EXISTS idx_intent_clarifications_room_status ON intent_clarifications (room_id, status, created_at DESC);
    CREATE TABLE IF NOT EXISTS connector_jobs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        provider TEXT NOT NULL,
        action TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'queued',
        room_id TEXT,
        actor_id TEXT NOT NULL,
        payload JSONB NOT NULL DEFAULT '{}'::jsonb,
        payload_hash TEXT NOT NULL,
        attempts INTEGER NOT NULL DEFAULT 0,
        next_run_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
        last_error TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
    );
    CREATE INDEX IF NOT EXISTS idx_connector_jobs_status_next_run ON connector_jobs (status, next_run_at);
    CREATE TABLE IF NOT EXISTS connector_job_attempts (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        job_id UUID NOT NULL,
        attempt_number INTEGER NOT NULL,
        status TEXT NOT NULL,
        error_class TEXT,
        error_message TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
    );
    CREATE INDEX IF NOT EXISTS idx_connector_job_attempts_job ON connector_job_attempts (job_id, created_at DESC);
    CREATE TABLE IF NOT EXISTS connector_dead_letters (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        job_id UUID,
        provider TEXT NOT NULL,
        action TEXT NOT NULL,
        room_id TEXT,
        actor_id TEXT NOT NULL,
        payload_hash TEXT NOT NULL,
        error_class TEXT,
        error_message TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
    );
    """)


def downgrade() -> None:
    op.execute("""
    DROP TABLE IF EXISTS connector_dead_letters;
    DROP TABLE IF EXISTS connector_job_attempts;
    DROP TABLE IF EXISTS connector_jobs;
    DROP TABLE IF EXISTS intent_clarifications;
    DROP TABLE IF EXISTS audio_worker_leases;
    """)
