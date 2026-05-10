from app.modules.connectors.providers.common import basic_auth, integration_config, post_json


async def execute(job: dict) -> dict:
    config = await integration_config(job)
    base_url = str(config.get("base_url") or "").rstrip("/")
    email = config.get("email")
    api_token = config.get("api_token")
    project_key = config.get("project_key")
    if not all([base_url, email, api_token, project_key]):
        raise RuntimeError("Jira base_url, email, api_token, and project_key are required")

    payload = dict(job.get("payload") or {})
    summary = payload.get("title") or payload.get("summary") or "FH-Connect task"
    description = payload.get("description") or payload.get("text") or ""
    body = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": payload.get("issue_type") or "Task"},
        }
    }
    result = await post_json(
        f"{base_url}/rest/api/2/issue",
        body,
        headers={"Authorization": basic_auth(email, api_token)},
    )
    key = result.get("key") or result.get("id")
    return {
        "external_object_id": str(key or job.get("id")),
        "external_object_url": f"{base_url}/browse/{key}" if key else None,
    }
