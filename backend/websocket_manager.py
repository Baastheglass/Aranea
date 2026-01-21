from fastapi import WebSocket
from typing import Dict
import json
from datetime import datetime

class WebSocketManager:
    def __init__(self):
        # Store active connections: session_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept and store a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        print(f"WebSocket connected: {session_id}")
    
    def disconnect(self, session_id: str):
        """Remove a WebSocket connection"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            print(f"WebSocket disconnected: {session_id}")
    
    async def send_event(self, session_id: str, event_type: str, data: dict):
        """Send an event to a specific session"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            event = {
                "event": event_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }
            try:
                await websocket.send_json(event)
            except Exception as e:
                print(f"Error sending event to {session_id}: {e}")
                self.disconnect(session_id)
    
    async def broadcast(self, event_type: str, data: dict):
        """Send an event to all connected sessions"""
        disconnected = []
        for session_id, websocket in self.active_connections.items():
            event = {
                "event": event_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }
            try:
                await websocket.send_json(event)
            except Exception as e:
                print(f"Error broadcasting to {session_id}: {e}")
                disconnected.append(session_id)
        
        # Clean up disconnected sessions
        for session_id in disconnected:
            self.disconnect(session_id)

# Global instance
ws_manager = WebSocketManager()
