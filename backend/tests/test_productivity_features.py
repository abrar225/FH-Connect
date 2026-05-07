import asyncio
import json

import httpx

from app.main import app
from app.modules.productivity import service
from app.core.auth import AuthUser, get_current_user


async def _request(method: str, url: str, **kwargs):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.request(method, url, **kwargs)


def test_productivity_endpoints_require_authentication():
    endpoints = [
        ("GET", "/api/meetings"),
        ("GET", "/api/actions"),
        ("GET", "/api/recordings"),
        ("GET", "/api/reports"),
        ("GET", "/api/settings"),
        ("GET", "/api/integrations"),
        ("POST", "/api/meeting/room-a/copilot"),
        ("GET", "/api/meeting/room-a/ai-health"),
        ("POST", "/api/reports/room-a/share"),
    ]

    for method, url in endpoints:
        response = asyncio.run(_request(method, url, json={"question": "summary"} if method == "POST" else None))
        assert response.status_code == 401


def test_report_exports_generate_real_file_bytes():
    meeting = {
        "room_id": "room-a",
        "title": "Launch Review",
        "report_content": json.dumps({
            "executive_summary": "Clear launch path.",
            "key_decisions": ["Ship beta"],
            "tasks": [{"title": "Prepare rollout", "assignee": "Ava", "deadline": None, "status": "approved"}],
            "participation": {"Ava": 2},
            "meeting_minutes": "Discussed readiness.",
        }),
    }

    markdown = service._report_to_markdown(meeting)
    pdf = service._markdown_to_pdf_bytes(markdown)
    docx = service._markdown_to_docx_bytes(markdown)

    assert "# Launch Review" in markdown
    assert "Ship beta" in markdown
    assert pdf.startswith(b"%PDF")
    assert docx.startswith(b"PK")


def test_heuristic_insights_capture_core_categories():
    transcript = (
        "We decided to ship beta next week. "
        "Rahul will prepare onboarding by Friday. "
        "Risk: billing migration may slip. "
        "Question: who owns customer comms? "
        "Follow up with design."
    )

    insights = service._heuristic_insights(transcript)
    insight_types = {item["type"] for item in insights}

    assert {"decision", "action_item", "risk", "question", "follow_up"}.issubset(insight_types)


def test_settings_payload_accepts_json_string_dicts():
    payload = service.SettingsPayload.model_validate({
        "profile": '{"name":"Abrar","email":"user@example.com"}',
        "notification_preferences": '{"email_summary":true}',
        "ai_preferences": '{"provider":"gemini","model":"gemini-2.5-flash"}',
        "security_preferences": '{"share_expiry_required":true}',
        "data_retention_days": 365,
    })

    assert payload.profile["name"] == "Abrar"
    assert payload.notification_preferences["email_summary"] is True
    assert payload.ai_preferences["provider"] == "gemini"
    assert payload.security_preferences["share_expiry_required"] is True


def test_normalize_settings_data_never_returns_json_strings_or_api_key():
    row = {
        "profile": '{"name":"Abrar"}',
        "notification_preferences": '{"email_summary":true}',
        "ai_preferences": '{"provider":"gemini","api_key":"secret"}',
        "security_preferences": '{"share_expiry_required":true}',
    }

    normalized = service._normalize_settings_data(row, {"gemini": {"configured": True, "last4": "1234"}})

    assert normalized["profile"] == {"name": "Abrar"}
    assert normalized["notification_preferences"] == {"email_summary": True}
    assert normalized["security_preferences"] == {"share_expiry_required": True}
    assert "api_key" not in normalized["ai_preferences"]
    assert normalized["ai_preferences"]["api_key_status"]["gemini"]["configured"] is True


def test_meeting_ai_health_reports_missing_ai_key(monkeypatch):
    from app.modules.meeting import summary

    async def fake_user():
        return AuthUser(id="user-a", email="user@example.com")

    async def no_user_ai_config(_user_id):
        return None

    app.dependency_overrides[get_current_user] = fake_user
    monkeypatch.setattr(summary, "get_user_ai_runtime_config", no_user_ai_config)
    monkeypatch.setattr(summary.settings, "GEMINI_API_KEY", "")
    monkeypatch.setattr(summary.settings, "GROQ_API_KEY", "")
    monkeypatch.setattr(summary.settings, "DEEPGRAM_API_KEY", "")
    monkeypatch.delenv("DEEPGRAM_TEMP_KEY", raising=False)

    try:
        response = asyncio.run(_request("GET", "/api/meeting/room-a/ai-health"))
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["overall"] == "unavailable"
    assert body["checks"]["ai_provider"]["ok"] is False
    assert body["checks"]["transcription"]["ok"] is False
