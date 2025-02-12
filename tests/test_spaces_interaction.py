import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
import tweepy
from app.services.spaces_interaction import SpacesInteractionService
from app.models.space_event import SpaceEvent

@pytest.fixture
def mock_twitter_client():
    client = Mock(spec=tweepy.Client)
    client.get_space = Mock(return_value={"state": "live"})
    return client

@pytest.fixture
def interaction_service(mock_twitter_client):
    return SpacesInteractionService(mock_twitter_client)

@pytest.mark.asyncio
async def test_register_handler(interaction_service):
    # Test handler registration
    async def test_handler(event: SpaceEvent):
        pass
    
    interaction_service.register_handler("space_update", test_handler)
    assert len(interaction_service.event_handlers["space_update"]) == 1

@pytest.mark.asyncio
async def test_start_stop_monitoring(interaction_service):
    # Test starting monitoring
    space_id = "test_space_123"
    await interaction_service.start_monitoring(space_id)
    assert space_id in interaction_service.active_spaces
    
    # Test stopping monitoring
    await interaction_service.stop_monitoring(space_id)
    assert space_id not in interaction_service.active_spaces

@pytest.mark.asyncio
async def test_event_emission(interaction_service):
    # Create a mock handler
    handler_called = asyncio.Event()
    received_event = None
    
    async def test_handler(event: SpaceEvent):
        nonlocal received_event
        received_event = event
        handler_called.set()
    
    # Register handler
    interaction_service.register_handler("space_update", test_handler)
    
    # Start monitoring
    space_id = "test_space_123"
    await interaction_service.start_monitoring(space_id)
    
    # Wait for handler to be called
    try:
        await asyncio.wait_for(handler_called.wait(), timeout=2.0)
    except asyncio.TimeoutError:
        pytest.fail("Event handler was not called")
    
    # Verify event data
    assert received_event is not None
    assert received_event.type == "space_update"
    assert received_event.data["space_id"] == space_id
    
    # Clean up
    await interaction_service.stop_monitoring(space_id)
