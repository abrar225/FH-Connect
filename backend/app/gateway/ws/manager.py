from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import re

from app.core.logging import get_logger
from app.core.auth import get_websocket_user

router = APIRouter()
logger = get_logger("ws.manager")
ROOM_ID_RE = re.compile(r"^[A-Za-z0-9_-]{3,80}$")
USER_ID_RE = re.compile(r"^[A-Za-z0-9:_@.-]{1,128}$")
MAX_WS_MESSAGE_BYTES = 8192

class ConnectionManager:
    def __init__(self):
        # Store connections by room_id and user_id: {room_id: {user_id: [websocket]}}
        self.active_connections: Dict[str, Dict[str, List[WebSocket]]] = {}
        # Store latest pulse per room so late joiners get it immediately
        self.latest_pulse: Dict[str, str] = {}

    async def connect(self, room_id: str, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}
        
        if user_id not in self.active_connections[room_id]:
            self.active_connections[room_id][user_id] = []
            
        self.active_connections[room_id][user_id].append(websocket)
        
        # Send cached pulse to the newly connected client
        if room_id in self.latest_pulse:
            try:
                await websocket.send_text(self.latest_pulse[room_id])
            except Exception:
                pass

    def disconnect(self, room_id: str, user_id: str, websocket: WebSocket):
        if room_id in self.active_connections:
            if user_id in self.active_connections[room_id]:
                if websocket in self.active_connections[room_id][user_id]:
                    self.active_connections[room_id][user_id].remove(websocket)
                if not self.active_connections[room_id][user_id]:
                    del self.active_connections[room_id][user_id]
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def send_personal_message(self, room_id: str, target_user_id: str, message: str):
        """Send a message to all connections of a specific user in a room."""
        if room_id in self.active_connections and target_user_id in self.active_connections[room_id]:
            dead_connections = []
            for websocket in self.active_connections[room_id][target_user_id]:
                try:
                    await websocket.send_text(message)
                except Exception:
                    dead_connections.append(websocket)
            
            for conn in dead_connections:
                self.disconnect(room_id, target_user_id, conn)

    def set_latest_pulse(self, room_id: str, message: str):
        """Cache the latest pulse for a room so late joiners receive it."""
        self.latest_pulse[room_id] = message

    async def broadcast(self, room_id: str, message: str):
        """Broadcast to all connected clients in a specific room."""
        if room_id not in self.active_connections:
            return

        for user_id in list(self.active_connections[room_id].keys()):
            dead_connections = []
            for connection in self.active_connections[room_id][user_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    dead_connections.append(connection)
            
            # Clean up dead connections for this user
            for conn in dead_connections:
                self.disconnect(room_id, user_id, conn)

manager = ConnectionManager()

@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    user = await get_websocket_user(websocket)
    if not user:
        return

    user_id = user.id
    if not ROOM_ID_RE.fullmatch(room_id) or not USER_ID_RE.fullmatch(user_id):
        await websocket.close(code=1008, reason="Invalid room or user")
        return

    await manager.connect(room_id, user_id, websocket)
    logger.info(f"Client connected [room={room_id}, user={user_id}]")
    
    try:
        while True:
            data = await websocket.receive_text()
            if len(data.encode("utf-8")) > MAX_WS_MESSAGE_BYTES:
                await websocket.close(code=1009, reason="Message too large")
                return
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "error", "message": "Invalid message"}))
                continue
            
            # Handle real-time chat messages
            if message.get("type") == "CHAT_SEND":
                payload = message.get("payload", {})
                recipient_id = payload.get("recipientId", "ALL")
                
                outgoing_msg = json.dumps({
                    "type": "chat",
                    "id": payload.get("id"),
                    "senderId": user_id,
                    "senderName": str(payload.get("senderName", "Anonymous"))[:80],
                    "text": str(payload.get("text", ""))[:2000],
                    "timestamp": payload.get("timestamp"),
                    "recipientId": recipient_id,
                    "isPrivate": recipient_id != "ALL"
                })
                
                if recipient_id == "ALL":
                    await manager.broadcast(room_id, outgoing_msg)
                else:
                    # Send to targeted user
                    await manager.send_personal_message(room_id, recipient_id, outgoing_msg)
                    # Also echo back to the sender if sender is different person
                    if recipient_id != user_id:
                        await manager.send_personal_message(room_id, user_id, outgoing_msg)
            
            else:
                await manager.send_personal_message(
                    room_id,
                    user_id,
                    json.dumps({"type": "error", "message": "Unsupported message type"}),
                )
                
    except WebSocketDisconnect:
        manager.disconnect(room_id, user_id, websocket)
        logger.info(f"Client disconnected [room={room_id}, user={user_id}]")
    except Exception as e:
        manager.disconnect(room_id, user_id, websocket)
        logger.error(f"WebSocket error [room={room_id}, user={user_id}]", exc_info=e)
