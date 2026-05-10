import asyncio
import json
from datetime import datetime, timezone
from urllib.parse import urlencode

import websockets
from livekit.rtc import Room, AudioStream, TrackKind
from app.core.logging import get_logger
from app.core.event_bus import bus, Event
from app.core.constants import EventTypes
from app.core.ids import new_trace_id
from app.core.database import db
from app.core.config import settings
from app.gateway.ws.manager import manager
from app.modules.observability import metrics
from app.workers.audio_leases import renew_audio_worker_lease

logger = get_logger("audio_worker")

async def fetch_room_context(room_id: str):
    """Fetch meeting metadata used for transcription keyword boosting."""
    if not db.pool:
        return "FireHox"
        
    record = await db.pool.fetchrow(
        "SELECT title FROM meetings WHERE room_id = $1",
        room_id
    )
    if record:
        return record["title"] or "FireHox"
    return "FireHox"


def _participant_display_name(participant) -> str:
    return (getattr(participant, "name", None) or getattr(participant, "identity", None) or "Unknown").strip()


def _active_user_names(room: Room, current_participant) -> list[str]:
    """Build a best-effort active speaker list from LiveKit participant names."""
    names = {_participant_display_name(current_participant)}
    for participant in getattr(room, "remote_participants", {}).values():
        name = _participant_display_name(participant)
        if name and not name.startswith("transcription_bot_"):
            names.add(name)
    return sorted(names)


def _is_audio_track(track) -> bool:
    return getattr(track, "kind", None) in (TrackKind.KIND_AUDIO, "audio")


async def _broadcast_transcript(room_id: str, payload: dict, is_final: bool) -> None:
    message = {
        "type": "TRANSCRIPT_FINAL" if is_final else "TRANSCRIPT_INTERIM",
        "payload": payload,
        # Legacy flat fields keep existing clients working during the transition.
        **payload,
    }
    await manager.broadcast(room_id, json.dumps(message))

async def process_track(room: Room, track, participant, room_id: str):
    """Pipes a single participant's audio track to a dedicated Deepgram WS."""
    user_id = participant.identity
    speaker_name = _participant_display_name(participant)
    logger.info(f"Subscribed to track for {speaker_name} ({user_id}) in room {room_id}")

    project_name = await fetch_room_context(room_id)
    active_users = _active_user_names(room, participant)
    
    # Format keywords with phonetic boosting
    keywords = [f"{user}:2" for user in active_users if user]
    if project_name:
        keywords.append(f"{project_name}:3")

    dg_api_key = settings.DEEPGRAM_API_KEY
    if not dg_api_key:
        logger.error("DEEPGRAM_API_KEY not set")
        return

    # No diarize flag needed since we segregate by track.
    query = {
        "model": "nova-2-meeting",
        "language": "en-IN",
        "smart_format": "true",
        "diarize": "false",
        "interim_results": "true",
        "endpointing": "300",
        "encoding": "linear16",
        "sample_rate": "48000",
        "channels": "1",
        "keywords": keywords,
    }
    url = f"wss://api.deepgram.com/v1/listen?{urlencode(query, doseq=True)}"
    headers = {"Authorization": f"Token {dg_api_key}"}

    audio_stream = AudioStream(track)
    frame_queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=settings.AUDIO_WORKER_FRAME_QUEUE_MAXSIZE)

    async def frame_reader():
        try:
            async for audio_event in audio_stream:
                frame_bytes = audio_event.frame.data.tobytes()
                if frame_queue.full():
                    try:
                        frame_queue.get_nowait()
                        metrics.deepgram_dropped_frames_total.labels(room_id=room_id).inc()
                    except asyncio.QueueEmpty:
                        pass
                frame_queue.put_nowait(frame_bytes)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            metrics.deepgram_dropped_frames_total.labels(room_id=room_id).inc()
            logger.error(f"Frame reader error for {speaker_name}", exc_info=e)
            raise

    async def sender(ws):
        try:
            while True:
                frame_bytes = await frame_queue.get()
                await ws.send(frame_bytes)
                metrics.deepgram_audio_frames_sent_total.labels(room_id=room_id).inc()
                metrics.deepgram_audio_bytes_sent_total.labels(room_id=room_id).inc(len(frame_bytes))
                audio_seconds = len(frame_bytes) / 96000
                estimated_cost = (audio_seconds / 3600) * settings.DEEPGRAM_COST_PER_AUDIO_HOUR
                if estimated_cost > 0:
                    metrics.deepgram_estimated_cost_usd_total.labels(room_id=room_id).inc(estimated_cost)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            metrics.deepgram_dropped_frames_total.labels(room_id=room_id).inc()
            logger.error(f"Sender error for {speaker_name}", exc_info=e)
            raise

    async def receiver(ws):
        nonlocal active_users
        current_utterance_id = None
        utterance_started_at = None
        try:
            async for message in ws:
                data = json.loads(message)
                if "channel" in data and "alternatives" in data["channel"]:
                    transcript = data["channel"]["alternatives"][0].get("transcript", "")
                    if not transcript:
                        continue
                    
                    is_final = data.get("is_final", False)
                    if not current_utterance_id:
                        current_utterance_id = new_trace_id()
                        utterance_started_at = datetime.now(timezone.utc)
                    sentence_id = current_utterance_id
                    active_users = _active_user_names(room, participant)
                    timestamp = datetime.now(timezone.utc).isoformat()

                    if is_final:
                        metrics.deepgram_transcript_final_total.labels(room_id=room_id).inc()
                        if utterance_started_at:
                            latency = (datetime.now(timezone.utc) - utterance_started_at).total_seconds()
                            metrics.deepgram_transcript_latency_seconds.labels(room_id=room_id).observe(latency)
                        formatted_transcript = f"Speaker ({speaker_name}): {transcript}"
                        trace_id = new_trace_id()
                        logger.debug(f"Final transcript from {speaker_name}: {transcript}")
                        
                        # Route to internal EventBus for LLM
                        await bus.emit(Event(
                            event_type=EventTypes.TRANSCRIPT_RECEIVED,
                            trace_id=trace_id,
                            meeting_id=room_id,
                            payload={
                                "id": sentence_id,
                                "text": formatted_transcript,
                                "speaker": speaker_name,
                                "user_id": user_id,
                                "room_id": room_id,
                                "active_users": active_users,
                                "is_final": True,
                                "source": "audio_worker",
                                "timestamp": timestamp,
                            }
                        ))
                    
                    # Route to frontend WS for live UI captions
                    if not is_final:
                        metrics.deepgram_transcript_interim_total.labels(room_id=room_id).inc()

                    await _broadcast_transcript(
                        room_id,
                        {
                            "id": sentence_id,
                            "text": transcript,
                            "speaker": speaker_name,
                            "user_id": user_id,
                            "room_id": room_id,
                            "is_final": is_final,
                            "timestamp": timestamp,
                        },
                        is_final,
                    )
                    if is_final or data.get("speech_final", False):
                        current_utterance_id = None
                        utterance_started_at = None
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Receiver error for {speaker_name}", exc_info=e)
            raise

    reconnect_delay = 1
    while True:
        try:
            # Specify the exact audio format LiveKit provides to Deepgram
            async with websockets.connect(url, additional_headers=headers) as ws:
                metrics.deepgram_ws_connect_total.labels(room_id=room_id).inc()
                logger.info(f"Deepgram WS connected for {speaker_name}")
                reconnect_delay = 1 # Reset delay on successful connection
                
                read_task = asyncio.create_task(frame_reader())
                send_task = asyncio.create_task(sender(ws))
                recv_task = asyncio.create_task(receiver(ws))
                
                done, pending = await asyncio.wait(
                    [read_task, send_task, recv_task],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                for task in pending:
                    task.cancel()
                await asyncio.gather(*pending, return_exceptions=True)
                
                for task in done:
                    task.result()  # Re-raise any exceptions from completed tasks
                    
        except asyncio.CancelledError:
            logger.info(f"Deepgram processing cancelled for {speaker_name}")
            break
        except Exception as e:
            metrics.deepgram_ws_reconnect_total.labels(room_id=room_id).inc()
            logger.error(f"Deepgram WS disconnected for {speaker_name}: {e}. Reconnecting in {reconnect_delay}s...")
            await asyncio.sleep(reconnect_delay)
            reconnect_delay = min(reconnect_delay * 2, 30)

async def run_room_audio_worker(room_id: str, livekit_url: str, token: str, lease=None):
    """
    Connects to a LiveKit room, subscribes to audio tracks, and spawns a processing task per track.
    This worker dies when the room is disconnected.
    """
    room = Room()
    track_tasks = {}
    disconnect_future = asyncio.Future()
    lease_task = None

    async def renew_lease_loop():
        if lease is None:
            return
        while True:
            await asyncio.sleep(settings.AUDIO_WORKER_LEASE_RENEW_INTERVAL_SECONDS)
            if not await renew_audio_worker_lease(lease):
                logger.warning(f"Audio worker lease lost for room {room_id}; disconnecting worker")
                if not disconnect_future.done():
                    disconnect_future.set_result(None)
                return

    @room.on("track_subscribed")
    def on_track_subscribed(track, publication, participant):
        if _is_audio_track(track):
            metrics.livekit_track_subscribed_total.labels(room_id=room_id).inc()
            task = asyncio.create_task(process_track(room, track, participant, room_id))
            track_tasks[track.sid] = task

    @room.on("track_unsubscribed")
    def on_track_unsubscribed(track, publication, participant):
        if _is_audio_track(track) and track.sid in track_tasks:
            track_tasks[track.sid].cancel()
            del track_tasks[track.sid]
            logger.info(f"Unsubscribed audio track for {participant.identity}")

    @room.on("disconnected")
    def on_disconnected():
        logger.info(f"Room {room_id} disconnected.")
        if not disconnect_future.done():
            disconnect_future.set_result(None)

    try:
        metrics.audio_worker_active.labels(room_id=room_id).set(1)
        if lease is not None:
            lease_task = asyncio.create_task(renew_lease_loop())
        await room.connect(livekit_url, token)
        logger.info(f"Audio worker connected to LiveKit room: {room_id}")
        
        # Wait until the room disconnects naturally or the worker is cancelled
        await disconnect_future

    except asyncio.CancelledError:
        logger.info(f"Audio worker for room {room_id} cancelled.")
    except Exception as e:
        logger.error(f"Error in LiveKit audio worker for room {room_id}: {e}")
    finally:
        metrics.audio_worker_active.labels(room_id=room_id).set(0)
        if lease_task:
            lease_task.cancel()
            await asyncio.gather(lease_task, return_exceptions=True)
        for task in track_tasks.values():
            task.cancel()
        await asyncio.gather(*track_tasks.values(), return_exceptions=True)
        await room.disconnect()
        logger.info(f"Audio worker cleanly exited for room: {room_id}")
