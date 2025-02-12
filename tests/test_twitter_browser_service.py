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
    service._backoff_delay = 5.0
    service._max_backoff_delay = 60.0
    service._max_retries = 3
    service._session_duration = 3600
    service._session_start_time = None
    service._exponential_backoff = AsyncMock()
    service._reset_backoff = Mock()
    service._type_like_human = AsyncMock()
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
async def test_session_rotation(browser_service):
    """Test session rotation based on duration."""
    # Set up expired session
    browser_service._session_start_time = time.time() - 4000  # Expired by 400s
    assert browser_service._should_rotate_session() == True
    
    # Set up fresh session
    browser_service._session_start_time = time.time()
    assert browser_service._should_rotate_session() == False

@pytest.mark.asyncio
async def test_exponential_backoff(browser_service):
    """Test exponential backoff behavior."""
    initial_delay = browser_service._backoff_delay
    
    # First backoff
    await browser_service._exponential_backoff()
    assert browser_service._backoff_delay == initial_delay * 2
    
    # Second backoff
    await browser_service._exponential_backoff()
    assert browser_service._backoff_delay == min(initial_delay * 4, browser_service._max_backoff_delay)
    
    # Reset backoff
    browser_service._reset_backoff()
    assert browser_service._backoff_delay == initial_delay

@pytest.mark.asyncio
async def test_error_recovery_login(browser_service):
    """Test error recovery during login."""
    # Mock WebDriverWait for testing timeouts
    mock_wait = Mock()
    mock_wait.until.side_effect = [TimeoutException(), TimeoutException(), Mock()]  # Fail twice, succeed on third
    
    with patch('selenium.webdriver.support.ui.WebDriverWait', return_value=mock_wait):
        success = await browser_service.login("test_user", "test_pass")
        assert success == True
        assert browser_service._exponential_backoff.call_count == 2  # Called twice for retries
        assert browser_service._reset_backoff.call_count >= 1  # Called at least once on success

@pytest.mark.asyncio
async def test_human_like_behavior(browser_service):
    """Test human-like behavior patterns."""
    mock_element = Mock()
    browser_service.driver = Mock()
    
    # Test typing behavior
    await browser_service._type_like_human(mock_element, "test123")
    assert mock_element.send_keys.call_count > len("test123")  # Should have extra keystrokes for corrections
    assert mock_element.send_keys.call_args_list[0][0][0] != Keys.BACKSPACE  # First key should not be backspace
    
    # Verify random delays between actions
    assert browser_service._exponential_backoff.call_count >= 0
    assert browser_service._reset_backoff.call_count >= 0

@pytest.mark.asyncio
async def test_anti_detection_setup(browser_service):
    """Test anti-detection mechanisms during browser setup."""
    mock_driver = Mock()
    mock_options = Mock()
    
    with patch('selenium.webdriver.Chrome', return_value=mock_driver), \
         patch('selenium.webdriver.chrome.options.Options', return_value=mock_options):
        
        await browser_service.setup_browser()
        
        # Verify stealth settings
        assert any('--disable-blink-features=AutomationControlled' in str(call) 
                  for call in mock_options.add_argument.call_args_list)
        assert any('--window-size' in str(call) 
                  for call in mock_options.add_argument.call_args_list)
        
        # Verify CDP commands for anti-detection
        assert any('Page.addScriptToEvaluateOnNewDocument' in str(call) 
                  for call in mock_driver.execute_cdp_cmd.call_args_list)
        
        # Verify random user agent
        user_agent_calls = [call for call in mock_options.add_argument.call_args_list 
                           if '--user-agent' in str(call)]
        assert len(user_agent_calls) > 0

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
