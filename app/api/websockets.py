from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict
from app.models.space_event import SpaceEvent
from app.services.twitter_service import TwitterSpacesService, TwitterSpacesError

class SpaceEventManager:
    """Manager for Space event WebSocket connections."""
    
    def __init__(self):
        """Initialize the event manager."""
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, space_id: str, websocket: WebSocket):
        """Connect a new WebSocket client."""
        await websocket.accept()
        self.active_connections[space_id] = websocket
    
    def disconnect(self, space_id: str):
        """Disconnect a WebSocket client."""
        if space_id in self.active_connections:
            del self.active_connections[space_id]
    
    async def broadcast_event(self, space_id: str, event: SpaceEvent):
        """Broadcast an event to connected clients."""
        if space_id in self.active_connections:
            try:
                await self.active_connections[space_id].send_json(event.dict())
            except Exception as e:
                self.disconnect(space_id)

# Global event manager instance
event_manager = SpaceEventManager()

async def handle_space_events(space_id: str, websocket: WebSocket, character: str = "Host"):
    """Handle WebSocket connection for Space events."""
    try:
        # Initialize services
        twitter_service = TwitterSpacesService()
        
        # Connect WebSocket
        await event_manager.connect(space_id, websocket)
        
        # Create event handler
        async def event_handler(event: SpaceEvent):
            await event_manager.broadcast_event(space_id, event)
        
        # Start monitoring space
        interaction_service = twitter_service.interaction_services.get(character)
        if not interaction_service:
            raise TwitterSpacesError(f"No active space found for character: {character}")
            
        interaction_service.register_handler("space_update", event_handler)
        await interaction_service.start_monitoring(space_id)
        
        # Keep connection alive and handle client messages
        try:
            while True:
                data = await websocket.receive_text()
                # Handle client messages if needed
        except WebSocketDisconnect:
            event_manager.disconnect(space_id)
            await interaction_service.stop_monitoring(space_id)
            
    except Exception as e:
        await websocket.close(code=1000, reason=str(e))
        raise
