import asyncio
import base64
import json
import urllib.request

from app.core.database import db


async def integration_config(job: dict) -> dict:
    if not db.pool:
        return {}
    row = await db.pool.fetchrow(
        "SELECT config FROM integrations WHERE user_id = $1 AND provider = $2 AND status = 'enabled'",
        job["actor_id"],
        job["provider"],
    )
    if not row:
        return {}
    return dict(row["config"] or {})


async def post_json(url: str, payload: dict, headers: dict | None = None) -> dict:
    data = json.dumps(payload).encode()
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )

    def run():
        with urllib.request.urlopen(request, timeout=15) as response:
            body = response.read().decode() or "{}"
            try:
                return json.loads(body)
            except json.JSONDecodeError:
                return {"status": response.status, "body": body}

    return await asyncio.to_thread(run)


def basic_auth(email: str, token: str) -> str:
    encoded = base64.b64encode(f"{email}:{token}".encode()).decode()
    return f"Basic {encoded}"
