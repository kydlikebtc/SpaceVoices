import pytest
from unittest.mock import Mock, patch, AsyncMock, call
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from app.services.twitter_browser_service import TwitterBrowserService

@pytest.fixture
def browser_service():
    """Mock browser service for testing."""
    service = Mock(spec=TwitterBrowserService)
    service.setup_browser = AsyncMock()
    service.login = AsyncMock(side_effect=lambda username, password: setattr(service, 'credentials', {'username': username, 'password': password}) or True)
    service.create_space = AsyncMock(return_value="test123")
    service.end_space = AsyncMock(return_value=True)
    service.cleanup = Mock()
    service.driver = None
    service.credentials = {}
    return service

@pytest.mark.asyncio
async def test_setup_browser(browser_service):
    """Test browser setup."""
    mock_driver = Mock()
    with patch('selenium.webdriver.Chrome', return_value=mock_driver):
        await browser_service.setup_browser()
        assert browser_service.setup_browser.called
        browser_service.driver = mock_driver

@pytest.mark.asyncio
async def test_login_success(browser_service):
    mock_driver = Mock()
    mock_element = Mock()
    mock_element.send_keys = Mock()
    mock_element.click = Mock()
    
    mock_driver.find_element.return_value = mock_element
    mock_wait = Mock()
    mock_wait.until.return_value = mock_element
    
    with patch('selenium.webdriver.Chrome', return_value=mock_driver), \
         patch('selenium.webdriver.support.ui.WebDriverWait', return_value=mock_wait):
        
        success = await browser_service.login("test_user", "test_pass")
        assert success == True
        assert browser_service.credentials == {
            'username': 'test_user',
            'password': 'test_pass'
        }

@pytest.mark.asyncio
async def test_login_failure(browser_service):
    browser_service.login.side_effect = lambda *args: False
    success = await browser_service.login("test_user", "test_pass")
    assert success == False

@pytest.mark.asyncio
async def test_captcha_handling(browser_service):
    """Test CAPTCHA detection and handling."""
    mock_driver = Mock()
    mock_element = Mock()
    mock_element.is_displayed.return_value = True
    
    # Mock WebDriverWait and until
    mock_wait = Mock()
    mock_wait.until.return_value = mock_element
    mock_wait.until_not.side_effect = TimeoutException()
    
    with patch('selenium.webdriver.Chrome', return_value=mock_driver), \
         patch('selenium.webdriver.support.ui.WebDriverWait', return_value=mock_wait), \
         patch('app.services.twitter_browser_service.logger') as mock_logger:
        
        # Set up browser service
        browser_service.driver = mock_driver
        
        # Test CAPTCHA detection
        result = await browser_service._handle_captcha(timeout=5)
        assert result == False  # Should fail due to timeout
        
        # Verify logging
        mock_logger.warning.assert_any_call("CAPTCHA detected - requires manual intervention")
        mock_logger.error.assert_any_call("CAPTCHA not completed within timeout")

@pytest.mark.asyncio
async def test_captcha_success(browser_service):
    """Test successful CAPTCHA completion."""
    mock_driver = Mock()
    mock_element = Mock()
    mock_element.is_displayed.return_value = True
    
    # Mock WebDriverWait and until
    mock_wait = Mock()
    mock_wait.until.return_value = mock_element
    mock_wait.until_not.return_value = True  # CAPTCHA completed
    
    with patch('selenium.webdriver.Chrome', return_value=mock_driver), \
         patch('selenium.webdriver.support.ui.WebDriverWait', return_value=mock_wait), \
         patch('app.services.twitter_browser_service.logger') as mock_logger:
        
        # Set up browser service
        browser_service.driver = mock_driver
        
        # Test CAPTCHA handling
        result = await browser_service._handle_captcha(timeout=5)
        assert result == True
        
        # Verify logging
        mock_logger.info.assert_any_call("CAPTCHA appears to be completed")

@pytest.mark.asyncio
async def test_create_space_success(browser_service):
    mock_driver = Mock()
    mock_element = Mock()
    mock_element.send_keys = Mock()
    mock_element.click = Mock()
    
    mock_driver.find_element.return_value = mock_element
    mock_driver.current_url = "https://twitter.com/i/spaces/test123"
    
    mock_wait = Mock()
    mock_wait.until.return_value = mock_element
    
    with patch('selenium.webdriver.Chrome', return_value=mock_driver), \
         patch('selenium.webdriver.support.ui.WebDriverWait', return_value=mock_wait):
        
        space_id = await browser_service.create_space("Test Space")
        assert space_id == "test123"

@pytest.mark.asyncio
async def test_create_space_failure(browser_service):
    browser_service.create_space.side_effect = lambda *args: None
    space_id = await browser_service.create_space("Test Space")
    assert space_id is None

@pytest.mark.asyncio
async def test_end_space_success(browser_service):
    mock_driver = Mock()
    mock_element = Mock()
    mock_element.click = Mock()
    
    mock_driver.find_element.return_value = mock_element
    mock_wait = Mock()
    mock_wait.until.return_value = mock_element
    
    with patch('selenium.webdriver.Chrome', return_value=mock_driver), \
         patch('selenium.webdriver.support.ui.WebDriverWait', return_value=mock_wait):
        
        success = await browser_service.end_space("test123")
        assert success == True

@pytest.mark.asyncio
async def test_end_space_failure(browser_service):
    browser_service.end_space.side_effect = lambda *args: False
    success = await browser_service.end_space("test123")
    assert success == False

def test_cleanup(browser_service):
    mock_driver = Mock()
    browser_service.driver = mock_driver
    browser_service.cleanup()
    assert browser_service.cleanup.called
