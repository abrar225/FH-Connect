import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.core.auth import AuthUser
from app.modules.meeting import repository


class TestMeetingRepository:
    """Unit tests for meeting repository functions"""

    @pytest.mark.asyncio
    async def test_create_meeting_record_success(self):
        """Test creating a new meeting creates record with correct fields"""
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value=None)
        mock_conn.execute = AsyncMock()

        async def mock_acquire():
            return mock_conn
        mock_pool.acquire = mock_acquire

        with patch("app.modules.meeting.repository.db") as mock_db:
            mock_db.pool = mock_pool
            result = await repository.create_meeting_record("room-test-1", "user-1", "Test Meeting")

            assert result["status"] == "created"
            assert result["room_id"] == "room-test-1"
            assert result["created_by"] == "user-1"
            assert "user-1" in result["admins"]
            assert result["is_locked"] is False

    @pytest.mark.asyncio
    async def test_create_meeting_record_already_exists(self):
        """Test creating existing meeting returns existing data"""
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        existing = {
            "room_id": "room-test-1",
            "created_by": "user-1",
            "admins": ["user-1"],
            "is_locked": False,
        }
        mock_conn.fetchrow = AsyncMock(return_value=existing)

        async def mock_acquire():
            return mock_conn
        mock_pool.acquire = mock_acquire

        with patch("app.modules.meeting.repository.db") as mock_db:
            mock_db.pool = mock_pool
            result = await repository.create_meeting_record("room-test-1", "user-1", "Test Meeting")

            assert result["status"] == "exists"
            mock_conn.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_meeting_record_no_database_raises_error(self):
        """Test that creating meeting without database raises runtime error"""
        with patch("app.modules.meeting.repository.db") as mock_db:
            mock_db.pool = None
            with pytest.raises(RuntimeError, match="Database not configured"):
                await repository.create_meeting_record("room-test-1", "user-1", "Test Meeting")

    @pytest.mark.asyncio
    async def test_get_meeting_returns_dict(self):
        """Test get_meeting returns correctly mapped dict"""
        mock_pool = AsyncMock()
        mock_pool.fetchrow = AsyncMock(return_value={
            "room_id": "room-1",
            "created_by": "user-1",
            "admins": ["user-1", "user-2"],
            "is_locked": True,
            "report_status": "completed",
            "report_error": None,
        })

        with patch("app.modules.meeting.repository.db") as mock_db:
            mock_db.pool = mock_pool
            result = await repository.get_meeting("room-1")

            assert result["room_id"] == "room-1"
            assert result["admins"] == ["user-1", "user-2"]
            assert result["is_locked"] is True

    @pytest.mark.asyncio
    async def test_get_meeting_returns_none_when_not_found(self):
        """Test get_meeting returns None when meeting doesn't exist"""
        mock_pool = AsyncMock()
        mock_pool.fetchrow = AsyncMock(return_value=None)

        with patch("app.modules.meeting.repository.db") as mock_db:
            mock_db.pool = mock_pool
            result = await repository.get_meeting("nonexistent")

            assert result is None

    @pytest.mark.asyncio
    async def test_get_meeting_returns_none_when_no_pool(self):
        """Test get_meeting returns None when database not connected"""
        with patch("app.modules.meeting.repository.db") as mock_db:
            mock_db.pool = None
            result = await repository.get_meeting("room-1")

            assert result is None

    @pytest.mark.asyncio
    async def test_set_room_lock_updates_lock_state(self):
        """Test set_room_lock executes update query"""
        mock_pool = AsyncMock()
        mock_pool.execute = AsyncMock()

        with patch("app.modules.meeting.repository.db") as mock_db:
            mock_db.pool = mock_pool
            await repository.set_room_lock("room-1", True)

            mock_pool.execute.assert_called_once()
            call_args = mock_pool.execute.call_args[0]
            assert "UPDATE meetings SET is_locked" in call_args[0]
            assert call_args[1] is True
            assert call_args[2] == "room-1"

    @pytest.mark.asyncio
    async def test_set_admins_updates_admins_list(self):
        """Test set_admins executes update with correct list"""
        mock_pool = AsyncMock()
        mock_pool.execute = AsyncMock()

        with patch("app.modules.meeting.repository.db") as mock_db:
            mock_db.pool = mock_pool
            new_admins = ["user-1", "user-2", "user-3"]
            await repository.set_admins("room-1", new_admins)

            mock_pool.execute.assert_called_once()
            call_args = mock_pool.execute.call_args[0]
            assert "UPDATE meetings SET admins" in call_args[0]
            assert call_args[1] == new_admins
            assert call_args[2] == "room-1"

    @pytest.mark.asyncio
    async def test_save_meeting_report_sets_completed_status(self):
        """Test save_meeting_report updates report content and status"""
        mock_pool = AsyncMock()
        mock_pool.execute = AsyncMock()

        with patch("app.modules.meeting.repository.db") as mock_db:
            mock_db.pool = mock_pool
            report_json = '{"summary": "Test report"}'
            await repository.save_meeting_report("room-1", report_json)

            mock_pool.execute.assert_called_once()
            call_args = mock_pool.execute.call_args[0]
            assert "report_content = " in call_args[0]
            assert "report_status = 'completed'" in call_args[0]
            assert call_args[1] == report_json
            assert call_args[2] == "room-1"

    @pytest.mark.asyncio
    async def test_set_report_status_queued_sets_timestamp(self):
        """Test set_report_status with queued sets requested_at"""
        mock_pool = AsyncMock()
        mock_pool.execute = AsyncMock()

        with patch("app.modules.meeting.repository.db") as mock_db:
            mock_db.pool = mock_pool
            await repository.set_report_status("room-1", "queued")

            mock_pool.execute.assert_called_once()
            call_args = mock_pool.execute.call_args[0]
            assert "report_requested_at" in call_args[0]
            assert call_args[1] == "queued"
            assert call_args[2] == "room-1"

    @pytest.mark.asyncio
    async def test_set_report_status_with_error(self):
        """Test set_report_status with error stores error message"""
        mock_pool = AsyncMock()
        mock_pool.execute = AsyncMock()

        with patch("app.modules.meeting.repository.db") as mock_db:
            mock_db.pool = mock_pool
            await repository.set_report_status("room-1", "failed", "AI timeout")

            mock_pool.execute.assert_called_once()
            call_args = mock_pool.execute.call_args[0]
            assert "report_status = $1" in call_args[0]
            assert call_args[1] == "failed"
            assert call_args[2] == "AI timeout"

    @pytest.mark.asyncio
    async def test_get_report_status_returns_status_shape(self):
        """Test get_report_status returns correct shape with has_report"""
        mock_pool = AsyncMock()
        mock_pool.fetchrow = AsyncMock(return_value={
            "room_id": "room-1",
            "report_status": "completed",
            "report_error": None,
            "report_requested_at": "2024-01-01T10:00:00",
            "ended_at": "2024-01-01T11:00:00",
            "has_report": True,
        })

        with patch("app.modules.meeting.repository.db") as mock_db:
            mock_db.pool = mock_pool
            result = await repository.get_report_status("room-1")

            assert result["room_id"] == "room-1"
            assert result["report_status"] == "completed"
            assert result["has_report"] is True


class TestMeetingStatus:
    """Tests for meeting status determination"""

    def test_room_status_ended_when_ended_at_exists(self):
        """Test that ended_at sets status to ended"""
        from app.modules.productivity.service import _room_status

        row = {"ended_at": "2024-01-01T10:00:00Z"}
        assert _room_status(row) == "ended"

    def test_room_status_scheduled_when_only_scheduled_for(self):
        """Test that only scheduled_for sets status to scheduled"""
        from app.modules.productivity.service import _room_status

        row = {"scheduled_for": "2024-01-01T10:00:00Z"}
        assert _room_status(row) == "scheduled"

    def test_room_status_scheduled_before_started(self):
        """Test scheduled takes precedence over started"""
        from app.modules.productivity.service import _room_status

        row = {
            "scheduled_for": "2024-01-01T10:00:00Z",
            "started_at": "2024-01-01T09:00:00Z",
        }
        assert _room_status(row) == "scheduled"

    def test_room_status_live_when_only_started(self):
        """Test that only started_at sets status to live"""
        from app.modules.productivity.service import _room_status

        row = {"started_at": "2024-01-01T10:00:00Z"}
        assert _room_status(row) == "live"

    def test_room_status_live_when_empty(self):
        """Test that empty row defaults to live"""
        from app.modules.productivity.service import _room_status

        row = {}
        assert _room_status(row) == "live"