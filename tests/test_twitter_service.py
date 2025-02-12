import pytest
from unittest.mock import Mock, AsyncMock
import tweepy
from app.services.twitter_service import TwitterSpacesService
from app.services.twitter_account_manager import TwitterAccountManager
from app.services.spaces_interaction import SpacesInteractionService

@pytest.fixture
def mock_account_manager(monkeypatch):
    manager = Mock(spec=TwitterAccountManager)
    manager.get_client.return_value = Mock(spec=tweepy.Client)
    return manager

@pytest.fixture
def spaces_service(mock_account_manager):
    service = TwitterSpacesService()
    service.account_manager = mock_account_manager
    return service

@pytest.mark.asyncio
async def test_create_space_with_character(spaces_service, mock_account_manager):
    # Test creating a space with a specific character
    space_id = await spaces_service.create_space(
        title="Test Space",
        description="A test space",
        character="Alice"
    )
    
    assert space_id is not None
    assert "Alice" in spaces_service.interaction_services
    assert isinstance(spaces_service.interaction_services["Alice"], SpacesInteractionService)
    
    # Verify account manager was called
    mock_account_manager.get_client.assert_called_once_with("Alice")

@pytest.mark.asyncio
async def test_create_space_invalid_character(spaces_service, mock_account_manager):
    # Set up mock to return None for invalid character
    mock_account_manager.get_client.return_value = None
    
    # Test creating a space with invalid character
    with pytest.raises(ValueError, match="Invalid character"):
        await spaces_service.create_space(
            title="Test Space",
            description="A test space",
            character="InvalidCharacter"
        )
