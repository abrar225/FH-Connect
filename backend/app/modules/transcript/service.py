"""
modules/transcript/service.py — HTTP API endpoint for transcript ingestion.

This is now a THIN GATEWAY. It does only:
  1. Accept the transcript payload
  2. Validate basic structure (Pydantic)
  3. Attach trace metadata
  4. Publish a transcript.received event to the Event Bus
  5. Return immediately (HTTP 202 Accepted)

All business logic (RBAC, intent detection, draft creation, broadcasting)
is handled by event handlers in their respective modules.
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import List

from app.core.event_bus import bus, Event
from app.core.constants import EventTypes
from app.core.ids import new_trace_id
from app.core.logging import get_logger
from app.core.auth import AuthUser, get_current_user

router = APIRouter()
logger = get_logger("transcript.api")


class TranscriptChunk(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    text: str = Field(min_length=1, max_length=4000)
    speaker: str = Field(default="Unknown", max_length=80)
    room_id: str = Field(default="", min_length=3, max_length=80)
    active_users: List[str] = Field(default_factory=list, max_length=100)
    is_final: bool = True


