import os
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.twitter_service import TwitterSpacesService, TwitterSpacesError
from app.services.twitter_browser_service import TwitterBrowserService

@pytest.fixture
def mock_browser_service():
    """Mock browser service for testing."""
    service = Mock(spec=TwitterBrowserService)
    service.login = AsyncMock()
    service.create_space = AsyncMock(return_value="test_space_123")
    service.end_space = AsyncMock(return_value=True)
    service.cleanup = Mock()
    return service

@pytest.fixture
def mock_browser_env(monkeypatch):
    """Set up mock environment variables for browser testing."""
    env_vars = {
        "TWITTER_BROWSER_1_CHARACTER": "Host",
        "TWITTER_BROWSER_1_USERNAME": "host_user",
        "TWITTER_BROWSER_1_PASSWORD": "host_pass",
        "USE_BROWSER_AUTOMATION": "true"
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars

@pytest.mark.asyncio
async def test_create_space_browser_automation(mock_browser_env, mock_browser_service):
    """Test creating a Space using browser automation."""
    with patch("app.services.twitter_browser_service.TwitterBrowserService") as mock_browser_class:
        mock_browser_class.return_value = mock_browser_service
        service = TwitterSpacesService()
        
        space_id = await service.create_space(
            "Test Space",
            character="Host"
        )
        
        assert space_id == "test_space_123"
        mock_browser_service.login.assert_called_once_with("host_user", "host_pass")
        mock_browser_service.create_space.assert_called_once_with("Test Space")

@pytest.mark.asyncio
async def test_end_space_browser_automation(mock_browser_env, mock_browser_service):
    """Test ending a Space using browser automation."""
    with patch("app.services.twitter_browser_service.TwitterBrowserService") as mock_browser_class:
        mock_browser_class.return_value = mock_browser_service
        service = TwitterSpacesService()
        
        success = await service.end_space("test_space_123", character="Host")
        
        assert success is True
        mock_browser_service.login.assert_called_once_with("host_user", "host_pass")
        mock_browser_service.end_space.assert_called_once_with("test_space_123")

@pytest.mark.asyncio
async def test_browser_automation_cleanup(mock_browser_env, mock_browser_service):
    """Test cleanup of browser automation resources."""
    with patch("app.services.twitter_browser_service.TwitterBrowserService") as mock_browser_class:
        mock_browser_class.return_value = mock_browser_service
        service = TwitterSpacesService()
        await service.cleanup()
        
        mock_browser_service.cleanup.assert_called_once()
        assert service.browser_service is None

@pytest.mark.asyncio
async def test_browser_automation_invalid_character(mock_browser_env, mock_browser_service):
    """Test browser automation with invalid character."""
    with patch("app.services.twitter_browser_service.TwitterBrowserService") as mock_browser_class:
        mock_browser_class.return_value = mock_browser_service
        service = TwitterSpacesService()
        
        with pytest.raises(TwitterSpacesError, match="No browser credentials for character: InvalidChar"):
            await service.create_space("Test Space", character="InvalidChar")
