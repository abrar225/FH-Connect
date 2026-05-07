import asyncio
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger("meeting.export")

class ExportRequest(BaseModel):
    task_id: str
    title: str
    assignee: Optional[str] = None
    platform: str # 'jira', 'linear', 'slack'

@router.post("/export", status_code=200)
async def export_task(req: ExportRequest):
    """
    Simulates exporting an approved task to an external platform.
    In a real app, this would use OAuth and call external APIs.
    """
    logger.info(f"Export requested [platform={req.platform}, task={req.task_id[:8]}]")
    
    # Simulate API latency
    await asyncio.sleep(1.5)
    
    return {
        "status": "success",
        "platform": req.platform,
        "external_url": f"https://{req.platform}.com/issue/{req.task_id[:8]}"
    }
