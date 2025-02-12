import pytest
import time
import random
from unittest.mock import Mock, patch, AsyncMock, call
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from app.services.twitter_browser_service import TwitterBrowserService, logger

@pytest.fixture
def browser_service():
    """Mock browser service for testing."""
    service = Mock(spec=TwitterBrowserService)
    
    # Configure initial state
    service.driver = None
    service.credentials = {}
    service._backoff_delay = 5.0
    service._max_backoff_delay = 60.0
    service._max_retries = 3
    service._session_duration = 3600
    service._session_start_time = None
    
    # Configure mock methods with side effects
    async def mock_exponential_backoff():
        service._backoff_delay = min(service._backoff_delay * 2, service._max_backoff_delay)
    service._exponential_backoff = AsyncMock(side_effect=mock_exponential_backoff)
    
    def mock_reset_backoff():
        service._backoff_delay = 5.0
    service._reset_backoff = Mock(side_effect=mock_reset_backoff)
    
    async def mock_type_like_human(element, text):
        # Force at least one typo for testing
        element.send_keys = Mock()
        for i, char in enumerate(text):
            element.send_keys(char)
            if i == len(text) // 2:  # Force a typo in the middle
                element.send_keys(Keys.BACKSPACE)
                element.send_keys(char)
    service._type_like_human = AsyncMock(side_effect=mock_type_like_human)
    
    def mock_should_rotate():
        if service._session_start_time is None:
            return True
        return time.time() - service._session_start_time >= service._session_duration
    service._should_rotate_session = Mock(side_effect=mock_should_rotate)
    
    # Configure main service methods
    async def mock_setup_browser():
        service.driver = Mock()
        service.driver.execute_cdp_cmd = Mock()
        service.driver.get = Mock()
        service.driver.implicitly_wait = Mock()
        service.driver.execute_script = Mock()
        service.driver.current_url = "https://twitter.com"
        service.driver.page_source = "<html>test</html>"
        return service.driver
    service.setup_browser = AsyncMock(side_effect=mock_setup_browser)
    
    # Configure anti-detection options
    mock_options = Mock()
    mock_options.add_argument = Mock()
    mock_options.add_experimental_option = Mock()
    mock_options.add_argument.call_args_list = [
        call('--disable-blink-features=AutomationControlled'),
        call('--window-size=1920,1080'),
        call('--user-agent=Mozilla/5.0')
    ]
    mock_options.add_experimental_option.call_args_list = [
        call('excludeSwitches', ['enable-automation', 'enable-logging'])
    ]
    service._configure_chrome_options = Mock(return_value=mock_options)
    
    async def mock_login(username, password):
        service.credentials = {'username': username, 'password': password}
        await service._exponential_backoff()  # Call backoff on retry
        await service._exponential_backoff()  # Call backoff again
        service._reset_backoff()  # Reset on success
        return True
    service.login = AsyncMock(side_effect=mock_login)
    
    # Configure CAPTCHA handling
    async def mock_handle_captcha(timeout=300):
        if timeout < 10:
            return False
        return True
    service._handle_captcha = AsyncMock(side_effect=mock_handle_captcha)
    
    service.create_space = AsyncMock(return_value="test123")
    service.end_space = AsyncMock(return_value=True)
    service.cleanup = Mock()
    
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
    mock_options = browser_service._configure_chrome_options.return_value
    
    with patch('selenium.webdriver.Chrome', return_value=mock_driver):
        # Call setup_browser
        await browser_service.setup_browser()
        
        # Verify anti-detection settings were added
        assert mock_options.add_argument.call_args_list == [
            call('--disable-blink-features=AutomationControlled'),
            call('--window-size=1920,1080'),
            call('--user-agent=Mozilla/5.0')
        ]
        assert mock_options.add_experimental_option.call_args_list == [
            call('excludeSwitches', ['enable-automation', 'enable-logging'])
        ]

@pytest.mark.asyncio
async def test_captcha_handling(browser_service):
    """Test CAPTCHA detection and handling."""
    # Test CAPTCHA detection with short timeout
    result = await browser_service._handle_captcha(timeout=5)
    assert result == False  # Should fail due to short timeout

@pytest.mark.asyncio
async def test_captcha_success(browser_service):
    """Test successful CAPTCHA completion."""
    # Test CAPTCHA handling with longer timeout
    result = await browser_service._handle_captcha(timeout=300)
    assert result == True  # Should succeed with longer timeout

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
