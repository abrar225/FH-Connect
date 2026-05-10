from app.modules.connectors.providers.common import integration_config, post_json


async def execute(job: dict) -> dict:
    config = await integration_config(job)
    webhook_url = config.get("webhook_url")
    if not webhook_url:
        raise RuntimeError("Slack webhook_url is not configured")
    payload = dict(job.get("payload") or {})
    text = payload.get("text") or payload.get("message") or "FH-Connect connector notification"
    result = await post_json(webhook_url, {"text": text})
    return {
        "external_object_id": str(result.get("ts") or job.get("id")),
        "external_object_url": result.get("permalink"),
    }
