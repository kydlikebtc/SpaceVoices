from typing import Optional, Dict
import logging
import time
import asyncio
import os
import psutil
import shutil
import random
import json
import tempfile
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from app.services.feature_flags import FeatureFlags

logger = logging.getLogger(__name__)

class TwitterBrowserService:
    """Service for browser-based Twitter Spaces interaction."""
    
    def __init__(self):
        """Initialize the browser service."""
        self.feature_flags = FeatureFlags()
        self.driver = None
        self.credentials: Dict[str, str] = {}
        self._temp_dir = None
        self._session_id = None
        self._debug_port = None
    
    async def _cleanup_chrome_processes(self):
        """Clean up any existing Chrome processes."""
        try:
            # Kill Chrome processes
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if any(x in proc.info['name'].lower() for x in ['chrome', 'chromium']):
                        proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Clean up temporary directories
            temp_dirs = ['/tmp/chrome*', '/dev/shm/chrome*']
            for pattern in temp_dirs:
                try:
                    for path in Path(os.path.dirname(pattern)).glob(os.path.basename(pattern)):
                        if path.is_dir():
                            shutil.rmtree(str(path), ignore_errors=True)
                        else:
                            path.unlink(missing_ok=True)
                except Exception as e:
                    logger.warning(f"Failed to clean up {pattern}: {e}")
            
            await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"Error cleaning up Chrome processes: {e}")

    async def _create_temp_directory(self):
        """Create a temporary directory for Chrome profile."""
        try:
            # Generate unique session directory
            timestamp = str(int(time.time()))
            pid = str(os.getpid())
            rand_suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=8))
            session_dir = f'chrome_session_{timestamp}_{pid}_{rand_suffix}'
            
            # Create temporary directory in /tmp
            self._temp_dir = tempfile.mkdtemp(prefix=session_dir)
            os.chmod(self._temp_dir, 0o700)
            
            # Create minimal directory structure
            default_dir = os.path.join(self._temp_dir, 'Default')
            os.makedirs(default_dir, mode=0o700)
            
            # Create preferences file
            prefs_file = os.path.join(default_dir, 'Preferences')
            with open(prefs_file, 'w') as f:
                json.dump({
                    'profile': {
                        'exit_type': 'Normal',
                        'exited_cleanly': True,
                        'default_content_setting_values': {
                            'notifications': 2,
                            'geolocation': 2
                        }
                    },
                    'session': {
                        'restore_on_startup': 4
                    },
                    'browser': {
                        'has_seen_welcome_page': True,
                        'check_default_browser': False
                    }
                }, f)
            
            # Create First Run file to skip first run experience
            with open(os.path.join(self._temp_dir, 'First Run'), 'w') as f:
                pass
                
            logger.info(f"Created profile directory: {self._temp_dir}")
            
        except Exception as e:
            logger.error(f"Failed to create directory: {e}")
            if hasattr(self, '_temp_dir') and os.path.exists(self._temp_dir):
                shutil.rmtree(self._temp_dir, ignore_errors=True)
            raise

    def _configure_chrome_options(self) -> Options:
        """Configure Chrome options with enhanced anti-detection."""
        options = Options()
        
        # Core settings
        options.add_argument('--no-sandbox')
        options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        
        # Random window size for more human-like appearance
        width = random.randint(1024, 1920)
        height = random.randint(768, 1080)
        options.add_argument(f'--window-size={width},{height}')
        
        # Profile and data directory
        options.add_argument(f'--user-data-dir={self._temp_dir}')
        
        # Performance and stability
        options.add_argument('--disable-background-networking')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-sync')
        options.add_argument('--disable-translate')
        
        # Enhanced anti-detection
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        options.add_argument('--disable-site-isolation-trials')
        
        # Random user agent
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0'
        ]
        options.add_argument(f'--user-agent={random.choice(user_agents)}')
        
        # Enhanced preferences
        prefs = {
            'profile': {
                'default_content_settings': {'notifications': 2},
                'exit_type': 'Normal',
                'exited_cleanly': True,
                'default_content_setting_values': {
                    'notifications': 2,
                    'geolocation': 2,
                    'media_stream': 2
                }
            },
            'credentials_enable_service': False,
            'profile.password_manager_enabled': False,
            'webrtc': {
                'ip_handling_policy': 'disable_non_proxied_udp',
                'multiple_routes_enabled': False,
                'nonproxied_udp_enabled': False
            }
        }
        options.add_experimental_option('prefs', prefs)
        
        # Additional automation detection prevention
        options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
        options.add_experimental_option('useAutomationExtension', False)
        
        return options

    async def setup_browser(self):
        """Set up the browser with proper configuration."""
        logger.info("Setting up browser...")
        
        # Generate unique session ID
        timestamp = str(int(time.time()))
        pid = os.getpid()
        rand_suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=8))
        self._session_id = f"{timestamp}_{pid}_{rand_suffix}"
        
        # Clean up any existing Chrome processes
        await self._cleanup_chrome_processes()
        
        # Create temporary directory
        await self._create_temp_directory()
        
        # Configure Chrome options
        options = self._configure_chrome_options()
        
        # Set up Chrome service with webdriver_manager
        service = Service(ChromeDriverManager().install())
        
        # Initialize driver with retry
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Initialize driver with explicit service
                self.driver = webdriver.Chrome(service=service, options=options)
                
                # Set page load timeout and implicit wait
                self.driver.set_page_load_timeout(30)
                self.driver.implicitly_wait(10)
                
                # Test browser is working
                self.driver.get('about:blank')
                await asyncio.sleep(1)
                
                # Execute CDP commands to prevent detection
                stealth_js = """
                    // Override webdriver and plugins
                    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                    Object.defineProperty(navigator, 'plugins', { 
                        get: () => [
                            { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                            { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                            { name: 'Native Client', filename: 'internal-nacl-plugin' }
                        ]
                    });
                    
                    // Override languages and platform
                    Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                    Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });
                    
                    // Override chrome runtime
                    window.chrome = {
                        app: { isInstalled: false },
                        runtime: {}
                    };
                    
                    // Add WebGL support
                    const getParameter = WebGLRenderingContext.prototype.getParameter;
                    WebGLRenderingContext.prototype.getParameter = function(parameter) {
                        const isMobile = navigator.userAgent.includes('Mobile');
                        
                        if (parameter === 37445) {
                            return 'Intel Inc.';
                        }
                        if (parameter === 37446) {
                            return isMobile ? 'Apple GPU' : 'Intel(R) Iris(TM) Graphics 6100';
                        }
                        
                        return getParameter.apply(this, arguments);
                    };
                """
                
                self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": stealth_js
                })
                
                # Success
                logger.info("Successfully initialized Chrome browser")
                return
                
            except Exception as e:
                last_error = e
                logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                
                # Cleanup on failure
                if hasattr(self, 'driver') and self.driver:
                    try:
                        self.driver.quit()
                    except:
                        pass
                    self.driver = None
                
                # Last attempt
                if attempt == max_retries - 1:
                    raise RuntimeError(f"Failed to initialize browser after {max_retries} attempts: {str(last_error)}")
                
                await asyncio.sleep(2)
        
        # Create unique temporary directory
        timestamp = str(int(time.time()))
        pid = os.getpid()
        rand_suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=8))
        self._session_id = f"{timestamp}_{pid}_{rand_suffix}"
        
        # Create fresh profile directory
        self._temp_dir = None
        data_dir = None
        
        # Create unique temporary directory
        timestamp = str(int(time.time()))
        pid = os.getpid()
        rand_suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=8))
        self._session_id = f"{timestamp}_{pid}_{rand_suffix}"
        
        # Create fresh profile directory
        self._temp_dir = os.path.join('/tmp', f'chrome_tmp_{self._session_id}')
        
        # Ensure clean state
        if os.path.exists(self._temp_dir):
            try:
                shutil.rmtree(self._temp_dir)
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Failed to remove directory: {e}")
                raise
        
        # Create minimal directory structure
        try:
            # Create base directory with strict permissions
            os.makedirs(self._temp_dir, mode=0o700)
            logger.info(f"Created profile directory: {self._temp_dir}")
            
            # Set Chrome data directory
            data_dir = self._temp_dir
            
        except Exception as e:
            logger.error(f"Failed to create directory: {e}")
            raise
            
        logger.info(f"Created Chrome directories in: {self._temp_dir}")
        
        logger.info(f"Created Chrome directories in: {self._temp_dir}")
        
        options = Options()
        # Minimal browser configuration
        options = Options()
        
        # Core settings
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        
        # Remote debugging
        debug_port = random.randint(9222, 9999)
        options.add_argument(f'--remote-debugging-port={debug_port}')
        
        # Profile settings
        options.add_argument(f'--user-data-dir={data_dir}')
        options.add_argument('--profile-directory=Default')
        
        # Basic preferences
        prefs = {
            'profile.default_content_settings.popups': 0,
            'profile.default_content_setting_values.notifications': 2,
            'profile.password_manager_enabled': False,
            'credentials_enable_service': False,
            'profile.exit_type': 'Normal',
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'safebrowsing.enabled': False,
            'translate.enabled': False
        }
        options.add_experimental_option('prefs', prefs)
        
        # Anti-detection
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Process isolation
        options.add_argument('--disable-background-networking')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-client-side-phishing-detection')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-sync')
        
        # Service configuration
        service = Service()
        
        # Initialize driver with retry
        max_retries = 3
        last_error = None
        
        # Initialize driver with retry
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Kill any existing Chrome processes
                os.system('pkill -f chrome')
                await asyncio.sleep(2)
                
                # Initialize driver with minimal options
                self.driver = webdriver.Chrome(options=options)
                self.driver.implicitly_wait(10)
                
                # Test browser is working
                self.driver.get('about:blank')
                await asyncio.sleep(1)
                
                # Execute CDP commands to prevent detection
                self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": """
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        });
                        Object.defineProperty(navigator, 'plugins', {
                            get: () => [1, 2, 3, 4, 5]
                        });
                        window.chrome = { runtime: {} };
                    """
                })
                
                # Success
                break
                
            except Exception as e:
                last_error = e
                logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                
                # Cleanup on failure
                if hasattr(self, 'driver') and self.driver:
                    try:
                        self.driver.quit()
                    except:
                        pass
                    self.driver = None
                
                # Last attempt
                if attempt == max_retries - 1:
                    raise last_error
                
                await asyncio.sleep(2)
        
        # Profile and data directory
        options.add_argument(f'--user-data-dir={data_dir}')
        options.add_argument('--profile-directory=Default')
        
        # Performance optimizations
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-accelerated-2d-canvas')
        options.add_argument('--disable-gpu-sandbox')
        options.add_argument('--disable-software-rasterizer')
        
        # Privacy and security
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        
        # Network and background
        options.add_argument('--disable-background-networking')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-breakpad')
        options.add_argument('--disable-component-update')
        options.add_argument('--disable-domain-reliability')
        options.add_argument('--disable-sync')
        
        # Experimental options
        options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Enhanced preferences
        prefs = {
            'profile': {
                'default_content_settings': {'notifications': 2},
                'password_manager_enabled': False,
                'exit_type': 'Normal'
            },
            'credentials_enable_service': False,
            'download': {
                'prompt_for_download': False,
                'directory_upgrade': True
            },
            'safebrowsing': {
                'enabled': False
            },
            'translate': {
                'enabled': False
            }
        }
        options.add_experimental_option('prefs', prefs)
        
        # Advanced anti-detection
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        
        # Random window size for more human-like appearance
        width = random.randint(1024, 1920)
        height = random.randint(768, 1080)
        options.add_argument(f'--window-size={width},{height}')
        
        # Randomized viewport size
        options.add_argument(f'--force-device-scale-factor={random.uniform(0.95, 1.05)}')
        
        # Enhanced privacy and fingerprint protection
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-site-isolation-trials')
        options.add_argument('--disable-features=IsolateOrigins')
        options.add_argument('--disable-notifications')
        
        # Additional experimental options
        options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option('detach', False)
        
        # Enhanced preferences
        prefs = {
            'profile.default_content_settings.popups': 0,
            'profile.default_content_setting_values.notifications': 2,
            'profile.default_content_setting_values.images': 1,
            'profile.default_content_setting_values.javascript': 1,
            'profile.default_content_setting_values.plugins': 1,
            'profile.default_content_setting_values.geolocation': 2,
            'profile.managed_default_content_settings.images': 1,
            'profile.managed_default_content_settings.javascript': 1,
            'credentials_enable_service': False,
            'profile.password_manager_enabled': False,
            'webrtc.ip_handling_policy': 'disable_non_proxied_udp',
            'webrtc.multiple_routes_enabled': False,
            'webrtc.nonproxied_udp_enabled': False
        }
        options.add_experimental_option('prefs', prefs)
        
        # Random viewport size to appear more human-like
        width = random.randint(1024, 1920)
        height = random.randint(768, 1080)
        options.add_argument(f'--window-size={width},{height}')
        
        # Randomized user agent
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0'
        ]
        options.add_argument(f'--user-agent={random.choice(user_agents)}')
        
        # Additional privacy settings
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--disable-extensions')
        options.add_argument('--remote-debugging-port=0')
        
        # Automation detection prevention
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option('detach', False)
        options.add_experimental_option("prefs", {
            "profile.default_content_settings.popups": 0,
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_setting_values.automatic_downloads": 1,
            "download.prompt_for_download": False,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        })
        
        # Privacy settings
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--disable-extensions')
        options.add_argument('--remote-debugging-port=0')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-save-password-bubble')
        options.add_argument('--disable-single-click-autofill')
        options.add_argument('--disable-autofill-keyboard-accessory-view')
        options.add_argument('--disable-translate')
        options.add_argument('--disable-default-apps')
        
        # Automation detection prevention
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option('detach', False)
        options.add_experimental_option("prefs", {
            "profile.default_content_settings.popups": 0,
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_setting_values.automatic_downloads": 1,
            "download.prompt_for_download": False
        })
        
        # Additional automation detection prevention
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option('detach', False)
        options.add_experimental_option("prefs", {
            "profile.default_content_settings.popups": 0,
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_setting_values.automatic_downloads": 1,
            "download.prompt_for_download": False,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        })
        
        try:
            # Use Selenium Manager for automatic driver management
            logger.info("Creating Chrome instance...")
            service = Service()
            
            # Initialize driver with retry
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    self.driver = webdriver.Chrome(
                        service=service,
                        options=options
                    )
                    self.driver.implicitly_wait(10)
                    
                    # Execute CDP commands to prevent detection
                    stealth_js = """
                        // Override webdriver
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        });
                        
                        // Override plugins
                        const getPlugins = () => {
                            const plugins = [
                                { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                                { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                                { name: 'Native Client', filename: 'internal-nacl-plugin' }
                            ];
                            const pluginArray = Object.create(PluginArray.prototype);
                            plugins.forEach((plugin, i) => {
                                const mimeTypes = Object.create(MimeTypeArray.prototype);
                                Object.defineProperty(pluginArray, i, {
                                    value: plugin,
                                    enumerable: true
                                });
                                Object.defineProperty(pluginArray, plugin.name, {
                                    value: plugin,
                                    enumerable: false
                                });
                            });
                            Object.defineProperty(pluginArray, 'length', {
                                value: plugins.length,
                                enumerable: false
                            });
                            return pluginArray;
                        };
                        Object.defineProperty(navigator, 'plugins', {
                            get: () => getPlugins()
                        });
                        
                        // Override languages
                        Object.defineProperty(navigator, 'languages', {
                            get: () => ['en-US', 'en']
                        });
                        
                        // Override platform
                        Object.defineProperty(navigator, 'platform', {
                            get: () => 'Win32'
                        });
                        
                        // Override chrome runtime
                        window.chrome = {
                            app: {
                                isInstalled: false,
                                InstallState: {
                                    DISABLED: 'disabled',
                                    INSTALLED: 'installed',
                                    NOT_INSTALLED: 'not_installed'
                                },
                                RunningState: {
                                    CANNOT_RUN: 'cannot_run',
                                    READY_TO_RUN: 'ready_to_run',
                                    RUNNING: 'running'
                                }
                            },
                            runtime: {
                                OnInstalledReason: {
                                    CHROME_UPDATE: 'chrome_update',
                                    INSTALL: 'install',
                                    SHARED_MODULE_UPDATE: 'shared_module_update',
                                    UPDATE: 'update'
                                },
                                OnRestartRequiredReason: {
                                    APP_UPDATE: 'app_update',
                                    OS_UPDATE: 'os_update',
                                    PERIODIC: 'periodic'
                                },
                                PlatformArch: {
                                    ARM: 'arm',
                                    ARM64: 'arm64',
                                    MIPS: 'mips',
                                    MIPS64: 'mips64',
                                    X86_32: 'x86-32',
                                    X86_64: 'x86-64'
                                },
                                PlatformNaclArch: {
                                    ARM: 'arm',
                                    MIPS: 'mips',
                                    MIPS64: 'mips64',
                                    X86_32: 'x86-32',
                                    X86_64: 'x86-64'
                                },
                                PlatformOs: {
                                    ANDROID: 'android',
                                    CROS: 'cros',
                                    LINUX: 'linux',
                                    MAC: 'mac',
                                    OPENBSD: 'openbsd',
                                    WIN: 'win'
                                },
                                RequestUpdateCheckStatus: {
                                    NO_UPDATE: 'no_update',
                                    THROTTLED: 'throttled',
                                    UPDATE_AVAILABLE: 'update_available'
                                }
                            }
                        };
                        
                        // Add WebGL support
                        const getParameter = WebGLRenderingContext.prototype.getParameter;
                        WebGLRenderingContext.prototype.getParameter = function(parameter) {
                            const isMobile = navigator.userAgent.includes('Mobile');
                            
                            if (parameter === 37445) {
                                return 'Intel Inc.';
                            }
                            if (parameter === 37446) {
                                return isMobile ? 'Apple GPU' : 'Intel(R) Iris(TM) Graphics 6100';
                            }
                            
                            return getParameter.apply(this, arguments);
                        };
                        
                        // Add touch support
                        const touchSupport = {
                            maxTouchPoints: 5,
                            touchEvent: function() { return true; },
                            touchStart: function() { return true; }
                        };
                        Object.defineProperty(navigator, 'maxTouchPoints', {
                            get: () => touchSupport.maxTouchPoints
                        });
                    """
                    
                    self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                        "source": stealth_js
                    })
                    
                    logger.info("Browser initialized successfully")
                    break
                except Exception as e:
                    logger.error(f"Attempt {attempt + 1} failed: {str(e)}")
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"Failed to initialize browser: {str(e)}")
            raise
    
    async def login(self, username: str, password: str) -> bool:
        """Log into Twitter using browser automation."""
        logger.info("Starting login process for user %s", username.split('@')[0])
        try:
            if not self.driver:
                await self.setup_browser()
            
            # Navigate to login page with retry
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    logger.info(f"Navigating to login page (attempt {attempt + 1})...")
                    self.driver.get('https://twitter.com/i/flow/login')
                    
                    # Wait for page load
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    await asyncio.sleep(2)
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Failed to load login page: {str(e)}")
                        return False
                    await asyncio.sleep(2)
            
            # Fill username with human-like timing
            try:
                logger.info("Looking for username input...")
                username_input = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[autocomplete='username'], input[name='text']"))
                )
                logger.info("Found username input, typing...")
                username_input.clear()
                for char in username:
                    username_input.send_keys(char)
                    await asyncio.sleep(random.uniform(0.1, 0.3))
                
                # Click next with JavaScript
                logger.info("Looking for next button...")
                next_button = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[text()='Next']"))
                )
                logger.info("Found next button, clicking...")
                
                # Move mouse to button with random offset
                button_size = next_button.size
                offset_x = random.randint(5, button_size['width'] - 5)
                offset_y = random.randint(5, button_size['height'] - 5)
                
                self.driver.execute_script(f"""
                    arguments[0].dispatchEvent(new MouseEvent('mouseover', {{
                        'view': window,
                        'bubbles': true,
                        'cancelable': true,
                        'clientX': arguments[1],
                        'clientY': arguments[2]
                    }}));
                """, next_button, offset_x, offset_y)
                await asyncio.sleep(random.uniform(0.2, 0.5))
                self.driver.execute_script("arguments[0].click();", next_button)
                await asyncio.sleep(2)
            except TimeoutException:
                logger.error("Timeout waiting for username input or next button")
                logger.error(f"Current URL: {self.driver.current_url}")
                logger.error(f"Page source: {self.driver.page_source[:1000]}")
                return False
            except Exception as e:
                logger.error(f"Error during username entry: {str(e)}")
                return False
            
            try:
                # Fill password with human-like timing
                logger.info("Looking for password input...")
                password_input = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='password']"))
                )
                logger.info("Found password input, typing...")
                password_input.clear()
                
                # Add random delays between keystrokes
                for char in password:
                    password_input.send_keys(char)
                    await asyncio.sleep(random.uniform(0.1, 0.4))
                
                # Random pause after password entry
                await asyncio.sleep(random.uniform(0.5, 1.0))
                
                # Click login with JavaScript and human-like behavior
                logger.info("Looking for login button...")
                login_button = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, "//span[text()='Log in']"))
                )
                logger.info("Found login button, preparing to click...")
                
                # Get button dimensions for realistic mouse movement
                button_size = login_button.size
                button_location = login_button.location
                
                # Calculate random click position within button
                click_x = button_location['x'] + random.randint(5, button_size['width'] - 5)
                click_y = button_location['y'] + random.randint(5, button_size['height'] - 5)
                
                # Simulate realistic mouse movement and click
                self.driver.execute_script(f"""
                    // Create mousemove event
                    const moveEvent = new MouseEvent('mousemove', {{
                        bubbles: true,
                        cancelable: true,
                        view: window,
                        clientX: {click_x},
                        clientY: {click_y}
                    }});
                    
                    // Create mouseover event
                    const overEvent = new MouseEvent('mouseover', {{
                        bubbles: true,
                        cancelable: true,
                        view: window,
                        clientX: {click_x},
                        clientY: {click_y}
                    }});
                    
                    // Dispatch events in sequence
                    arguments[0].dispatchEvent(moveEvent);
                    arguments[0].dispatchEvent(overEvent);
                """, login_button)
                
                # Random pause before click
                await asyncio.sleep(random.uniform(0.3, 0.7))
                
                # Click the button
                self.driver.execute_script("arguments[0].click();", login_button)
                
                # Random pause after click
                await asyncio.sleep(random.uniform(2.0, 4.0))
                
            except TimeoutException:
                logger.error("Timeout waiting for password input or login button")
                logger.error(f"Current URL: {self.driver.current_url}")
                return False
            except Exception as e:
                logger.error(f"Error during password entry and login: {str(e)}")
                return False
            
            try:
                # Wait for navigation and verify login with retry
                max_verify_attempts = 3
                for verify_attempt in range(max_verify_attempts):
                    logger.info(f"Verification attempt {verify_attempt + 1}/{max_verify_attempts}")
                    # Wait for URL change with increased timeout
                    logger.info("Waiting for navigation away from login page...")
                    try:
                        WebDriverWait(self.driver, 15).until(
                            lambda driver: 'flow/login' not in driver.current_url.lower()
                        )
                        
                        # Check for verification/error pages
                        current_url = self.driver.current_url.lower()
                        if any(x in current_url for x in ['challenge', 'verify', 'error']):
                            logger.error(f"Hit verification/error page: {current_url}")
                            if verify_attempt < max_verify_attempts - 1:
                                logger.info("Retrying verification...")
                                await asyncio.sleep(2)
                                continue
                            return False
                        
                        # Navigate to home to verify login
                        logger.info("Navigating to home page for verification...")
                        self.driver.get('https://twitter.com/home')
                        await asyncio.sleep(random.uniform(2.0, 4.0))
                        
                        # Enhanced success indicators with multiple checks
                        success_indicators = [
                            "[data-testid='primaryColumn']",
                            "[data-testid='SideNav_NewTweet_Button']",
                            "[data-testid='AppTabBar_Home_Link']",
                            "[aria-label='Home']",
                            "[aria-label='Timeline: Your Home Timeline']",
                            "[data-testid='AppTabBar_Profile_Link']",
                            "a[href='/home']",
                            "a[href='/explore']",
                            "div[data-testid='sidebarColumn']"
                        ]
                
                for selector in success_indicators:
                    try:
                        element = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        if element.is_displayed():
                            logger.info(f"Login successful - found element: {selector}")
                            self.credentials = {'username': username, 'password': password}
                            return True
                    except:
                        continue
                
                # If we get here, no success indicators were found
                logger.error("Could not verify login success")
                logger.error(f"Current URL: {self.driver.current_url}")
                return False
                
            except TimeoutException:
                logger.error("Timeout waiting for login completion")
                return False
            except Exception as e:
                logger.error(f"Error during login verification: {str(e)}")
                return False
            
            for selector in success_indicators:
                try:
                    element = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if element.is_displayed():
                        logger.info(f"Login successful - found element: {selector}")
                        self.credentials = {'username': username, 'password': password}
                        return True
                except:
                    continue
            
            # If we get here, no success indicators were found
            logger.error("Could not verify login success")
            logger.error(f"Current URL: {self.driver.current_url}")
            return False
            
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            if hasattr(self, 'driver') and self.driver:
                logger.error(f"Current URL: {self.driver.current_url}")
                logger.error(f"Current title: {self.driver.title}")
            return False
    
    async def _ensure_logged_in(self) -> bool:
        """Ensure we are logged in and on the home page."""
        try:
            # Check if we're already on home page and logged in
            if 'home' in self.driver.current_url.lower() and not 'login' in self.driver.current_url.lower():
                try:
                    # Quick check for logged-in state using multiple indicators
                    for selector in [
                        "[data-testid='AppTabBar_Home_Link']",
                        "[data-testid='SideNav_NewTweet_Button']",
                        "[data-testid='AppTabBar_Profile_Link']"
                    ]:
                        try:
                            WebDriverWait(self.driver, 5).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                            )
                            logger.info(f"Found login indicator: {selector}")
                            return True
                        except TimeoutException:
                            continue
                except Exception:
                    pass
            
            # Try navigating to home
            logger.info("Navigating to home page to verify login...")
            self.driver.get('https://x.com/home')
            await asyncio.sleep(5)  # Give more time for page load
            
            # Check current state
            logger.info(f"Current URL after navigation: {self.driver.current_url}")
            logger.info(f"Current title after navigation: {self.driver.title}")
            
            # Check for login indicators
            for selector in [
                "[data-testid='AppTabBar_Home_Link']",
                "[data-testid='SideNav_NewTweet_Button']",
                "[data-testid='AppTabBar_Profile_Link']"
            ]:
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"Found login indicator: {selector}")
                    return True
                except TimeoutException:
                    continue
            
            # If we get here, we're not logged in
            logger.error("Not logged in, attempting to re-login")
            if self.credentials:
                # Clear cookies and storage before re-login
                self.driver.delete_all_cookies()
                self.driver.execute_script("window.localStorage.clear();")
                self.driver.execute_script("window.sessionStorage.clear();")
                await asyncio.sleep(1)
                
                return await self.login(self.credentials['username'], self.credentials['password'])
            return False
                
        except Exception as e:
            logger.error(f"Error checking login state: {str(e)}")
            if hasattr(self, 'driver') and self.driver:
                logger.error(f"Current URL: {self.driver.current_url}")
                logger.error(f"Current title: {self.driver.title}")
            return False

    async def create_space(self, title: str) -> Optional[str]:
        """Create a new Twitter Space."""
        try:
            if not self.driver:
                await self.setup_browser()
            
            # Ensure we're logged in
            if not await self._ensure_logged_in():
                logger.error("Failed to ensure logged in state")
                return None
            
            # Navigate to home page first
            logger.info("Navigating to home page...")
            self.driver.get('https://x.com/home')
            await asyncio.sleep(3)
            
            # Log current state
            logger.info(f"Current URL: {self.driver.current_url}")
            logger.info(f"Current title: {self.driver.title}")
            
            # Click Spaces button
            logger.info("Looking for Spaces button...")
            try:
                spaces_button = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='AppTabBar_Audio_Link']"))
                )
                spaces_button.click()
                await asyncio.sleep(2)
            except TimeoutException:
                logger.error("Could not find Spaces button")
                logger.error(f"Page source preview: {self.driver.page_source[:1000]}")
                return None
            
            # Click Create Space button
            logger.info("Looking for Create Space button...")
            create_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='createSpaceButton']"))
            )
            create_button.click()
            await asyncio.sleep(2)
            
            # Set title
            logger.info("Looking for title input...")
            title_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='What do you want to talk about?']"))
            )
            title_input.clear()
            title_input.send_keys(title)
            await asyncio.sleep(1)
            
            # Start Space
            logger.info("Looking for Start Space button...")
            start_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Start your Space']"))
            )
            
            # Log pre-click state
            logger.info(f"Pre-click URL: {self.driver.current_url}")
            logger.info(f"Pre-click title: {self.driver.title}")
            
            start_button.click()
            await asyncio.sleep(3)
            
            # Log post-click state
            logger.info(f"Post-click URL: {self.driver.current_url}")
            logger.info(f"Post-click title: {self.driver.title}")
            
            # Get Space ID from URL
            try:
                WebDriverWait(self.driver, 20).until(
                    lambda driver: 'spaces' in driver.current_url.lower()
                )
                space_id = self.driver.current_url.split('/')[-1]
                logger.info(f"Successfully created Space with ID: {space_id}")
                return space_id
            except TimeoutException:
                logger.error("Could not verify Space creation")
                logger.error(f"Current URL: {self.driver.current_url}")
                logger.error(f"Current title: {self.driver.title}")
                logger.error(f"Page source preview: {self.driver.page_source[:1000]}")
                return None
            
        except Exception as e:
            logger.error(f"Failed to create Space: {str(e)}")
            if hasattr(self, 'driver') and self.driver:
                logger.error(f"Current URL: {self.driver.current_url}")
                logger.error(f"Current title: {self.driver.title}")
            return None
    
    async def end_space(self, space_id: str) -> bool:
        """End a Twitter Space."""
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
            
        except Exception as e:
            logger.error(f"Failed to end Space: {str(e)}")
            return False
    
    def cleanup(self):
        """Clean up browser resources."""
        if self.driver:
            try:
                # Get all window handles and close them
                try:
                    for handle in self.driver.window_handles:
                        self.driver.switch_to.window(handle)
                        self.driver.close()
                except:
                    pass
                
                # Quit the driver
                self.driver.quit()
            except Exception as e:
                logger.error(f"Error quitting driver: {str(e)}")
            finally:
                self.driver = None
        
        # Kill any remaining chrome processes for this session
        if hasattr(self, '_session_id'):
            try:
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        if 'chrome' in proc.info['name'].lower():
                            cmdline = ' '.join(proc.info['cmdline'] or [])
                            if self._session_id in cmdline:
                                proc.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            except Exception as e:
                logger.error(f"Error killing chrome processes: {str(e)}")
        
        # Clean up temporary directory
        if hasattr(self, '_temp_dir') and self._temp_dir:
            try:
                shutil.rmtree(self._temp_dir, ignore_errors=True)
                logger.info(f"Cleaned up temporary directory: {self._temp_dir}")
            except Exception as e:
                logger.error(f"Failed to clean up directory {self._temp_dir}: {str(e)}")
            self._temp_dir = None
            self._session_id = None
