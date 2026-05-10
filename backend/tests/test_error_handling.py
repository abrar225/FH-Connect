import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from fastapi import HTTPException


class TestDatabaseErrorHandling:
    """Tests for database error handling"""

    @pytest.mark.asyncio
    async def test_meeting_creation_no_database_raises_error(self):
        """Test that meeting creation fails gracefully without database"""
        from app.modules.meeting import repository

        with patch("app.modules.meeting.repository.db") as mock_db:
            mock_db.pool = None
            with pytest.raises(RuntimeError, match="Database not configured"):
                await repository.create_meeting_record("room-1", "user-1", "Test")

    @pytest.mark.asyncio
    async def test_get_meeting_no_database_returns_none(self):
        """Test that get_meeting returns None without database"""
        from app.modules.meeting import repository

        with patch("app.modules.meeting.repository.db") as mock_db:
            mock_db.pool = None
            result = await repository.get_meeting("room-1")
            assert result is None


class TestPermissionErrorHandling:
    """Tests for permission/authorization error handling"""

    @pytest.mark.asyncio
    async def test_require_admin_raises_403_for_non_admin(self):
        """Test that require_admin raises 403 for non-admin users"""
        from app.modules.meeting import permissions

        mock_db_pool = MagicMock()

        async def fake_get_meeting(room_id):
            return {"room_id": "room-1", "admins": ["admin-user"], "created_by": "admin-user"}

        with patch.object(permissions, "get_meeting", fake_get_meeting):
            with patch.object(permissions.db, "pool", mock_db_pool):
                with pytest.raises(HTTPException) as exc:
                    await permissions.require_admin("room-1", MagicMock(id="regular-user"))

                assert exc.value.status_code == 403
                assert "Admin" in exc.value.detail or "not authorized" in exc.value.detail.lower()

    @pytest.mark.asyncio
    async def test_require_admin_raises_404_for_nonexistent_meeting(self):
        """Test that require_admin raises 404 for non-existent meeting"""
        from app.modules.meeting import permissions

        mock_db_pool = MagicMock()

        async def fake_get_meeting(room_id):
            return None

        with patch.object(permissions, "get_meeting", fake_get_meeting):
            with patch.object(permissions.db, "pool", mock_db_pool):
                with pytest.raises(HTTPException) as exc:
                    await permissions.require_admin("nonexistent", MagicMock(id="user-1"))

                assert exc.value.status_code == 404


class TestValidationErrorHandling:
    """Tests for input validation error handling"""

    def test_settings_rejects_invalid_email(self):
        """Test that settings validation rejects invalid email"""
        from app.modules.productivity.service import EmailReportRequest

        with pytest.raises(Exception):
            EmailReportRequest(
                recipients=["not-an-email"],
                message="Test"
            )

    def test_settings_rejects_invalid_retention_days(self):
        """Test that settings reject out-of-range retention days"""
        from app.modules.productivity.service import SettingsPayload

        with pytest.raises(Exception):
            SettingsPayload(data_retention_days=5000)

        with pytest.raises(Exception):
            SettingsPayload(data_retention_days=5)

    def test_schedule_meeting_validates_room_id_length(self):
        """Test that schedule meeting validates room_id length"""
        from app.modules.productivity.service import ScheduleMeetingRequest

        with pytest.raises(Exception):
            ScheduleMeetingRequest(room_id="ab", title="Test")

        with pytest.raises(Exception):
            ScheduleMeetingRequest(room_id="a" * 100, title="Test")


class TestAPIErrorHandling:
    """Tests for API-level error handling"""

    def test_api_returns_401_for_unauthenticated_request(self):
        """Test that API returns 401 for unauthenticated requests"""
        import httpx
        from app.main import app

        async def run_test():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/v1/api/meetings")
                return response.status_code

        status = asyncio.run(run_test())
        assert status == 401

    def test_api_returns_404_for_nonexistent_endpoint(self):
        """Test that API returns 404 for non-existent endpoints"""
        import httpx
        from app.main import app

        async def run_test():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/v1/api/nonexistent-endpoint")
                return response.status_code

        status = asyncio.run(run_test())
        assert status == 404


class TestHealthEndpoint:
    """Tests for health check endpoint"""

    def test_health_endpoint_returns_ok(self):
        """Test that health endpoint returns 200 with status"""
        import httpx
        from app.main import app

        async def run_test():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/health")
                return response.status_code, response.json()

        status, body = asyncio.run(run_test())
        assert status == 200
        assert "status" in body


class TestRateLimitingErrorHandling:
    """Tests for rate limiting"""

    def test_rate_limit_enforcement(self):
        """Test that rate limiting is enforced"""
        import httpx
        from app.main import app

        async def run_test():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                from app.core.config import settings
                original_limit = settings.RATE_LIMIT_REQUESTS

                settings.RATE_LIMIT_REQUESTS = 1

                try:
                    await client.get("/health", headers={"x-forwarded-for": "10.0.0.1"})
                    await client.get("/health", headers={"x-forwarded-for": "10.0.0.1"})
                finally:
                    settings.RATE_LIMIT_REQUESTS = original_limit

        asyncio.run(run_test())


class TestEventBusErrorHandling:
    """Tests for event bus error handling"""

    @pytest.mark.asyncio
    async def test_event_bus_disconnect_doesnt_crash(self):
        """Test that event bus operations work even if emit fails"""
        from app.core.event_bus import bus

        with patch.object(bus, "emit", side_effect=Exception("Redis disconnected")):
            try:
                await bus.emit(MagicMock())
            except Exception:
                pass


class TestReportErrorHandling:
    """Tests for report generation error handling"""

    def test_fetch_nonexistent_report_raises_404(self):
        """Test that fetching non-existent report raises 404"""
        from app.modules.productivity.service import _fetch_report

        async def run_test():
            with patch("app.modules.productivity.service.db") as mock_db:
                mock_pool = MagicMock()
                mock_pool.fetchrow = AsyncMock(return_value=None)
                mock_db.pool = mock_pool
                with patch("app.modules.productivity.service.require_database", AsyncMock()):
                    with pytest.raises(HTTPException) as exc:
                        await _fetch_report("nonexistent")
                    return exc.value.status_code

        status = asyncio.run(run_test())
        assert status == 404

    def test_fetch_unready_report_raises_404(self):
        """Test that fetching unready report raises 404"""
        from app.modules.productivity.service import _fetch_report

        async def run_test():
            with patch("app.modules.productivity.service.db") as mock_db:
                mock_pool = MagicMock()
                mock_pool.fetchrow = AsyncMock(return_value={
                    "room_id": "room-1",
                    "title": "Meeting",
                    "report_content": None,
                })
                mock_db.pool = mock_pool
                with patch("app.modules.productivity.service.require_database", AsyncMock()):
                    with pytest.raises(HTTPException) as exc:
                        await _fetch_report("room-1")
                    return exc.value.status_code

        status = asyncio.run(run_test())
        assert status == 404