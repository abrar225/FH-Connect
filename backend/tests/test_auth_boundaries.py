import asyncio

import httpx

from app.main import app


async def _request(method: str, url: str, **kwargs):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.request(method, url, **kwargs)


def test_livekit_token_requires_authentication():
    response = asyncio.run(
        _request("GET", "/v1/api/livekit/token?room_name=abc-def-ghi&participant_name=Test")
    )

    assert response.status_code == 401


def test_legacy_transcript_ingest_route_is_removed():
    response = asyncio.run(
        _request(
            "POST",
            "/api/transcript",
            json={
                "id": "line-1",
                "text": "Please create a task",
                "speaker": "Test",
                "room_id": "abc-def-ghi",
            },
        )
    )

    assert response.status_code == 404


def test_legacy_deepgram_token_route_is_removed():
    response = asyncio.run(_request("GET", "/api/deepgram/token"))

    assert response.status_code == 404


def test_approval_list_requires_authentication():
    response = asyncio.run(_request("GET", "/v1/api/approval?room_id=abc-def-ghi"))

    assert response.status_code == 401
