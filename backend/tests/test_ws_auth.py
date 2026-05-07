import asyncio

from app.core.auth import get_websocket_user


class FakeWebSocket:
    query_params = {}

    def __init__(self):
        self.close_code = None
        self.close_reason = None

    async def close(self, code: int, reason: str):
        self.close_code = code
        self.close_reason = reason


def test_websocket_rejects_missing_supabase_token():
    websocket = FakeWebSocket()

    user = asyncio.run(get_websocket_user(websocket))

    assert user is None
    assert websocket.close_code == 1008
    assert websocket.close_reason == "Authentication required"
