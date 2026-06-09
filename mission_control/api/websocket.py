"""WebSocket manager for real-time chat updates."""

from fastapi import WebSocket
from typing import Dict, Set
import json


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        # All active connections
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        """Accept and store a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove a disconnected WebSocket."""
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        """Send a message to all connected clients."""
        dead = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead.add(connection)
        # Clean up dead connections
        for conn in dead:
            self.active_connections.discard(conn)

    async def send_personal(self, websocket: WebSocket, message: dict):
        """Send a message to a specific client."""
        try:
            await websocket.send_json(message)
        except Exception:
            self.active_connections.discard(websocket)


# Singleton
ws_manager = ConnectionManager()
