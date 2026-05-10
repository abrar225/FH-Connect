import asyncio
import inspect
from fastapi import APIRouter, Depends, HTTPException, Query
from livekit.api import AccessToken, VideoGrants
from app.core.auth import AuthUser, get_current_user
from app.core.config import settings
from app.core.database import db
from app.core.logging import get_logger
from app.core.permissions import Capability, require_capability

router = APIRouter()
logger = get_logger("livekit.api")

async def start_worker_if_needed(room_name: str, livekit_url: str, api_key: str, api_secret: str):
    from app.workers.audio_leases import acquire_audio_worker_lease, release_audio_worker_lease

    try:
        lease = await acquire_audio_worker_lease(room_name)
    except RuntimeError as exc:
        logger.error("Audio worker lease acquisition failed", exc_info=exc)
        raise HTTPException(status_code=503, detail="Distributed audio worker lease unavailable") from exc
    if lease is None:
        logger.info(f"Audio worker lease already owned for room: {room_name}")
        return

    logger.info(f"Starting audio worker for room: {room_name}")
    
    # Generate a token for the transcription bot
    bot_token = (
        AccessToken(api_key, api_secret)
        .with_identity(f"transcription_bot_{room_name}")
        .with_name("Transcription Bot")
        .with_grants(
            VideoGrants(
                room_join=True,
                room=room_name,
                can_subscribe=True,
                can_publish=False,
                hidden=True,
            )
        )
    ).to_jwt()
    
    async def worker_wrapper():
        try:
            from app.workers.audio_worker import run_room_audio_worker
            await run_room_audio_worker(room_name, livekit_url, bot_token, lease)
        except Exception as exc:
            logger.error(f"Audio worker crashed for room {room_name}", exc_info=exc)
        finally:
            await release_audio_worker_lease(lease)
            logger.info(f"Audio worker task removed for room: {room_name}")
            
    asyncio.create_task(worker_wrapper())


@router.get("/livekit/token")
async def get_livekit_token(
    room_name: str = Query(..., description="Name of the LiveKit room to join"),
    participant_name: str = Query(..., description="Display name of the participant"),
    current_user: AuthUser = Depends(get_current_user),
):
    """
    Generates a signed LiveKit access token so the frontend can join a room.
    """
    api_key = settings.LIVEKIT_API_KEY
    api_secret = settings.LIVEKIT_API_SECRET

    if not api_key or not api_secret:
        raise HTTPException(status_code=500, detail="LiveKit API credentials not configured")

    if db.pool:
        await require_capability(current_user, Capability.MEETING_JOIN, {"room_id": room_name})

    identity = current_user.id

    token = (
        AccessToken(api_key, api_secret)
        .with_identity(identity)
        .with_name(participant_name)
        .with_grants(
            VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
            )
        )
    )

    jwt_token = token.to_jwt()
    livekit_url = settings.LIVEKIT_URL

    # Spawn the backend audio worker if it isn't running yet
    worker_result = start_worker_if_needed(room_name, livekit_url, api_key, api_secret)
    if inspect.isawaitable(worker_result):
        await worker_result

    return {
        "token": jwt_token,
        "url": livekit_url,
        "room": room_name,
        "identity": identity,
    }
