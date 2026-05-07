import os
from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import AuthUser, get_current_user
from app.core.config import settings

router = APIRouter()

@router.get("/deepgram/token")
async def get_deepgram_token(current_user: AuthUser = Depends(get_current_user)):
    """
    Generates a short-lived temporary key for the frontend 
    to securely connect to Deepgram's real-time WebSocket.
    """
    deepgram_token = os.getenv("DEEPGRAM_TEMP_KEY") or settings.DEEPGRAM_API_KEY
    if not deepgram_token:
        raise HTTPException(status_code=501, detail="Temporary transcription token service is not configured")
    
    return {"token": deepgram_token}
