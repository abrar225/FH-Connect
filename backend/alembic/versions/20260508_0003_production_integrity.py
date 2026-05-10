"""production integrity constraints

Revision ID: 20260508_0003
Revises: 20260508_0002
Create Date: 2026-05-08
"""

from alembic import op

revision = "20260508_0003"
down_revision = "20260508_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    ALTER TABLE connector_jobs ADD COLUMN IF NOT EXISTS idempotency_key TEXT;
    ALTER TABLE connector_jobs ADD COLUMN IF NOT EXISTS external_object_id TEXT;
    ALTER TABLE connector_jobs ADD COLUMN IF NOT EXISTS external_object_url TEXT;
    CREATE UNIQUE INDEX IF NOT EXISTS idx_connector_jobs_idempotency
      ON connector_jobs (provider, action, idempotency_key)
      WHERE idempotency_key IS NOT NULL;

    DO $$ BEGIN
      ALTER TABLE task_drafts ADD CONSTRAINT fk_task_drafts_meeting FOREIGN KEY (room_id) REFERENCES meetings(room_id) ON DELETE CASCADE;
    EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    DO $$ BEGIN
      ALTER TABLE meeting_transcripts ADD CONSTRAINT fk_meeting_transcripts_meeting FOREIGN KEY (room_id) REFERENCES meetings(room_id) ON DELETE CASCADE;
    EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    DO $$ BEGIN
      ALTER TABLE meeting_insights ADD CONSTRAINT fk_meeting_insights_meeting FOREIGN KEY (room_id) REFERENCES meetings(room_id) ON DELETE CASCADE;
    EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    DO $$ BEGIN
      ALTER TABLE meeting_agendas ADD CONSTRAINT fk_meeting_agendas_meeting FOREIGN KEY (room_id) REFERENCES meetings(room_id) ON DELETE CASCADE;
    EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    DO $$ BEGIN
      ALTER TABLE report_shares ADD CONSTRAINT fk_report_shares_meeting FOREIGN KEY (room_id) REFERENCES meetings(room_id) ON DELETE CASCADE;
    EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    DO $$ BEGIN
      ALTER TABLE connector_jobs ADD CONSTRAINT fk_connector_jobs_meeting FOREIGN KEY (room_id) REFERENCES meetings(room_id) ON DELETE SET NULL;
    EXCEPTION WHEN duplicate_object THEN NULL; END $$;

    DO $$ BEGIN
      ALTER TABLE task_drafts ADD CONSTRAINT chk_task_drafts_status CHECK (status IN ('pending', 'approved', 'rejected'));
    EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    DO $$ BEGIN
      ALTER TABLE meetings ADD CONSTRAINT chk_meetings_report_status CHECK (report_status IN ('none', 'queued', 'processing', 'completed', 'failed'));
    EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    DO $$ BEGIN
      ALTER TABLE connector_jobs ADD CONSTRAINT chk_connector_jobs_status CHECK (status IN ('queued', 'processing', 'succeeded', 'retrying', 'dead_lettered'));
    EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    DO $$ BEGIN
      ALTER TABLE intent_clarifications ADD CONSTRAINT chk_intent_clarifications_status CHECK (status IN ('pending', 'accepted', 'rejected', 'resolved'));
    EXCEPTION WHEN duplicate_object THEN NULL; END $$;
    """)


def downgrade() -> None:
    op.execute("""
    ALTER TABLE intent_clarifications DROP CONSTRAINT IF EXISTS chk_intent_clarifications_status;
    ALTER TABLE connector_jobs DROP CONSTRAINT IF EXISTS chk_connector_jobs_status;
    ALTER TABLE meetings DROP CONSTRAINT IF EXISTS chk_meetings_report_status;
    ALTER TABLE task_drafts DROP CONSTRAINT IF EXISTS chk_task_drafts_status;
    ALTER TABLE connector_jobs DROP CONSTRAINT IF EXISTS fk_connector_jobs_meeting;
    ALTER TABLE report_shares DROP CONSTRAINT IF EXISTS fk_report_shares_meeting;
    ALTER TABLE meeting_agendas DROP CONSTRAINT IF EXISTS fk_meeting_agendas_meeting;
    ALTER TABLE meeting_insights DROP CONSTRAINT IF EXISTS fk_meeting_insights_meeting;
    ALTER TABLE meeting_transcripts DROP CONSTRAINT IF EXISTS fk_meeting_transcripts_meeting;
    ALTER TABLE task_drafts DROP CONSTRAINT IF EXISTS fk_task_drafts_meeting;
    DROP INDEX IF EXISTS idx_connector_jobs_idempotency;
    ALTER TABLE connector_jobs DROP COLUMN IF EXISTS external_object_url;
    ALTER TABLE connector_jobs DROP COLUMN IF EXISTS external_object_id;
    ALTER TABLE connector_jobs DROP COLUMN IF EXISTS idempotency_key;
    """)
