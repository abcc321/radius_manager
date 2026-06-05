import asyncio
from typing import Dict, Set
from fastapi import WebSocket
import json


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel: str = "radius"):
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        self.active_connections[channel].add(websocket)
        print(f"[WS] Client connected to {channel}. Total: {len(self.active_connections[channel])}")

    def disconnect(self, websocket: WebSocket, channel: str = "radius"):
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
            print(f"[WS] Client disconnected from {channel}. Total: {len(self.active_connections[channel])}")

    async def send_to_channel(self, channel: str, message: dict):
        if channel in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[channel]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    print(f"[WS] Send error: {e}")
                    disconnected.add(connection)

            for conn in disconnected:
                self.active_connections[channel].discard(conn)

    async def broadcast_radius_status(self, status: dict):
        message = {
            "type": "radius_status",
            "data": status,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.send_to_channel("radius", message)
        print(f"[WS] Broadcasted radius status: {status}")

    async def broadcast_communication_event(self, event_type: str, data: dict):
        message = {
            "type": "communication_event",
            "event": event_type,
            "data": data,
            "timestamp": asyncio.get_event_loop().time()
        }
        await self.send_to_channel("radius", message)
        print(f"[WS] Broadcasted communication event: {event_type}")


manager = ConnectionManager()
