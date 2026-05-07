import asyncio
import unittest

import httpx

from app.main import app


class HealthEndpointTestCase(unittest.TestCase):
    def test_health_endpoint_returns_ok(self) -> None:
        async def run_request() -> tuple[int, dict[str, str]]:
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://testserver",
            ) as client:
                response = await client.get("/health")
                return response.status_code, response.json()

        status_code, payload = asyncio.run(run_request())

        self.assertEqual(status_code, 200)
        self.assertEqual(payload, {"status": "ok"})


if __name__ == "__main__":
    unittest.main()
