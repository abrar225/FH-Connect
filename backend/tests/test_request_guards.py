import asyncio

import httpx

from app.main import app


async def _request(method: str, url: str, **kwargs):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.request(method, url, **kwargs)


def test_oversized_request_is_rejected(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "MAX_REQUEST_BYTES", 8)

    response = asyncio.run(
        _request(
            "POST",
            "/api/transcript",
            content="too-large-body",
            headers={"content-length": "14", "content-type": "application/json"},
        )
    )

    assert response.status_code == 413


def test_invalid_content_length_is_rejected():
    response = asyncio.run(
        _request("POST", "/api/transcript", content="{}", headers={"content-length": "not-a-number"})
    )

    assert response.status_code == 400


def test_rate_limiter_rejects_after_threshold(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "RATE_LIMIT_REQUESTS", 1)
    monkeypatch.setattr(settings, "RATE_LIMIT_WINDOW_SECONDS", 60)

    headers = {"x-forwarded-for": "203.0.113.10"}
    first = asyncio.run(_request("GET", "/health", headers=headers))
    second = asyncio.run(_request("GET", "/health", headers=headers))

    assert first.status_code == 200
    assert second.status_code == 429


def test_request_id_is_returned_to_client():
    response = asyncio.run(_request("GET", "/health", headers={"x-request-id": "req-test-123"}))

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "req-test-123"
