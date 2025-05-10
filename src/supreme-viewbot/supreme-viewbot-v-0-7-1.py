#!/usr/bin/env python3
"""
Supreme ViewBot v0.7.1 - Medium Article Optimizer
A tool for boosting engagement metrics on Medium articles
"""

import os
import json
import queue
import random
import time
import threading
import asyncio
import aiohttp
import logging
import requests
import markovify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from stem import Signal
from stem.control import Controller
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Configuration
CONFIG = {
    "target_url": "https://medium.com/@cgpt/is-vibe-coding-cheating-or-the-future-of-programming-in-the-workplace-216fe9d5084d",
    "webhook_url": "https://discord.com/api/webhooks/1368210146949464214/QqgJoJOeI2qzfQjqlMCVWKgHpYqCZFGlVQ9EnugixWmwaP567xQw1w7l7DEm-pqOpP93",
    "captcha_api_key": os.getenv('2CAPTCHA_APIKEY', ''),
    "max_concurrent_threads": 7,
    "requests_per_thread": lambda: random.randint(30, 60),
    "delay_between_requests": lambda: random.uniform(20.0, 45.0),
    "use_tor": False,
    "use_freedium": True,
    "log_level": logging.INFO,
    "browser_timeout": 30,  # seconds
    "read_time_min": 60,    # seconds
    "read_time_max": 300,   # seconds
    "clap_probability": 0.7,
    "comment_probability": 0.3,
    "follow_probability": 0.4,
    "starting_articles": [
        "https://medium.com/the-narrative-arc/if-you-want-to-be-a-writer-maybe-read-this-first-okay-54a341d293e6"
    ]
}

# Setup logging
logging.basicConfig(
    level=CONFIG["log_level"],
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("viewbot.log"),
        logging.StreamHandler()
    ]
)

# Article Queue with deduplication
class ArticleQueue:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.visited = set()
        self.lock = threading.Lock()
        
    async def put(self, article_url, priority=1):
        with self.lock:
            if article_url not in self.visited:
                await self.queue.put((priority, article_url))
                self.visited.add(article_url)
                return True
        return False
        
    async def get(self):
        try:
            _, article_url = await self.queue.get()
            return article_url
        except asyncio.QueueEmpty:
            raise
            
    def task_done(self):
        self.queue.task_done()

# Account Management
class AccountManager:
    def __init__(self, account_file=None):
        self.accounts = []
        self.in_use = set()
        self.lock = threading.Lock()
        
        if account_file and os.path.exists(account_file):
            self.load_from_file(account_file)
            
    def load_from_file(self, filename):
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                for account in data:
                    self.add_account(account['username'], account['password'])
            logging.info(f"Loaded {len(self.accounts)} accounts from {filename}")
        except Exception as e:
            logging.error(f"Failed to load accounts from file: {e}")
            # Add a default account if loading fails
            self.add_account("geoffrey.le@proton.me", "pass1")
            
    def add_account(self, username, password):
        with self.lock:
            account = {
                'username': username, 
                'password': password, 
                'last_used': 0, 
                'failures': 0
            }
            self.accounts.append(account)
            
    def get_account(self):
        with self.lock:
            now = time.time()
            available = [a for a in self.accounts 
                         if a['username'] not in self.in_use 
                         and a['failures'] < 3 
                         and now - a['last_used'] > 3600]  # 1 hour cooldown
            
            if not available:
                return None
                
            # Sort by last_used (oldest first)
            available.sort(key=lambda a: a['last_used'])
            account = available[0]
            account['last_used'] = now
            self.in_use.add(account['username'])
            return account.copy()
            
    def release_account(self, username, success=True):
        with self.lock:
            if username in self.in_use:
                self.in_use.remove(username)
                
            for account in self.accounts:
                if account['username'] == username:
                    if not success:
                        account['failures'] += 1
                    else:
                        account['failures'] = 0
                    break

# Advanced Proxy Management
class ProxyPool:
    def __init__(self, proxy_file=None, max_failures=3):
        self.proxies = []
        self.max_failures = max_failures
        self.lock = threading.Lock()
        
        # Try to load from proxy file
        if proxy_file and os.path.exists(proxy_file):
            self.load_from_file(proxy_file)
            
        # If no proxies loaded, use default proxies
        if not self.proxies:
            default_proxies = [
                "http://8.130.34.237:5555", "http://8.130.36.245:80", 
                "http://8.130.37.235:9080", "http://8.130.39.117:8001",
                "http://8.146.200.53:8080", "http://8.148.24.225:9080"
            ]
            
            for proxy in default_proxies:
                self.add_proxy(proxy)
    
    def load_from_file(self, filename):
        try:
            with open(filename, 'r') as f:
                for line in f:
                    proxy = line.strip()
                    if proxy:
                        self.add_proxy(proxy)
            logging.info(f"Loaded {len(self.proxies)} proxies from {filename}")
        except Exception as e:
            logging.error(f"Failed to load proxies from file: {e}")
    
    def add_proxy(self, proxy_url):
        with self.lock:
            if not any(p["proxy"] == proxy_url for p in self.proxies):
                self.proxies.append({
                    "proxy": proxy_url, 
                    "weight": 1.0, 
                    "failures": 0,
                    "success_count": 0,
                    "last_used": 0
                })
    
    def get_proxy(self):
        with self.lock:
            now = time.time()
            # Filter by failures and add cooldown
            available = [p for p in self.proxies 
                        if p["failures"] < self.max_failures 
                        and now - p["last_used"] > 5]  # 5 second cooldown
            
            if not available:
                return None
                
            # Calculate weighted probabilities
            total_weight = sum(p["weight"] for p in available)
            if total_weight == 0:
                return None
                
            choice = random.uniform(0, total_weight)
            cumulative = 0
            
            selected_proxy = None
            for proxy in available:
                cumulative += proxy["weight"]
                if choice <= cumulative:
                    selected_proxy = proxy
                    break
                    
            if selected_proxy:
                selected_proxy["last_used"] = now
                return selected_proxy["proxy"]
                
            return available[-1]["proxy"] if available else None

    def report_failure(self, proxy_url):
        with self.lock:
            for proxy in self.proxies:
                if proxy["proxy"] == proxy_url:
                    proxy["failures"] += 1
                    proxy["weight"] *= 0.5  # Reduce weight on failure
                    if proxy["failures"] >= self.max_failures:
                        logging.info(f"Removing proxy {proxy_url} due to excessive failures")
                        self.proxies.remove(proxy)
                    break

    def report_success(self, proxy_url):
        with self.lock:
            for proxy in self.proxies:
                if proxy["proxy"] == proxy_url:
                    proxy["failures"] = 0
                    proxy["success_count"] += 1
                    proxy["weight"] = min(proxy["weight"] * 1.2, 2.0)  # Increase weight on success
                    break
                    
    def get_stats(self):
        with self.lock:
            active = len([p for p in self.proxies if p["failures"] < self.max_failures])
            total = len(self.proxies)
            success_rate = sum(p["success_count"] for p in self.proxies) / max(1, sum(p["success_count"] + p["failures"] for p in self.proxies))
            return {
                "active_proxies": active,
                "total_proxies": total,
                "success_rate": success_rate
            }

# User Agent Management
class UserAgentManager:
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.113 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
            "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.116 Mobile Safari/537.362",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:125.0) Gecko/20100101 Firefox/125.0",
            "Mozilla/5.0 (Linux; Android 14; Samsung Galaxy S24 Ultra) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.99 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; OnePlus 11 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.87 Mobile Safari/537.36"
        ]
        
    def get_random(self):
        return random.choice(self.user_agents)
        
    def get_desktop(self):
        desktop_agents = [ua for ua in self.user_agents if "Android" not in ua and "iPhone" not in ua and "iPad" not in ua]
        return random.choice(desktop_agents) if desktop_agents else self.get_random()
        
    def get_mobile(self):
        mobile_agents = [ua for ua in self.user_agents if "Android" in ua or "iPhone" in ua or "iPad" in ua]
        return random.choice(mobile_agents) if mobile_agents else self.get_random()

# Tor integration
class TorController:
    def __init__(self, port=9051, password=None):
        self.port = port
        self.password = password
        
    def renew_ip(self):
        try:
            with Controller.from_port(port=self.port) as controller:
                if self.password:
                    controller.authenticate(password=self.password)
                else:
                    controller.authenticate()
                controller.signal(Signal.NEWNYM)
                logging.info("Renewed Tor IP")
                return True
        except Exception as e:
            logging.error(f"Failed to renew Tor IP: {e}")
            return False

# Encryption for webhook notifications
class EncryptionManager:
    def __init__(self, password=None):
        self.password = password or "supreme_viewbot_v7"
        self.cipher = self._generate_cipher()
        
    def _generate_cipher(self):
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.password.encode()))
        return Fernet(key)
        
    def encrypt(self, message):
        return self.cipher.encrypt(message.encode()).decode()
        
    def decrypt(self, encrypted_message):
        return self.cipher.decrypt(encrypted_message.encode()).decode()

# Webhook notifications
class WebhookManager:
    def __init__(self, webhook_url, encryption_manager=None):
        self.webhook_url = webhook_url
        self.encryption_manager = encryption_manager
        
    def send_notification(self, message, encrypt=True):
        try:
            if encrypt and self.encryption_manager:
                encrypted_message = self.encryption_manager.encrypt(message)
                payload = {"content": f"Encrypted: {encrypted_message}"}
            else:
                payload = {"content": message}
                
            headers = {"Content-Type": "application/json"}
            response = requests.post(self.webhook_url, json=payload, headers=headers)
            
            if response.status_code == 204:
                logging.info("Webhook sent successfully")
                return True
            else:
                logging.error(f"Failed to send webhook: {response.status_code}")
                return False
        except Exception as e:
            logging.error(f"Error sending webhook: {e}")
            return False

# CAPTCHA solving
class CaptchaSolver:
    def __init__(self, api_key):
        self.api_key = api_key
        
    def solve_recaptcha(self, site_key, page_url, timeout=300):
        if not self.api_key:
            logging.error("No 2CAPTCHA API key provided")
            return None
            
        payload = {
            'key': self.api_key,
            'method': 'userrecaptcha',
            'googlekey': site_key,
            'pageurl': page_url,
            'json': 1
        }
        try:
            # Submit CAPTCHA
            response = requests.post('http://2captcha.com/in.php', data=payload)
            response_data = response.json()
            
            if response_data.get('status') != 1:
                logging.error(f"CAPTCHA submission failed: {response_data.get('error_text')}")
                return None
                
            captcha_id = response_data.get('request')
            logging.info(f"CAPTCHA submitted, ID: {captcha_id}")
            
            # Wait for solution
            result_payload = {'key': self.api_key, 'action': 'get', 'id': captcha_id, 'json': 1}
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                time.sleep(5)
                result = requests.get('http://2captcha.com/res.php', params=result_payload)
                result_data = result.json()
                
                if result_data.get('status') == 1:
                    captcha_solution = result_data.get('request')
                    logging.info("CAPTCHA solved successfully")
                    return captcha_solution
                    
                logging.debug(f"Waiting for CAPTCHA solution... ({int(time.time() - start_time)}s)")
                
            logging.error(f"CAPTCHA solving timed out after {timeout}s")
            return None
        except Exception as e:
            logging.error(f"CAPTCHA solving error: {e}")
            return None
    
    def apply_solution(self, driver, solution):
        try:
            driver.execute_script(f'document.getElementById("g-recaptcha-response").innerHTML="{solution}";')
            driver.execute_script("___grecaptcha_cfg.clients[0].Y.Y.callback('" + solution + "')")
            return True
        except Exception as e:
            logging.error(f"Error applying CAPTCHA solution: {e}")
            return False

# Temporary email service
class TempEmailService:
    def __init__(self, api_base="https://api.temp-mail.org"):
        self.api_base = api_base
        self.email = None
        self.email_id = None
        
    def get_email(self):
        try:
            response = requests.get(f"{self.api_base}/request/email/format/json")
            if response.status_code == 200:
                data = response.json()
                self.email = data.get('email')
                self.email_id = data.get('email_id')
                logging.info(f"Got temp email: {self.email}")
                return self.email
            else:
                logging.error(f"Failed to get temp email: {response.status_code}")
                return None
        except Exception as e:
            logging.error(f"Error getting temp email: {e}")
            return None
            
    def check_inbox(self, timeout=180, interval=5):
        """Check inbox for Medium sign-in emails and return sign-in link if found."""
        if not self.email_id:
            logging.error("No email ID available")
            return None
            
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.api_base}/request/mail/id/{self.email_id}/format/json")
                if response.status_code == 200:
                    emails = response.json()
                    for email_data in emails:
                        if "Medium" in email_data.get('subject', ''):
                            soup = BeautifulSoup(email_data.get('body', ''), 'html.parser')
                            links = soup.find_all('a')
                            for link in links:
                                href = link.get('href', '')
                                if "signin" in href:
                                    logging.info(f"Found Medium sign-in link")
                                    return href
            except Exception as e:
                logging.error(f"Error checking inbox: {e}")
                
            time.sleep(interval)
            
        logging.error(f"No sign-in email found after {timeout}s")
        return None

# Browser and Selenium utilities
class BrowserManager:
    def __init__(self, headless=True, user_agent_manager=None):
        self.headless = headless
        self.user_agent_manager = user_agent_manager or UserAgentManager()
        
    def setup_browser(self, proxy=None, use_tor=False, use_extension=False, extension_path=None, use_mobile=False):
        """Create and configure a Chrome browser instance."""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument("--headless=new")
        
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920x1080")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        
        # Anti-detection measures
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        
        # Set user agent
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
            
        try:
            driver = webdriver.Chrome(options=chrome_options)
            
            # Set page load timeout
            driver.set_page_load_timeout(CONFIG["browser_timeout"])
            
            # Apply additional stealth measures
            self._apply_stealth_js(driver)
            
            return driver
        except Exception as e:
            logging.error(f"Error creating browser: {e}")
            return None
            
    def _apply_stealth_js(self, driver):
        """Apply JavaScript-based stealth techniques."""
        try:
            # Mask WebDriver presence
            driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false,
                });
            """)
            
            # Add fake plugins
            driver.execute_script("""
                const makePluginInfo = (name, filename, desc, suffixes, type) => ({
                    name, filename, description: desc, suffixes, type
                });
                
                const pluginArray = [
                    makePluginInfo('Chrome PDF Plugin', 'internal-pdf-viewer', 'Portable Document Format', 'pdf', 'application/x-google-chrome-pdf'),
                    makePluginInfo('Chrome PDF Viewer', 'mhjfbmdgcfjbbpaeojofohoefgiehjai', '', 'pdf', 'application/pdf'),
                    makePluginInfo('Native Client', 'internal-nacl-plugin', '', '', 'application/x-nacl')
                ];
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => Object.setPrototypeOf({
                        length: pluginArray.length,
                        ...Object.fromEntries(pluginArray.map((p, i) => [i, p])),
                        ...Object.fromEntries(pluginArray.map(p => [p.name, p])),
                    }, PluginArray.prototype),
                });
            """)
            
            # Add hardware concurrency
            driver.execute_script("""
                Object.defineProperty(navigator, 'hardwareConcurrency', {
                    get: () => Math.floor(Math.random() * 8) + 4, // Return between 4 and 12
                });
            """)
            
            # Add canvas fingerprint poisoning
            driver.execute_script("""
                const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
                CanvasRenderingContext2D.prototype.getImageData = function(x, y, w, h) {
                    const imageData = originalGetImageData.call(this, x, y, w, h);
                    const data = imageData.data;
                    // Slightly alter a few random pixels
                    for (let i = 0; i < 10; i++) {
                        const offset = Math.floor(Math.random() * data.length);
                        data[offset] = data[offset] ^ 1;
                    }
                    return imageData;
                };
            """)
        except Exception as e:
            logging.error(f"Error applying stealth JS: {e}")

# Medium-specific interaction utilities
class MediumInteractor:
    def __init__(self, browser_manager, captcha_solver=None, temp_email_service=None):
        self.browser_manager = browser_manager
        self.captcha_solver = captcha_solver
        self.temp_email_service = temp_email_service
        
    def get_freedium_url(self, medium_url):
        """Convert Medium URL to Freedium URL to bypass paywall."""
        # Make sure URL is properly formatted
        if not medium_url.startswith("http"):
            medium_url = f"https://{medium_url}"
        return f"https://freedium.cfd/{medium_url}"
        
    def _detect_and_solve_captcha(self, driver, url):
        """Detect and solve CAPTCHA if present."""
        if not self.captcha_solver:
            return False
            
        try:
            # Check for reCAPTCHA presence
            captcha_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'g-recaptcha'))
            )

# Here's a complete implementation showing how the Freedium functionality 
# is integrated in the main ViewBot class

async def interact_with_article(self, article_url, proxy=None, account=None):
    """Full article interaction flow."""
    driver = None
    success = False
    
    try:
        # Set up browser
        use_mobile = random.random() < 0.3  # 30% chance of mobile browser
        driver = self.browser_manager.setup_browser(
            proxy=proxy, 
            use_tor=self.use_tor,
            use_mobile=use_mobile
        )
        
        if not driver:
            logging.error("Failed to create browser")
            return False
            
        # Try Freedium first if enabled
        if self.use_freedium:
            freedium_url = self.medium_interactor.get_freedium_url(article_url)
            logging.info(f"Attempting to access article via Freedium: {freedium_url}")
            
            try:
                driver.get(freedium_url)
                
                # Wait for page to load
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Check if Freedium worked
                if "Access denied" not in driver.page_source and len(driver.find_elements(By.TAG_NAME, "p")) > 5:
                    logging.info("Successfully accessed article via Freedium")
                    
                    # Check for CAPTCHA
                    if not self.medium_interactor._detect_and_solve_captcha(driver, freedium_url):
                        # If CAPTCHA detected but not solved, we may need to try alternative methods
                        if "g-recaptcha" in driver.page_source:
                            logging.warning("CAPTCHA detected in Freedium but not solved, will try alternative access")
                            raise Exception("CAPTCHA not solved in Freedium")
                else:
                    logging.warning("Freedium access appears limited, will try alternative methods")
                    raise Exception("Limited content through Freedium")
                    
            except Exception as e:
                logging.warning(f"Freedium access failed: {e}")
                
                # If Freedium fails, try direct access with login
                logging.info(f"Falling back to direct access: {article_url}")
                driver.get(article_url)
                
                # Check for paywall
                if "paywall" in driver.page_source.lower() or "member-only" in driver.page_source.lower() or "limited access" in driver.page_source.lower():
                    logging.info("Paywall detected, trying authentication")
                    
                    # Try using account if available
                    if account:
                        logging.info(f"Attempting login with account: {account['username']}")
                        if not self.medium_interactor.login_with_credentials(driver, account['username'], account['password']):
                            # If account login fails, try email login
                            logging.info("Account login failed, trying email login")
                            if not await self.medium_interactor.login_with_email(driver, article_url):
                                logging.error("Could not bypass paywall")
                                return False
                    else:
                        # Try email login
                        logging.info("No account available, trying email login")
                        if not await self.medium_interactor.login_with_email(driver, article_url):
                            logging.error("Could not bypass paywall")
                            return False
                            
                    # Navigate back to article after login
                    driver.get(article_url)
                    time.sleep(3)
        else:
            # Direct access without Freedium
            logging.info(f"Accessing article directly: {article_url}")
            driver.get(article_url)
            
            # Handle paywall if encountered
            if "paywall" in driver.page_source.lower() or "member-only" in driver.page_source.lower():
                logging.info("Paywall detected without Freedium enabled")
                
                # Try authentication methods
                auth_success = False
                if account:
                    auth_success = self.medium_interactor.login_with_credentials(driver, account['username'], account['password'])
                
                if not auth_success:
                    auth_success = await self.medium_interactor.login_with_email(driver, article_url)
                    
                if not auth_success:
                    logging.error("Could not bypass paywall")
                    return False
                    
                # Navigate back to article after login
                driver.get(article_url)
                time.sleep(3)
        
        # Extract article stats before interaction
        before_stats = self.medium_interactor.extract_medium_stats(driver)
        
        # Simulate reading
        self.medium_interactor.simulate_human_reading(driver)
        
        # 70% chance to clap
        if random.random() < CONFIG["clap_probability"]:
            if self.medium_interactor.clap_for_article(driver):
                self.stats["claps"] += 1
        
        # 30% chance to comment
        if random.random() < CONFIG["comment_probability"]:
            if self.medium_interactor.post_comment(driver):
                self.stats["comments"] += 1
                
        # 40% chance to follow author
        if random.random() < CONFIG["follow_probability"]:
            if self.medium_interactor.follow_author(driver):
                self.stats["follows"] += 1
                
        # Find next article
        next_article = self.medium_interactor.find_next_article(driver)
        if next_article:
            await self.article_queue.put(next_article)
            
        # Extract article stats after interaction
        after_stats = self.medium_interactor.extract_medium_stats(driver)
        
        # Send webhook notification if configured
        if self.webhook_manager:
            # Prepare stats comparison
            before_after = {
                "title": after_stats.get("title", "Unknown Article"),
                "url": article_url,
                "before": before_stats,
                "after": after_stats,
                "actions": {
                    "read": True,
                    "clapped": self.stats["claps"] > 0,
                    "commented": self.stats["comments"] > 0,
                    "followed": self.stats["follows"] > 0
                }
            }
            
            # Send notification
            self.webhook_manager.send_notification(
                f"Interacted with article: {before_after['title']}. " +
                f"Actions: read={before_after['actions']['read']}, " +
                f"clapped={before_after['actions']['clapped']}, " +
                f"commented={before_after['actions']['commented']}, " +
                f"followed={before_after['actions']['followed']}"
            )
            
        # Report success
        self.stats["views"] += 1
        success = True
        return True
        
    except Exception as e:
        logging.error(f"Error interacting with article: {e}")
        self.stats["failures"] += 1
        return False
    finally:
        # Clean up
        if driver:
            try:
                driver.quit()
            except:
                pass
                
        # Release account if used
        if account:
            self.account_manager.release_account(account['username'], success)
            
        # Report proxy success/failure
        if proxy and not self.use_tor:
            if success:
                self.proxy_pool.report_success(proxy)
            else:
                self.proxy_pool.report_failure(proxy)       

     