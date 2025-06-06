import time
import logging
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
        
        # Enhanced stability options
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-background-networking")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-breakpad")
        chrome_options.add_argument("--disable-component-extensions-with-background-pages")
        chrome_options.add_argument("--disable-features=TranslateUI,BlinkGenPropertyTrees")
        chrome_options.add_argument("--disable-ipc-flooding-protection")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--enable-features=NetworkServiceInProcess2")
        chrome_options.add_argument("--force-color-profile=srgb")
        chrome_options.add_argument("--metrics-recording-only")
        chrome_options.add_argument("--mute-audio")
        
        # Memory options
        chrome_options.add_argument("--js-flags=--expose-gc")
        chrome_options.add_argument("--disable-site-isolation-trials")
        
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
            
        # Add extension if needed
        if use_extension and extension_path and os.path.exists(extension_path):
            chrome_options.add_extension(extension_path)
            
        # Custom Chrome capabilities with timeouts
        capabilities = webdriver.ChromeOptions().to_capabilities()
        capabilities['pageLoadStrategy'] = 'eager'  # Interactive instead of complete
        
        # Try up to 3 times to create browser
        browser_timeout = self.config.get("browser_timeout", 90)
        for attempt in range(3):
            try:
                # Use webdriver-manager to automatically download and manage ChromeDriver
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
                
                # Configure timeouts
                driver.set_page_load_timeout(browser_timeout)
                driver.set_script_timeout(browser_timeout)
                
                # Apply stealth measures
                self._apply_enhanced_stealth_js(driver)
                
                # Test browser is working
                driver.get("about:blank")
                
                return driver
            except Exception as e:
                logging.error(f"Browser creation attempt {attempt+1} failed: {e}")
                if attempt == 2:  # Last attempt
                    logging.error(f"Failed to create browser after 3 attempts")
                    return None
                time.sleep(2)  # Wait before retry
                
    def _apply_enhanced_stealth_js(self, driver):
        """Apply advanced JavaScript-based stealth techniques."""
        try:
            # Mask WebDriver presence
            driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Hide automation
                window.navigator.chrome = {
                    runtime: {}
                };
                
                // Spoof plugins
                const makePluginInfo = (name, filename, desc, suffixes, type) => ({
                    name, filename, description: desc, suffixes, type
                });
                
                const plugins = [
                    makePluginInfo('Chrome PDF Plugin', 'internal-pdf-viewer', 'Portable Document Format', 'pdf', 'application/x-google-chrome-pdf'),
                    makePluginInfo('Chrome PDF Viewer', 'mhjfbmdgcfjbbpaeojofohoefgiehjai', '', 'pdf', 'application/pdf'),
                    makePluginInfo('Native Client', 'internal-nacl-plugin', '', '', 'application/x-nacl')
                ];
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => Object.setPrototypeOf({
                        length: plugins.length,
                        ...Object.fromEntries(plugins.map((p, i) => [i, p])),
                        ...Object.fromEntries(plugins.map(p => [p.name, p])),
                        namedItem: name => plugins.find(p => p.name === name),
                        item: index => plugins[index],
                    }, PluginArray.prototype),
                });
                
                // Spoof mimeTypes
                Object.defineProperty(navigator, 'mimeTypes', {
                    get: () => Object.setPrototypeOf({
                        length: 2,
                        0: { type: 'application/pdf', suffixes: 'pdf', description: '', enabledPlugin: navigator.plugins[0] },
                        1: { type: 'application/x-google-chrome-pdf', suffixes: 'pdf', description: '', enabledPlugin: navigator.plugins[1] },
                    }, MimeTypeArray.prototype),
                });
                
                // Random hardware concurrency (4-8 cores)
                Object.defineProperty(navigator, 'hardwareConcurrency', {
                    get: () => Math.floor(Math.random() * 4) + 4
                });
                
                // Random device memory (4-8GB)
                Object.defineProperty(navigator, 'deviceMemory', {
                    get: () => Math.floor(Math.random() * 4) + 4
                });
                
                // Spoof languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en', 'es'],
                });
                
                // Canvas fingerprint poisoning (minimal noise to avoid detection)
                const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
                CanvasRenderingContext2D.prototype.getImageData = function(x, y, w, h) {
                    const imageData = originalGetImageData.call(this, x, y, w, h);
                    const data = imageData.data;
                    
                    // Alter only a few random pixels (less than 0.1%)
                    const numPixels = Math.floor(data.length / 400);  // 0.25% of pixels
                    for (let i = 0; i < numPixels; i++) {
                        const offset = Math.floor(Math.random() * data.length);
                        // Subtle 1-bit modification
                        data[offset] = data[offset] ^ 1;
                    }
                    return imageData;
                };
                
                // Spoof screen size with small variations
                const realWidth = window.screen.width;
                const realHeight = window.screen.height;
                const variationW = Math.floor(Math.random() * 10);
                const variationH = Math.floor(Math.random() * 10);
                
                Object.defineProperty(screen, 'width', { get: () => realWidth - variationW });
                Object.defineProperty(screen, 'height', { get: () => realHeight - variationH });
                Object.defineProperty(screen, 'availWidth', { get: () => realWidth - variationW });
                Object.defineProperty(screen, 'availHeight', { get: () => realHeight - variationH });
                
                // Spoof modern browser features
                Object.defineProperty(navigator, 'userActivation', {
                    get: () => ({
                        hasBeenActive: true,
                        isActive: true
                    })
                });
            """)
        except Exception as e:
            logging.error(f"Error applying enhanced stealth JS: {e}")