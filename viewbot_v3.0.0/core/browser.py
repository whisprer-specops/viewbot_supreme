import time
import logging
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

class BrowserManager:
    """
    Advanced browser management with anti-detection and stability features.
    """
    
    def __init__(self, headless=True, user_agent_manager=None, config=None):
        """
        Initialize the BrowserManager.
        
        Args:
            headless: Whether to run the browser in headless mode
            user_agent_manager: User agent manager instance
            config: Configuration dictionary
        """
        self.headless = headless
        self.user_agent_manager = user_agent_manager
        self.config = config or {}
        
    def setup_browser(self, proxy=None, use_tor=False, use_extension=False, extension_path=None, use_mobile=False):
        """
        Create and configure a Chrome browser instance with improved stability.
        
        Args:
            proxy: Proxy string to use (e.g., "http://1.2.3.4:8080")
            use_tor: Whether to route through Tor
            use_extension: Whether to load a Chrome extension
            extension_path: Path to Chrome extension
            use_mobile: Whether to use a mobile user agent
            
        Returns:
            WebDriver instance or None if setup failed
        """
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless=new")
        
        # Core performance options
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        
        # Anti-detection measures
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        # SSL error bypass (for problematic proxies)
        if not self.config.get("verify_ssl", True):
            chrome_options.add_argument("--ignore-certificate-errors")
            chrome_options.add_argument("--allow-insecure-localhost")
        
        # Set user agent
        if self.user_agent_manager:
            if use_mobile:
                user_agent = self.user_agent_manager.get_mobile()
            else:
                user_agent = self.user_agent_manager.get_desktop()
            chrome_options.add_argument(f"--user-agent={user_agent}")
        
        # Configure proxy
        if use_tor:
            chrome_options.add_argument("--proxy-server=socks5://127.0.0.1:9050")
        elif proxy:
            chrome_options.add_argument(f"--proxy-server={proxy}")
        
        # Try to create the browser directly without ChromeType
        for attempt in range(3):
            try:
                # Check for local chromedriver first
                local_drivers = ["./chromedriver.exe", "chromedriver.exe", "./chromedriver", "chromedriver"]
                
                driver_found = False
                for driver_path in local_drivers:
                    if os.path.exists(driver_path):
                        logging.info(f"Using local Chrome driver at: {driver_path}")
                        service = Service(executable_path=driver_path)
                        driver = webdriver.Chrome(service=service, options=chrome_options)
                        driver_found = True
                        break
                
                if not driver_found:
                    # Use default ChromeDriverManager
                    logging.info("Using ChromeDriverManager to get driver")
                    service = Service(ChromeDriverManager().install())
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                
                # Configure timeouts
                browser_timeout = self.config.get("browser_timeout", 90)
                driver.set_page_load_timeout(browser_timeout)
                driver.set_script_timeout(browser_timeout)
                
                # Test browser is working
                driver.get("about:blank")
                
                return driver
                
            except Exception as e:
                logging.error(f"Browser creation attempt {attempt+1} failed: {e}")
                if attempt == 2:  # Last attempt
                    logging.error(f"Failed to create browser after 3 attempts")
                    return None
                time.sleep(2)  # Wait before retry
                