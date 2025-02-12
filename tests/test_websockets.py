import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
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
async def test_handle_space_events(mock_websocket):
    from app.api.websockets import handle_space_events
    
    # Test successful connection
    space_id = "test_space_123"
    mock_websocket.receive_text.side_effect = ["message", Exception("WebSocket disconnected")]
    
    with pytest.raises(Exception, match="WebSocket disconnected"):
        await handle_space_events(space_id, mock_websocket)
    
    # Verify WebSocket was accepted
    mock_websocket.accept.assert_called_once()
