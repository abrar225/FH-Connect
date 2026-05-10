import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.core.auth import AuthUser
from app.modules.productivity import service


class TestHeuristicInsights:
    """Tests for heuristic insight detection"""

    def test_insights_capture_decisions(self):
        """Test that decision keywords trigger decision insights"""
        transcript = "We decided to proceed with the launch plan"
        insights = service._heuristic_insights(transcript)
        types = {i["type"] for i in insights}
        assert "decision" in types

    def test_insights_capture_action_items(self):
        """Test that action keywords trigger action_item insights"""
        transcript = "Sarah will prepare the budget by Friday"
        insights = service._heuristic_insights(transcript)
        types = {i["type"] for i in insights}
        assert "action_item" in types

    def test_insights_capture_risks(self):
        """Test that risk keywords trigger risk insights"""
        transcript = "There's a risk that the timeline might slip"
        insights = service._heuristic_insights(transcript)
        types = {i["type"] for i in insights}
        assert "risk" in types

    def test_insights_capture_questions(self):
        """Test that question marks trigger question insights"""
        transcript = "Who will handle the customer onboarding?"
        insights = service._heuristic_insights(transcript)
        types = {i["type"] for i in insights}
        assert "question" in types

    def test_insights_capture_follow_ups(self):
        """Test that follow-up keywords trigger follow_up insights"""
        transcript = "Let's follow up on this next week"
        insights = service._heuristic_insights(transcript)
        types = {i["type"] for i in insights}
        assert "follow_up" in types

    def test_insights_limit_to_five(self):
        """Test that insights are limited to 5 max"""
        transcript = "We decided. Action: do this. Risk: that. Question? Follow up. Decision made."
        insights = service._heuristic_insights(transcript)
        assert len(insights) <= 5


class TestReportGeneration:
    """Tests for report generation functions"""

    def test_report_to_markdown_with_json_content(self):
        """Test markdown generation from JSON report content"""
        meeting = {
            "room_id": "room-1",
            "title": "Sprint Planning",
            "report_content": {
                "executive_summary": "Sprint planned successfully",
                "key_decisions": ["Use Scrum framework", "Two-week sprints"],
                "tasks": [
                    {"title": "Set up Jira", "assignee": "John", "deadline": "2024-01-15", "status": "approved"},
                ],
                "meeting_minutes": "All team members present",
            },
        }
        markdown = service._report_to_markdown(meeting)

        assert "# Sprint Planning" in markdown
        assert "Sprint planned successfully" in markdown
        assert "Use Scrum framework" in markdown
        assert "Set up Jira" in markdown
        assert "John" in markdown

    def test_report_to_markdown_with_string_content(self):
        """Test markdown generation from string report content"""
        meeting = {
            "room_id": "room-1",
            "title": "Quick Sync",
            "report_content": "Quick discussion about the bug fix",
        }
        markdown = service._report_to_markdown(meeting)
        assert "Quick discussion" in markdown

    def test_markdown_to_pdf_generates_valid_pdf(self):
        """Test PDF generation produces valid PDF header"""
        pdf_bytes = service._markdown_to_pdf_bytes("# Test Report\nContent here")
        assert pdf_bytes.startswith(b"%PDF")
        assert b"endobj" in pdf_bytes
        assert b"%%EOF" in pdf_bytes

    def test_markdown_to_docx_generates_valid_docx(self):
        """Test DOCX generation produces valid DOCX (ZIP) header"""
        docx_bytes = service._markdown_to_docx_bytes("# Test Document\nContent")
        assert docx_bytes.startswith(b"PK")
        assert b"word/document.xml" in docx_bytes


class TestSettingsPayload:
    """Tests for settings payload validation"""

    def test_settings_with_dict_profile(self):
        """Test settings accept dict profile"""
        payload = service.SettingsPayload.model_validate({
            "profile": {"name": "Test User", "email": "test@example.com"},
            "notification_preferences": {"email_summary": True},
            "ai_preferences": {"provider": "gemini"},
            "security_preferences": {"share_expiry_required": True},
            "data_retention_days": 90,
        })
        assert payload.profile["name"] == "Test User"
        assert payload.notification_preferences["email_summary"] is True

    def test_settings_with_json_string_profile(self):
        """Test settings accept JSON string profile"""
        payload = service.SettingsPayload.model_validate({
            "profile": '{"name": "Test User", "email": "test@example.com"}',
        })
        assert payload.profile["name"] == "Test User"

    def test_settings_default_data_retention(self):
        """Test settings have default data retention of 365 days"""
        payload = service.SettingsPayload()
        assert payload.data_retention_days == 365

    def test_settings_default_report_format(self):
        """Test settings default to markdown report format"""
        payload = service.SettingsPayload()
        assert payload.default_report_format == "markdown"

    def test_settings_validate_retention_range(self):
        """Test settings enforce 30-3650 day retention range"""
        with pytest.raises(Exception):
            service.SettingsPayload.model_validate({"data_retention_days": 10})

        with pytest.raises(Exception):
            service.SettingsPayload.model_validate({"data_retention_days": 5000})


class TestSettingsNormalization:
    """Tests for settings normalization"""

    def test_normalize_removes_api_key(self):
        """Test that normalized settings never expose API keys"""
        row = {
            "profile": {"name": "User"},
            "ai_preferences": {"provider": "gemini", "api_key": "secret-key-123"},
        }
        normalized = service._normalize_settings_data(row)
        assert "api_key" not in normalized["ai_preferences"]

    def test_normalize_includes_key_status(self):
        """Test that normalized settings include API key status"""
        row = {
            "profile": {"name": "User"},
            "ai_preferences": {"provider": "gemini"},
        }
        api_key_status = {"gemini": {"configured": True, "last4": "abc"}}
        normalized = service._normalize_settings_data(row, api_key_status)
        assert normalized["ai_preferences"]["api_key_status"]["gemini"]["configured"] is True


class TestQualityScoreCalculation:
    """Tests for quality score computation"""

    @pytest.mark.asyncio
    async def test_compute_quality_score_returns_dict(self):
        """Test compute_quality_score returns properly structured result"""
        mock_pool = AsyncMock()

        fetchrow_call_count = [0]
        async def mock_fetchrow(query, *args):
            fetchrow_call_count[0] += 1
            if fetchrow_call_count[0] == 1:
                return {"goals": ["goal1"], "agenda_items": ["item1"], "expected_decisions": []}
            else:
                return {"room_id": "room-1", "score": 75, "agenda_followed": 0.5, "decisions_made": 1, "action_items_assigned": 1, "unresolved_questions": 2, "participation": {}}

        mock_pool.fetchrow = mock_fetchrow
        mock_pool.fetch = AsyncMock(return_value=[])
        mock_pool.execute = AsyncMock()

        with patch("app.modules.productivity.service.db") as mock_db:
            mock_db.pool = mock_pool
            with patch("app.modules.productivity.service.bus") as mock_bus:
                mock_bus.emit = AsyncMock()
                result = await service.compute_quality_score("room-1")

                assert "score" in result
                assert "agenda_followed" in result
                assert result["score"] >= 0
                assert result["score"] <= 100


class TestInsightsOperations:
    """Tests for insight persistence"""

    @pytest.mark.asyncio
    async def test_persist_transcript_saves_transcript(self):
        """Test that persist_transcript_and_insights saves transcript"""
        mock_pool = AsyncMock()
        mock_pool.execute = AsyncMock()
        mock_pool.fetchrow = AsyncMock(return_value={"id": "insight-1"})

        payload = {
            "id": "transcript-1",
            "room_id": "room-1",
            "speaker": "User1",
            "text": "We decided to proceed",
            "is_final": True,
        }

        with patch("app.modules.productivity.service.db") as mock_db:
            mock_db.pool = mock_pool
            with patch("app.modules.productivity.service.bus") as mock_bus:
                mock_bus.emit = AsyncMock()
                await service.persist_transcript_and_insights(payload, "user-1")

                mock_pool.execute.assert_called()
                call_args = mock_pool.execute.call_args[0]
                assert "INSERT INTO meeting_transcripts" in call_args[0]

    @pytest.mark.asyncio
    async def test_persist_transcript_skips_non_final(self):
        """Test that non-final transcripts are skipped"""
        mock_pool = AsyncMock()

        payload = {
            "id": "transcript-1",
            "room_id": "room-1",
            "text": "Draft text",
            "is_final": False,
        }

        with patch("app.modules.productivity.service.db") as mock_db:
            mock_db.pool = mock_pool
            await service.persist_transcript_and_insights(payload, "user-1")

            mock_pool.execute.assert_not_called()


class TestReportMarkdownConversion:
    """Tests for report to markdown conversion"""

    def test_markdown_includes_all_sections(self):
        """Test markdown includes all required sections"""
        meeting = {
            "title": "Test Meeting",
            "report_content": {
                "executive_summary": "Summary text",
                "key_decisions": ["Decision 1", "Decision 2"],
                "tasks": [
                    {"title": "Task 1", "assignee": "User1"},
                    {"title": "Task 2", "assignee": "User2"},
                ],
                "meeting_minutes": "Minutes text",
            },
        }
        markdown = service._report_to_markdown(meeting)

        assert "# Test Meeting" in markdown
        assert "## Executive Summary" in markdown
        assert "## Key Decisions" in markdown
        assert "## Tasks" in markdown
        assert "## Meeting Minutes" in markdown

    def test_markdown_handles_empty_tasks(self):
        """Test markdown handles empty task list"""
        meeting = {
            "title": "Meeting",
            "report_content": {
                "executive_summary": "Summary",
                "key_decisions": [],
                "tasks": [],
                "meeting_minutes": "",
            },
        }
        markdown = service._report_to_markdown(meeting)
        assert "Summary" in markdown

    def test_markdown_handles_unassigned_tasks(self):
        """Test markdown handles tasks without assignee"""
        meeting = {
            "title": "Meeting",
            "report_content": {
                "executive_summary": "Summary",
                "key_decisions": [],
                "tasks": [{"title": "Some task", "assignee": None}],
                "meeting_minutes": "",
            },
        }
        markdown = service._report_to_markdown(meeting)
        assert "Some task" in markdown
        assert "Unassigned" in markdown