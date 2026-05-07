from fastapi import APIRouter

from app.gateway.http.health import router as health_router
from app.gateway.ws.manager import router as websocket_router
from app.modules.transcript.service import router as transcript_router
from app.modules.approval.service import router as approval_router
from app.modules.media.livekit import router as livekit_router
from app.modules.meeting.summary import router as summary_router
from app.modules.meeting.export import router as export_router
from app.modules.transcript.deepgram import router as deepgram_router
from app.modules.meeting.service import router as meeting_admin_router
from app.modules.productivity.service import router as productivity_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(websocket_router)
api_router.include_router(transcript_router, prefix="/api")
api_router.include_router(approval_router, prefix="/api")
api_router.include_router(livekit_router, prefix="/api")
api_router.include_router(summary_router, prefix="/api")
api_router.include_router(export_router, prefix="/api")
api_router.include_router(deepgram_router, prefix="/api")
api_router.include_router(meeting_admin_router, prefix="/api")
api_router.include_router(productivity_router, prefix="/api")
