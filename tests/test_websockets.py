import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket, WebSocketDisconnect
from unittest.mock import Mock, AsyncMock
import json
from app.main import app
from app.api.websockets import SpaceEventManager, event_manager
from app.models.space_event import SpaceEvent

@pytest.fixture
def websocket_client():
    return TestClient(app)

@pytest.fixture
def mock_websocket():
    websocket = Mock(spec=WebSocket)
    websocket.accept = AsyncMock()
    websocket.send_json = AsyncMock()
    websocket.receive_text = AsyncMock(return_value="")
    return websocket

@pytest.mark.asyncio
async def test_space_event_manager():
    manager = SpaceEventManager()
    mock_ws = Mock(spec=WebSocket)
    mock_ws.accept = AsyncMock()
    mock_ws.send_json = AsyncMock()
    
    # Test connection
    space_id = "test_space_123"
    await manager.connect(space_id, mock_ws)
    assert space_id in manager.active_connections
    
    # Test event broadcast
    event = SpaceEvent(
        type="space_update",
        data={"space_id": space_id, "state": "live"}
    )
    await manager.broadcast_event(space_id, event)
    mock_ws.send_json.assert_called_once_with(event.dict())
    
    # Test disconnection
    manager.disconnect(space_id)
    assert space_id not in manager.active_connections

@pytest.mark.asyncio
async def test_handle_space_events(mock_websocket, monkeypatch):
    from app.api.websockets import handle_space_events
    from app.services.twitter_service import TwitterSpacesService
    from app.services.spaces_interaction import SpacesInteractionService
    
    # Mock TwitterSpacesService
    mock_service = Mock(spec=TwitterSpacesService)
    mock_interaction = Mock(spec=SpacesInteractionService)
    mock_interaction.start_monitoring = AsyncMock()
    mock_interaction.stop_monitoring = AsyncMock()
    mock_interaction.register_handler = Mock()
    
    mock_service.interaction_services = {"Host": mock_interaction}
    
    def mock_init():
        return mock_service
    monkeypatch.setattr(TwitterSpacesService, "__new__", mock_init)
    
    # Test successful connection
    space_id = "test_space_123"
    mock_websocket.receive_text.side_effect = WebSocketDisconnect()
    
    await handle_space_events(space_id, mock_websocket)
    
    # Verify WebSocket was accepted and monitoring started
    mock_websocket.accept.assert_called_once()
    mock_interaction.start_monitoring.assert_called_once_with(space_id)
    mock_interaction.stop_monitoring.assert_called_once_with(space_id)
