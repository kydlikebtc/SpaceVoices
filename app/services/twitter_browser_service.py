from typing import Optional, Dict
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from app.services.feature_flags import FeatureFlags

logger = logging.getLogger(__name__)

class TwitterBrowserService:
    """Service for browser-based Twitter Spaces interaction."""
    
    def __init__(self):
        """Initialize the browser service."""
        self.feature_flags = FeatureFlags()
        self.driver = None
        self.credentials: Dict[str, str] = {}
    
    async def setup_browser(self):
        """Set up the browser with proper configuration."""
        from selenium.webdriver.chrome.options import Options
        
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(10)
    
    async def login(self, username: str, password: str) -> bool:
        """
        Log into Twitter using browser automation.
        
        Args:
            username: Twitter username/email
            password: Twitter password
            
        Returns:
            bool: True if login successful
        """
        try:
            if not self.driver:
                await self.setup_browser()
            
            self.driver.get('https://twitter.com/login')
            
            # Wait for and fill username
            username_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "text"))
            )
            username_input.send_keys(username)
            
            # Click next
            next_button = self.driver.find_element(By.XPATH, "//span[text()='Next']")
            next_button.click()
            
            # Wait for and fill password
            password_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            password_input.send_keys(password)
            
            # Click login
            login_button = self.driver.find_element(By.XPATH, "//span[text()='Log in']")
            login_button.click()
            
            # Wait for home page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ARIA_LABEL, "Home"))
            )
            
            self.credentials = {
                'username': username,
                'password': password
            }
            
            return True
            
        except TimeoutException as e:
            logger.error(f"Timeout during login: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Failed to login: {str(e)}")
            return False
    
    async def create_space(self, title: str) -> Optional[str]:
        """
        Create a new Twitter Space using browser automation.
        
        Args:
            title: Title of the Space
            
        Returns:
            Optional[str]: Space ID if successful, None otherwise
        """
        try:
            if not self.driver:
                await self.setup_browser()
            
            # Click Spaces button
            spaces_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[@aria-label='Spaces']"))
            )
            spaces_button.click()
            
            # Click Create Space button
            create_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//span[text()='Create a Space']"))
            )
            create_button.click()
            
            # Set title
            title_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='What do you want to talk about?']"))
            )
            title_input.send_keys(title)
            
            # Start Space
            start_button = self.driver.find_element(By.XPATH, "//span[text()='Start your Space']")
            start_button.click()
            
            # Get Space ID from URL
            WebDriverWait(self.driver, 10).until(
                lambda driver: 'spaces' in driver.current_url
            )
            
            space_id = self.driver.current_url.split('/')[-1]
            return space_id
            
        except TimeoutException as e:
            logger.error(f"Timeout creating Space: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Failed to create Space: {str(e)}")
            return None
    
    async def end_space(self, space_id: str) -> bool:
        """
        End a Twitter Space using browser automation.
        
        Args:
            space_id: ID of the Space to end
            
        Returns:
            bool: True if successful
        """
        try:
            if not self.driver:
                await self.setup_browser()
            
            self.driver.get(f'https://twitter.com/i/spaces/{space_id}')
            
            # Click end Space button
            end_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//span[text()='End Space']"))
            )
            end_button.click()
            
            # Confirm end
            confirm_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//span[text()='Yes, end']"))
            )
            confirm_button.click()
            
            return True
            
        except TimeoutException as e:
            logger.error(f"Timeout ending Space: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Failed to end Space: {str(e)}")
            return False
    
    def cleanup(self):
        """Clean up browser resources."""
        if self.driver:
            self.driver.quit()
            self.driver = None
