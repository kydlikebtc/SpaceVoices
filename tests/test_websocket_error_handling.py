import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from app.api.websockets import SpaceEventManager

@pytest.fixture
def event_manager():
    return SpaceEventManager()

@pytest.fixture
def mock_websocket():
    websocket = Mock(spec=WebSocket)
    websocket.accept = AsyncMock()
    websocket.send_json = AsyncMock()
    websocket.receive_text = AsyncMock()
    return websocket

@pytest.mark.asyncio
async def test_connect_with_heartbeat(event_manager, mock_websocket):
    # Mock heartbeat to avoid infinite loop
    with patch.object(event_manager, '_start_heartbeat', AsyncMock()) as mock_heartbeat:
        await event_manager.connect("test_space", mock_websocket)
        
        # Verify connection setup
        mock_websocket.accept.assert_called_once()
        assert "test_space" in event_manager.active_connections
        mock_heartbeat.assert_called_once_with("test_space")

@pytest.mark.asyncio
async def test_connect_error_handling(event_manager, mock_websocket):
    # Mock accept to raise error
    mock_websocket.accept.side_effect = Exception("Connection error")
    
    with pytest.raises(Exception, match="Connection error"):
        await event_manager.connect("test_space", mock_websocket)
    
    # Verify cleanup on error
    assert "test_space" not in event_manager.active_connections

@pytest.mark.asyncio
async def test_heartbeat_mechanism(event_manager, mock_websocket):
    # Create a future to control heartbeat loop
    heartbeat_started = asyncio.Future()
    
    async def mock_heartbeat(space_id):
        heartbeat_started.set_result(True)
        await event_manager._start_heartbeat(space_id)
    
    with patch.object(event_manager, '_start_heartbeat', mock_heartbeat):
        # Start connection
        await event_manager.connect("test_space", mock_websocket)
        
        # Wait for heartbeat to start
        await asyncio.wait_for(heartbeat_started, timeout=1.0)
        
        # Verify ping was sent
        mock_websocket.send_json.assert_called_with({"type": "ping"})

@pytest.mark.asyncio
async def test_reconnection_attempts(event_manager, mock_websocket):
    space_id = "test_space"
    max_attempts = 2
    
    # Mock sleep to speed up test
    with patch('asyncio.sleep', AsyncMock()) as mock_sleep:
        await event_manager._attempt_reconnect(space_id, max_attempts)
        
        # Verify exponential backoff
        assert mock_sleep.call_count == max_attempts
        mock_sleep.assert_has_calls([
            AsyncMock()(1),  # First attempt: 2^0
            AsyncMock()(2),  # Second attempt: 2^1
        ])
