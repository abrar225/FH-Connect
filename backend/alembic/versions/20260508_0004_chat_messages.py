"""chat messages table

Revision ID: 20260508_0004
Revises: 20260508_0003
Create Date: 2026-05-08

"""

from alembic import op

revision = "20260508_0004"
down_revision = "20260508_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE IF NOT EXISTS meeting_chats (
        id TEXT PRIMARY KEY,
        room_id TEXT NOT NULL,
        sender_id TEXT NOT NULL,
        sender_name TEXT NOT NULL,
        message_text TEXT NOT NULL,
        recipient_id TEXT,
        is_private BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
        CONSTRAINT fk_meeting_chats_meeting FOREIGN KEY (room_id) REFERENCES meetings(room_id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_meeting_chats_room ON meeting_chats(room_id);
    """)


def downgrade() -> None:
    op.execute("""
    DROP TABLE IF NOT EXISTS meeting_chats;
    """)
