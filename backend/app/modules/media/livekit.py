import os
from fastapi import APIRouter, Depends, HTTPException, Query
from livekit.api import AccessToken, VideoGrants
from app.core.auth import AuthUser, get_current_user

router = APIRouter()


@router.get("/livekit/token")
async def get_livekit_token(
    room_name: str = Query(..., description="Name of the LiveKit room to join"),
    participant_name: str = Query(..., description="Display name of the participant"),
    current_user: AuthUser = Depends(get_current_user),
):
    """
    Generates a signed LiveKit access token so the frontend can join a room.
    """
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    if not api_key or not api_secret:
        raise HTTPException(status_code=500, detail="LiveKit API credentials not configured")

    from app.core.database import db
    if db.pool:
        meeting_record = await db.pool.fetchrow(
            "SELECT is_locked, admins FROM meetings WHERE room_id = $1", 
            room_name
        )
        if meeting_record:
            is_locked = meeting_record["is_locked"]
            admins = meeting_record["admins"] or []
            if is_locked and current_user.id not in admins:
                raise HTTPException(status_code=403, detail="Meeting is locked")

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
    livekit_url = os.getenv("LIVEKIT_URL", "")

    return {
        "token": jwt_token,
        "url": livekit_url,
        "room": room_name,
        "identity": identity,
    }
