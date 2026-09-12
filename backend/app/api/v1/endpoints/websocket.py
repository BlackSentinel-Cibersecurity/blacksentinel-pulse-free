from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import json
import asyncio
from datetime import datetime

from app.core.security import decode_token
from app.core.cache import cache

router = APIRouter()


class ConnectionManager:
    """WebSocket connection manager for real-time updates."""

    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

    async def broadcast(self, message: dict):
        for user_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint with first-message authentication.
    Token is NEVER in the URL - it's sent as the first message after connection.
    """
    await websocket.accept()

    user_id = None
    try:
        # Wait for auth message (first message must be auth)
        auth_data = await asyncio.wait_for(websocket.receive_text(), timeout=10.0)
        auth_msg = json.loads(auth_data)

        if auth_msg.get("type") != "auth" or not auth_msg.get("token"):
            await websocket.send_json({"type": "error", "message": "Auth required"})
            await websocket.close(code=4001, reason="Auth required")
            return

        payload = decode_token(auth_msg["token"])
        if not payload or payload.get("type") != "access":
            await websocket.send_json({"type": "error", "message": "Invalid token"})
            await websocket.close(code=4001, reason="Invalid token")
            return

        user_id = int(payload.get("sub"))
        await manager.connect(websocket, user_id)

        await websocket.send_json({
            "type": "connected",
            "message": "Connected to BlackSentinel Pulse",
            "timestamp": datetime.utcnow().isoformat(),
        })

        heartbeat_task = asyncio.create_task(send_heartbeat(websocket))

        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "ping":
                await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})

            elif message.get("type") == "subscribe":
                channel = message.get("channel", "general")
                await websocket.send_json({"type": "subscribed", "channel": channel})

            elif message.get("type") == "unsubscribe":
                channel = message.get("channel", "general")
                await websocket.send_json({"type": "unsubscribed", "channel": channel})

    except asyncio.TimeoutError:
        await websocket.close(code=4001, reason="Auth timeout")
    except WebSocketDisconnect:
        if user_id:
            manager.disconnect(websocket, user_id)
    except Exception:
        if user_id:
            manager.disconnect(websocket, user_id)


async def send_heartbeat(websocket: WebSocket):
    """Send periodic heartbeats to keep connection alive."""
    while True:
        try:
            await asyncio.sleep(30)
            await websocket.send_json({
                "type": "heartbeat",
                "timestamp": datetime.utcnow().isoformat(),
            })
        except Exception:
            break


async def notify_asset_discovered(org_id: int, asset_data: dict):
    """Notify all connected users about a new asset discovery."""
    await manager.broadcast({
        "type": "asset_discovered",
        "organization_id": org_id,
        "data": asset_data,
        "timestamp": datetime.utcnow().isoformat(),
    })


async def notify_vulnerability_found(org_id: int, vuln_data: dict):
    """Notify about new vulnerability findings."""
    await manager.broadcast({
        "type": "vulnerability_found",
        "organization_id": org_id,
        "data": vuln_data,
        "timestamp": datetime.utcnow().isoformat(),
    })


async def notify_alert_created(org_id: int, alert_data: dict):
    """Notify about new alerts."""
    await manager.broadcast({
        "type": "alert_created",
        "organization_id": org_id,
        "data": alert_data,
        "timestamp": datetime.utcnow().isoformat(),
    })


async def notify_scan_progress(org_id: int, scan_id: str, progress: int, status: str):
    """Notify about scan progress updates."""
    await manager.broadcast({
        "type": "scan_progress",
        "organization_id": org_id,
        "scan_id": scan_id,
        "progress": progress,
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
    })
