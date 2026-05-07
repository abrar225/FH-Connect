import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.event_bus import bus, Event
from app.core.constants import EventTypes
from app.core.ids import new_trace_id
import json
from app.core.auth import AuthUser, get_current_user
from app.modules.audit.repository import record_audit_event
from app.modules.meeting.permissions import require_admin, require_database
from app.modules.meeting.repository import create_meeting_record, set_admins, set_room_lock

router = APIRouter()


class CreateMeetingReq(BaseModel):
    room_id: str
    title: str = "Instant Meeting"


@router.post("/meeting/create")
async def create_meeting(req: CreateMeetingReq, current_user: AuthUser = Depends(get_current_user)):
    """Create a meeting record. Bypasses Supabase RLS by using the backend DB pool."""
    await require_database()
    result = await create_meeting_record(req.room_id, current_user.id, req.title)
    if result["status"] == "created":
        await record_audit_event(
            action="meeting.created",
            actor_id=current_user.id,
            room_id=req.room_id,
            metadata={"title": req.title},
        )
    return {"status": result["status"], "room_id": req.room_id, "admins": result.get("admins", [])}

class AdminActionReq(BaseModel):
    pass

@router.post("/meeting/{room_id}/lock")
async def toggle_room_lock(room_id: str, req: AdminActionReq, locked: bool = True, current_user: AuthUser = Depends(get_current_user)):
    await require_admin(room_id, current_user)
    await set_room_lock(room_id, locked)
    await record_audit_event(
        action="meeting.locked" if locked else "meeting.unlocked",
        actor_id=current_user.id,
        room_id=room_id,
        metadata={"is_locked": locked},
    )
        
    # Broadcast lock update via event bus
    lock_update_message = json.dumps({
        "type": "lock_update",
        "is_locked": locked,
    })
    await bus.emit(Event(
        event_type=EventTypes.MEETING_LOCK_UPDATED,
        trace_id=new_trace_id(),
        meeting_id=room_id,
        payload={"room_id": room_id, "broadcast_json": lock_update_message},
    ))
        
    return {"status": "success", "is_locked": locked}


class TargetUserReq(BaseModel):
    target_user_id: str

@router.post("/meeting/{room_id}/admin")
async def toggle_admin(room_id: str, req: TargetUserReq, is_admin: bool = True, current_user: AuthUser = Depends(get_current_user)):
    meeting = await require_admin(room_id, current_user)
    admins = list(meeting.get("admins") or [])

    if is_admin:
        if req.target_user_id not in admins:
            admins.append(req.target_user_id)
    else:
        if req.target_user_id == current_user.id and len(admins) <= 1:
            raise HTTPException(status_code=400, detail="Meeting must keep at least one admin")
        if req.target_user_id in admins:
            admins.remove(req.target_user_id)

    await set_admins(room_id, admins)
    await record_audit_event(
        action="meeting.admin_granted" if is_admin else "meeting.admin_revoked",
        actor_id=current_user.id,
        room_id=room_id,
        target_id=req.target_user_id,
        metadata={"admins": admins},
    )
    
    # Broadcast admin change via event bus
    admin_update_message = json.dumps({
        "type": "admin_update",
        "admins": admins,
    })
    await bus.emit(Event(
        event_type=EventTypes.MEETING_ADMIN_UPDATED,
        trace_id=new_trace_id(),
        meeting_id=room_id,
        payload={"room_id": room_id, "broadcast_json": admin_update_message},
    ))
        
    return {"status": "success", "admins": admins}


@router.post("/meeting/{room_id}/mute-all")
async def mute_all(room_id: str, req: AdminActionReq, current_user: AuthUser = Depends(get_current_user)):
    await require_admin(room_id, current_user)

    # Mute using Livekit API
    from livekit import api
    livekit_url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    client = api.LiveKitAPI(livekit_url, api_key, api_secret)
    try:
        # Use ListParticipantsRequest from the package
        res = await client.room.list_participants(api.ListParticipantsRequest(room=room_id))
        participants = res.participants
        
        for p in participants:
            if p.identity != current_user.id:  # Do not mute the admin themselves
                # Need to mute their tracks
                for track in p.tracks:
                    if track.type == api.TrackType.AUDIO:
                        await client.room.mute_published_track(
                            api.MuteRoomTrackRequest(
                                room=room_id,
                                identity=p.identity,
                                track_sid=track.sid,
                                muted=True
                            )
                        )
    except HTTPException:
        raise
    except Exception:
        await client.aclose()
        raise HTTPException(status_code=502, detail="Unable to mute participants")
        
    await client.aclose()
    await record_audit_event(action="meeting.mute_all", actor_id=current_user.id, room_id=room_id)
    return {"status": "success"}
@router.post("/meeting/{room_id}/mute-user")
async def mute_user(room_id: str, req: TargetUserReq, current_user: AuthUser = Depends(get_current_user)):
    await require_admin(room_id, current_user)

    from livekit import api
    livekit_url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    client = api.LiveKitAPI(livekit_url, api_key, api_secret)
    try:
        # Find the specific participant and mute them
        res = await client.room.list_participants(api.ListParticipantsRequest(room=room_id))
        participants = res.participants
        target_p = next((p for p in participants if p.identity == req.target_user_id), None)
        
        if target_p:
            for track in target_p.tracks:
                if track.type == api.TrackType.AUDIO:
                    await client.room.mute_published_track(
                        api.MuteRoomTrackRequest(
                            room=room_id,
                            identity=target_p.identity,
                            track_sid=track.sid,
                            muted=True
                        )
                    )
        else:
            raise HTTPException(status_code=404, detail="Participant not found")
    except HTTPException:
        raise
    except Exception:
        await client.aclose()
        raise HTTPException(status_code=502, detail="Unable to mute participant")
        
    await client.aclose()
    await record_audit_event(
        action="meeting.mute_user",
        actor_id=current_user.id,
        room_id=room_id,
        target_id=req.target_user_id,
    )
    return {"status": "success"}
