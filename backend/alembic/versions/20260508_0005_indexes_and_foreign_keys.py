"""add indexes and foreign keys for production performance

Revision ID: 20260508_0005
Revises: 20260508_0004
Create Date: 2026-05-08

Adds missing performance indexes on frequently queried columns
and foreign key constraints with ON DELETE CASCADE for referential
integrity.

Safety: All statements use IF NOT EXISTS / ADD IF NOT EXISTS patterns
so this migration is idempotent and safe to re-run.
"""

from alembic import op

revision = "20260508_0005"
down_revision = "20260508_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Performance Indexes ──────────────────────────────────────────────
    op.execute("""
    -- meetings.created_by is used in every list query (dashboard, recordings, reports)
    CREATE INDEX IF NOT EXISTS idx_meetings_created_by ON meetings (created_by);

    -- meeting_chats: compound index for the chat history query
    CREATE INDEX IF NOT EXISTS idx_meeting_chats_room_created ON meeting_chats (room_id, created_at DESC);

    -- meeting_insights: used by the actions list endpoint
    CREATE INDEX IF NOT EXISTS idx_meeting_insights_room_created ON meeting_insights (room_id, created_at DESC);
    """)

    # ── Foreign Key Constraints ──────────────────────────────────────────
    # Using DO $$ blocks to safely add constraints only if they don't exist.
    op.execute("""
    DO $$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.table_constraints
            WHERE constraint_name = 'fk_task_drafts_meeting'
              AND table_name = 'task_drafts'
        ) THEN
            ALTER TABLE task_drafts
                ADD CONSTRAINT fk_task_drafts_meeting
                FOREIGN KEY (room_id) REFERENCES meetings(room_id) ON DELETE CASCADE;
        END IF;
    END $$;

    DO $$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.table_constraints
            WHERE constraint_name = 'fk_meeting_transcripts_meeting'
              AND table_name = 'meeting_transcripts'
        ) THEN
            ALTER TABLE meeting_transcripts
                ADD CONSTRAINT fk_meeting_transcripts_meeting
                FOREIGN KEY (room_id) REFERENCES meetings(room_id) ON DELETE CASCADE;
        END IF;
    END $$;

    DO $$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.table_constraints
            WHERE constraint_name = 'fk_meeting_insights_meeting'
              AND table_name = 'meeting_insights'
        ) THEN
            ALTER TABLE meeting_insights
                ADD CONSTRAINT fk_meeting_insights_meeting
                FOREIGN KEY (room_id) REFERENCES meetings(room_id) ON DELETE CASCADE;
        END IF;
    END $$;

    DO $$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.table_constraints
            WHERE constraint_name = 'fk_meeting_agendas_meeting'
              AND table_name = 'meeting_agendas'
        ) THEN
            ALTER TABLE meeting_agendas
                ADD CONSTRAINT fk_meeting_agendas_meeting
                FOREIGN KEY (room_id) REFERENCES meetings(room_id) ON DELETE CASCADE;
        END IF;
    END $$;

    DO $$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.table_constraints
            WHERE constraint_name = 'fk_meeting_quality_scores_meeting'
              AND table_name = 'meeting_quality_scores'
        ) THEN
            ALTER TABLE meeting_quality_scores
                ADD CONSTRAINT fk_meeting_quality_scores_meeting
                FOREIGN KEY (room_id) REFERENCES meetings(room_id) ON DELETE CASCADE;
        END IF;
    END $$;

    DO $$ BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.table_constraints
            WHERE constraint_name = 'fk_report_shares_meeting'
              AND table_name = 'report_shares'
        ) THEN
            ALTER TABLE report_shares
                ADD CONSTRAINT fk_report_shares_meeting
                FOREIGN KEY (room_id) REFERENCES meetings(room_id) ON DELETE CASCADE;
        END IF;
    END $$;
    """)


def downgrade() -> None:
    op.execute("""
    ALTER TABLE report_shares DROP CONSTRAINT IF EXISTS fk_report_shares_meeting;
    ALTER TABLE meeting_quality_scores DROP CONSTRAINT IF EXISTS fk_meeting_quality_scores_meeting;
    ALTER TABLE meeting_agendas DROP CONSTRAINT IF EXISTS fk_meeting_agendas_meeting;
    ALTER TABLE meeting_insights DROP CONSTRAINT IF EXISTS fk_meeting_insights_meeting;
    ALTER TABLE meeting_transcripts DROP CONSTRAINT IF EXISTS fk_meeting_transcripts_meeting;
    ALTER TABLE task_drafts DROP CONSTRAINT IF EXISTS fk_task_drafts_meeting;

    DROP INDEX IF EXISTS idx_meeting_insights_room_created;
    DROP INDEX IF EXISTS idx_meeting_chats_room_created;
    DROP INDEX IF EXISTS idx_meetings_created_by;
    """)
