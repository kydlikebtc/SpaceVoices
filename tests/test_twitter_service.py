import pytest
from unittest.mock import Mock, AsyncMock
import tweepy
from app.services.twitter_service import TwitterSpacesService
from app.services.twitter_account_manager import TwitterAccountManager
from app.services.spaces_interaction import SpacesInteractionService

@pytest.fixture
def mock_account_manager():
    manager = Mock(spec=TwitterAccountManager)
    
    # Set up mock client for valid characters
    mock_client = Mock(spec=tweepy.Client)
    mock_space = Mock()
    mock_space.data = {"id": "test_space_123"}
    mock_client.create_space.return_value = mock_space
    
    def get_client(character):
        if character in ["Host", "Alice"]:
            return mock_client
        return None
    
    manager.get_client.side_effect = get_client
    return manager

@pytest.fixture
def spaces_service(monkeypatch, mock_account_manager):
    # Mock the TwitterAccountManager class to return our mock instance
    def mock_init(self):
        self.accounts = {}
    monkeypatch.setattr(TwitterAccountManager, "__init__", mock_init)
    monkeypatch.setattr(TwitterAccountManager, "get_client", mock_account_manager.get_client)
    
    # Create service with mocked dependencies
    service = TwitterSpacesService()
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
