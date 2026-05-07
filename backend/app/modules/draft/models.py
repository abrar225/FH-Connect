from pydantic import BaseModel, Field
import uuid
from typing import Optional
from datetime import datetime, timezone

class TaskDraft(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    room_id: Optional[str] = ""
    original_transcript: str
    title: str
    assignee: Optional[str] = None
    deadline: Optional[str] = None
    status: str = "pending" # pending | approved | rejected
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
