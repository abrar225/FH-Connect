from app.modules.connectors.providers.common import integration_config, post_json


async def execute(job: dict) -> dict:
    config = await integration_config(job)
    webhook_url = config.get("webhook_url")
    access_token = config.get("access_token")
    if webhook_url:
        result = await post_json(webhook_url, dict(job.get("payload") or {}))
        return {
            "external_object_id": str(result.get("id") or job.get("id")),
            "external_object_url": result.get("htmlLink") or result.get("url"),
        }
    if access_token:
        raise RuntimeError("Calendar direct API execution needs OAuth client wiring before use")
    raise RuntimeError("Calendar webhook_url or OAuth access_token is required")
