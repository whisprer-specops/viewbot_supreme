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
    "max_concurrent_threads": 3,
    "requests_per_thread": lambda: random.randint(30, 60),
    "delay_between_requests": lambda: random.uniform(200.0, 450.0),
    "use_tor": False,
    "use_freedium": True,
    "log_level": logging.INFO,
    "browser_timeout": 30,  # seconds
    "read_time_min": 150,    # seconds
    "read_time_max": 900,   # seconds
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
        
        # Load default proxies
        default_proxies = [
            "http://8.130.34.237:5555", "http://8.130.36.245:80", 
            "http://8.130.37.235:9080", "http://8.130.39.117:8001",
            "http://8.146.200.53:8080", "http://8.148.24.225:9080",
            "http://8.212.165.164:1000", "http://8.213.129.15:50001",
            "http://8.213.222.157:3128", "http://8.219.97.248:80",
            "http://9.223.187.19:3128", "http://34.102.48.89:8080",
            "http://37.140.51.159:80", "http://38.49.129.205:999",
            "http://38.65.172.81:999", "http://39.100.88.89:9080"
        ]
        
        for proxy in default_proxies:
            self.add_proxy(proxy)
            
        if proxy_file and os.path.exists(proxy_file):
            self.load_from_file(proxy_file)
    
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
            
            # Extract site key
            site_key = driver.execute_script(
                "return document.querySelector('.g-recaptcha').dataset.sitekey;"
            )
            
            if not site_key:
                logging.error("CAPTCHA detected but couldn't extract site key")
                return False
                
            # Solve CAPTCHA
            solution = self.captcha_solver.solve_recaptcha(site_key, url)
            if not solution:
                return False
                
            # Apply solution
            return self.captcha_solver.apply_solution(driver, solution)
            
        except TimeoutException:
            # No CAPTCHA found
            return True
        except Exception as e:
            logging.error(f"Error in CAPTCHA handling: {e}")
            return False
    
    async def login_with_email(self, driver, medium_url):
        """Login to Medium using temporary email."""
        if not self.temp_email_service:
            return False
            
        email = self.temp_email_service.get_email()
        if not email:
            return False
            
        try:
            # Navigate to Medium
            driver.get(medium_url)
            
            # Find and click sign in button
            try:
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//a[contains(text(), "Sign in")]'))
                ).click()
            except:
                logging.warning("Could not find Sign in button, looking for alternative")
                # Try alternative sign-in buttons
                alternatives = [
                    '//button[contains(text(), "Sign in")]',
                    '//a[contains(@href, "signin")]',
                    '//a[contains(@class, "signin")]'
                ]
                for xpath in alternatives:
                    try:
                        element = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, xpath))
                        )
                        element.click()
                        break
                    except:
                        continue
            
            # Enter email
            try:
                email_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, 'email'))
                )
                email_input.send_keys(email)
                
                # Find and click continue button
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Continue")]'))
                ).click()
                
                # Wait for sign-in email
                logging.info("Waiting for sign-in email...")
                signin_url = await asyncio.to_thread(
                    self.temp_email_service.check_inbox, 
                    timeout=180,  # 3 minutes to wait for email
                    interval=5    # Check every 5 seconds
                )
                
                if signin_url:
                    driver.get(signin_url)
                    # Wait for login to complete
                    time.sleep(5)
                    logging.info("Successfully logged in via email link")
                    return True
                else:
                    logging.error("No sign-in email received")
                    return False
            except Exception as e:
                logging.error(f"Error during email login flow: {e}")
                return False
                
        except Exception as e:
            logging.error(f"Email login failed: {e}")
            return False
            
    def login_with_credentials(self, driver, username, password):
        """Login to Medium using stored credentials."""
        try:
            # Navigate to sign-in page
            driver.get('https://medium.com/m/signin')
            
            # Enter email
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'email'))
            ).send_keys(username)
            
            # Click next
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Next") or contains(text(), "Continue")]'))
            ).click()
            
            # If redirected to password page
            try:
                password_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, 'password'))
                )
                password_field.send_keys(password)
                
                # Click sign in
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Sign in")]'))
                ).click()
                
                # Wait for login to complete
                time.sleep(5)
                
                # Check for successful login
                if "Sign in" in driver.title or "/signin" in driver.current_url:
                    logging.error("Login unsuccessful - still on login page")
                    return False
                    
                logging.info(f"Successfully logged in as {username}")
                return True
                
            except TimeoutException:
                # May already be logged in or email-only login
                logging.warning("Could not find password field, checking login status")
                
                # Check if we're already logged in
                if "Sign in" not in driver.title and "/signin" not in driver.current_url:
                    logging.info(f"Login seems successful for {username}")
                    return True
                    
                return False
                
        except Exception as e:
            logging.error(f"Login with credentials failed: {e}")
            return False
    
    def simulate_human_reading(self, driver, article_length=None):
        """Simulate realistic human reading patterns."""
        try:
            # Get scroll height
            scroll_height = driver.execute_script("return document.body.scrollHeight")
            
            if not article_length:
                # Estimate article length by text content
                article_text = driver.find_element(By.TAG_NAME, "body").text
                article_length = len(article_text)
            
            # Calculate read time based on article length (approx 200-300 WPM)
            words = article_length // 5  # Approx 5 chars per word
            base_read_time = words / random.uniform(200, 300)  # Random WPM between 200-300
            
            # Add some randomness (±20%)
            read_time = base_read_time * random.uniform(0.8, 1.2)
            
            # Cap read time between config min and max
            read_time = max(CONFIG["read_time_min"], min(CONFIG["read_time_max"], read_time))
            
            # Divide scroll height into random segments
            segments = random.randint(5, 15)
            segment_height = scroll_height / segments
            
            logging.info(f"Reading article for ~{read_time:.1f}s with {segments} scroll segments")
            
            # Initial pause to simulate page load review
            time.sleep(random.uniform(1, 3))
            
            # Scroll through article with random pauses
            for i in range(segments):
                # Scroll to next segment with some randomness
                target_scroll = int((i + 1) * segment_height * random.uniform(0.9, 1.1))
                driver.execute_script(f"window.scrollTo(0, {min(target_scroll, scroll_height)});")
                
                # Pause for reading with some randomness
                segment_time = read_time / segments * random.uniform(0.7, 1.3)
                time.sleep(segment_time)
                
                # 10% chance to scroll back up a bit (like re-reading)
                if random.random() < 0.1:
                    scroll_back = max(0, target_scroll - segment_height * random.uniform(0.3, 0.7))
                    driver.execute_script(f"window.scrollTo(0, {scroll_back});")
                    time.sleep(random.uniform(1, 3))
                    
                    # Then continue where we left off
                    driver.execute_script(f"window.scrollTo(0, {target_scroll});")
                    time.sleep(random.uniform(1, 2))
                    
                # 5% chance to pause a little longer (like being distracted)
                if random.random() < 0.05:
                    time.sleep(random.uniform(3, 8))
                    
            # 70% chance to scroll back up randomly at the end
            if random.random() < 0.7:
                random_position = random.uniform(0, scroll_height * 0.8)
                driver.execute_script(f"window.scrollTo(0, {random_position});")
                time.sleep(random.uniform(1, 3))
            
            return True
        except Exception as e:
            logging.error(f"Error during reading simulation: {e}")
            return False
            
    def clap_for_article(self, driver, min_claps=1, max_claps=50):
        """Clap for an article with a random number of claps."""
        try:
            # Find the clap button
            clap_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//button[contains(@aria-label, "clap") or contains(@class, "clap")]'))
            )
            
            # Random number of claps
            num_claps = random.randint(min_claps, max_claps)
            logging.info(f"Clapping {num_claps} times")
            
            # Click the button multiple times
            for _ in range(num_claps):
                clap_button.click()
                time.sleep(random.uniform(0.05, 0.2))  # Random delay between claps
                
            return True
        except Exception as e:
            logging.error(f"Error while clapping: {e}")
            return False
            
    def generate_comment(self, article_text):
        """Generate a Markov chain-based comment from article text."""
        try:
            # Clean up article text
            clean_text = ' '.join(article_text.split())
            
            # Create Markov model
            text_model = markovify.Text(clean_text, state_size=2)
            
            # Try to generate a sensible comment
            for _ in range(10):  # Try up to 10 times
                comment = text_model.make_short_sentence(
                    max_chars=280, 
                    min_chars=50,
                    tries=100
                )
                if comment and len(comment) >= 50:
                    break
                    
            # Fallback comments if generation fails
            fallback_comments = [
                "Great article! Really enjoyed the insights.",
                "Thanks for sharing these thoughts, very enlightening!",
                "This was an interesting read. Looking forward to more.",
                "I appreciate the perspective shared here.",
                "This resonates with my own experiences. Well written!",
                "Thoughtful analysis. I'll be reflecting on these points.",
                "You've articulated something I've been thinking about too."
            ]
            
            if not comment:
                comment = random.choice(fallback_comments)
                
            return comment
        except Exception as e:
            logging.error(f"Error generating comment: {e}")
            return random.choice([
                "Interesting perspective!",
                "Great read!",
                "Thanks for sharing this!"
            ])
            
    def post_comment(self, driver, comment=None):
        """Post a comment on the article."""
        try:
            if not comment:
                # Get article text
                article_text = driver.find_element(By.TAG_NAME, "body").text
                comment = self.generate_comment(article_text)
                
            # Look for comment box
            comment_selectors = [
                '//textarea[contains(@placeholder, "comment") or contains(@placeholder, "response")]',
                '//div[contains(@aria-label, "comment") or contains(@aria-label, "response")]',
                '//textarea',  # Fallback to any textarea
            ]
            
            comment_box = None
            for selector in comment_selectors:
                try:
                    comment_box = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    break
                except:
                    continue
                    
            if not comment_box:
                logging.error("Could not find comment box")
                return False
                
            # Click on comment box
            comment_box.click()
            time.sleep(random.uniform(0.5, 1.5))
            
            # Type comment with human-like timing
            for char in comment:
                comment_box.send_keys(char)
                time.sleep(random.uniform(0.01, 0.10))  # Random typing delay
                
            time.sleep(random.uniform(0.5, 2))  # Pause before publishing
            
            # Try to find publish button
            publish_selectors = [
                '//button[contains(text(), "Publish") or contains(text(), "Comment") or contains(text(), "Respond")]',
                '//button[@type="submit"]',
                '//button[contains(@class, "publish") or contains(@class, "submit")]'
            ]
            
            for selector in publish_selectors:
                try:
                    publish_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    publish_button.click()
                    logging.info(f"Posted comment: {comment[:50]}...")
                    time.sleep(random.uniform(1, 3))  # Wait for submission
                    return True
                except:
                    continue
                    
            # Fallback: try Enter key
            comment_box.send_keys(Keys.CONTROL, Keys.ENTER)
            logging.info(f"Posted comment using Ctrl+Enter: {comment[:50]}...")
            time.sleep(random.uniform(1, 3))
            
            return True
        except Exception as e:
            logging.error(f"Error posting comment: {e}")
            return False
            
    def follow_author(self, driver):
        """Find and click the follow button to follow the author."""
        try:
            follow_selectors = [
                '//button[contains(text(), "Follow")]',
                '//a[contains(text(), "Follow")]',
                '//button[contains(@aria-label, "Follow")]'
            ]
            
            for selector in follow_selectors:
                try:
                    follow_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    follow_button.click()
                    logging.info("Followed author")
                    time.sleep(random.uniform(1, 3))
                    return True
                except:
                    continue
                    
            logging.warning("Could not find follow button")
            return False
        except Exception as e:
            logging.error(f"Error following author: {e}")
            return False
            
    def find_next_article(self, driver):
        """Find and return URL of a next or related article."""
        try:
            # Try to find "Next" or "Part" links first
            next_selectors = [
                '//a[contains(text(), "Next")]',
                '//a[contains(text(), "Part")]',
                '//a[contains(@class, "next")]'
            ]
            
            for selector in next_selectors:
                try:
                    next_link = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    next_url = next_link.get_attribute('href')
                    if next_url and "medium.com" in next_url:
                        logging.info(f"Found next article: {next_url}")
                        return next_url
                except:
                    continue
                    
            # If no next article, try to find related/recommended articles
            related_selectors = [
                '//h2[contains(text(), "More from")]/following::a',
                '//h3[contains(text(), "Recommended")]/following::a',
                '//div[contains(@class, "recommended")]/descendant::a',
                '//article//a[contains(@href, "medium.com")]'
            ]
            
            for selector in related_selectors:
                try:
                    related_links = driver.find_elements(By.XPATH, selector)
                    if related_links:
                        # Get random related article
                        related_link = random.choice(related_links)
                        related_url = related_link.get_attribute('href')
                        if related_url and "medium.com" in related_url:
                            logging.info(f"Found related article: {related_url}")
                            return related_url
                except:
                    continue
                    
            logging.warning("Could not find next or related article")
            return None
        except Exception as e:
            logging.error(f"Error finding next article: {e}")
            return None
            
    def extract_medium_stats(self, driver):
        """Extract and return article metadata and stats."""
        try:
            stats = {
                "title": None,
                "author": None,
                "publish_date": None,
                "read_time": None,
                "clap_count": None,
                "comment_count": None
            }
            
            # Extract title
            try:
                stats["title"] = driver.find_element(By.TAG_NAME, "h1").text
            except:
                pass
                
            # Extract author
            try:
                stats["author"] = driver.find_element(By.XPATH, '//a[contains(@href, "/@")]').text
            except:
                pass
                
            # Extract publish date
            try:
                date_element = driver.find_element(By.XPATH, '//time')
                stats["publish_date"] = date_element.get_attribute("datetime") or date_element.text
            except:
                pass
                
            # Extract read time
            try:
                read_time_text = driver.find_element(By.XPATH, '//*[contains(text(), "min read")]').text
                stats["read_time"] = read_time_text
            except:
                pass
                
            # Extract clap count
            try:
                clap_text = driver.find_element(By.XPATH, '//*[contains(@aria-label, "clap") or contains(@class, "clap")]//following-sibling::*').text
                stats["clap_count"] = clap_text
            except:
                pass
                
            # Extract comment count
            try:
                comment_text = driver.find_element(By.XPATH, '//*[contains(text(), "response") or contains(text(), "comment")]').text
                stats["comment_count"] = comment_text
            except:
                pass
                
            return {k: v for k, v in stats.items() if v}  # Only return non-None values
        except Exception as e:
            logging.error(f"Error extracting article stats: {e}")
            return {}

# Main interaction class
class ViewBot:
    def __init__(self, config):
        self.config = config
        self.target_url = config["target_url"]
        self.use_tor = config["use_tor"]
        self.use_freedium = config["use_freedium"]
        
        # Initialize managers
        self.user_agent_manager = UserAgentManager()
        self.browser_manager = BrowserManager(headless=True, user_agent_manager=self.user_agent_manager)
        self.proxy_pool = ProxyPool()
        self.account_manager = AccountManager()
        
        # Initialize services if API keys available
        self.captcha_solver = CaptchaSolver(config["captcha_api_key"]) if config["captcha_api_key"] else None
        self.temp_email_service = TempEmailService()
        self.tor_controller = TorController() if self.use_tor else None
        
        # Initialize managers for notifications
        self.encryption_manager = EncryptionManager()
        self.webhook_manager = WebhookManager(config["webhook_url"], self.encryption_manager) if config["webhook_url"] else None
        
        # Create Medium interactor
        self.medium_interactor = MediumInteractor(
            self.browser_manager,
            self.captcha_solver,
            self.temp_email_service
        )
        
        # Create article queue
        self.article_queue = ArticleQueue()
        
        # Load starting articles
        for article in config["starting_articles"]:
            asyncio.run(self.article_queue.put(article))
        
        # Stats tracking
        self.stats = {
            "views": 0,
            "claps": 0,
            "comments": 0,
            "follows": 0,
            "failures": 0,
            "start_time": time.time()
        }
        
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
                
            # Determine URL to use
            url = self.medium_interactor.get_freedium_url(article_url) if self.use_freedium else article_url
            
            # Load the page
            logging.info(f"Loading article: {url}")
            driver.get(url)
            
            # Check for CAPTCHA
            if not self.medium_interactor._detect_and_solve_captcha(driver, url):
                logging.warning("CAPTCHA detected but not solved")
                
            # Check for paywall
            if "paywall" in driver.page_source.lower() or "member-only" in driver.page_source.lower():
                logging.info("Paywall detected, trying alternative access")
                
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
                driver.get(url)
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
    
    async def simple_view_request(self, url, proxy=None):
        """Send a simple async HTTP request to register a view."""
        headers = {
            "User-Agent": self.user_agent_manager.get_random(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0"
        }
        
        # Add cookies for medium.com
        cookies = {
            "sid": f"1:{random.randint(1000000000, 9999999999)}",
            "_ga": f"GA1.2.{random.randint(1000000000, 9999999999)}.{int(time.time()-random.randint(1000000, 9999999))}",
            "_gid": f"GA1.2.{random.randint(1000000000, 9999999999)}.{int(time.time())}",
            "xsrf": base64.b64encode(os.urandom(16)).decode('utf-8'),
            "_med": "refer",
            "_parsely_visitor": f"{{{random.randint(1000000000, 9999999999)}}}",
            "sz": f"{random.randint(1, 100)}",
        }
        
        # Add referrers - 30% chance of having a referrer
        if random.random() < 0.3:
            referrers = [
                "https://www.google.com/",
                "https://www.reddit.com/",
                "https://twitter.com/",
                "https://www.linkedin.com/",
                "https://www.facebook.com/",
                "https://medium.com/",
                "https://news.ycombinator.com/"
            ]
            headers["Referer"] = random.choice(referrers)
        
        try:
            proxy_url = None
            if self.use_tor:
                proxy_url = "http://127.0.0.1:9050"
            elif proxy:
                proxy_url = proxy
                
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(cookies=cookies, timeout=timeout) as session:
                # First request just for the main URL
                async with session.get(url, headers=headers, proxy=proxy_url, allow_redirects=True) as response:
                    if response.status == 200:
                        self.stats["views"] += 1
                        logging.info(f"View request successful: {response.status}")
                        
                        # 20% chance to make additional requests for assets
                        if random.random() < 0.2:
                            # Parse HTML to find assets
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            
                            # Find a few asset URLs to request
                            asset_urls = []
                            
                            # Look for scripts
                            for script in soup.find_all('script', src=True):
                                asset_urls.append(script['src'])
                                
                            # Look for stylesheets
                            for link in soup.find_all('link', rel='stylesheet', href=True):
                                asset_urls.append(link['href'])
                                
                            # Look for images
                            for img in soup.find_all('img', src=True):
                                asset_urls.append(img['src'])
                                
                            # Request a few random assets (max 5)
                            for asset_url in random.sample(asset_urls, min(5, len(asset_urls))):
                                # Make sure URL is absolute
                                if not asset_url.startswith('http'):
                                    if asset_url.startswith('//'):
                                        asset_url = 'https:' + asset_url
                                    elif asset_url.startswith('/'):
                                        asset_url = 'https://medium.com' + asset_url
                                        
                                try:
                                    async with session.get(asset_url, headers=headers, proxy=proxy_url) as asset_response:
                                        logging.debug(f"Asset request: {asset_url} - Status: {asset_response.status}")
                                except Exception as e:
                                    logging.debug(f"Asset request failed: {e}")
                        
                        # Report success
                        if proxy and not self.use_tor:
                            self.proxy_pool.report_success(proxy)
                        return True
                    else:
                        logging.warning(f"View request failed: {response.status}")
                        if proxy and not self.use_tor:
                            self.proxy_pool.report_failure(proxy)
                        return False
        except Exception as e:
            logging.error(f"Error sending view request: {e}")
            if proxy and not self.use_tor:
                self.proxy_pool.report_failure(proxy)
            self.stats["failures"] += 1
            return False
            
    def get_run_stats(self):
        """Get current statistics about the bot run."""
        now = time.time()
        runtime = now - self.stats["start_time"]
        
        # Calculate rates
        views_per_hour = (self.stats["views"] / runtime) * 3600 if runtime > 0 else 0
        claps_per_hour = (self.stats["claps"] / runtime) * 3600 if runtime > 0 else 0
        comments_per_hour = (self.stats["comments"] / runtime) * 3600 if runtime > 0 else 0
        
        # Format time
        hours, remainder = divmod(runtime, 3600)
        minutes, seconds = divmod(remainder, 60)
        runtime_formatted = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
        
        # Get proxy stats
        proxy_stats = self.proxy_pool.get_stats()
        
        return {
            "runtime": runtime_formatted,
            "runtime_seconds": runtime,
            "views": self.stats["views"],
            "claps": self.stats["claps"],
            "comments": self.stats["comments"],
            "follows": self.stats["follows"],
            "failures": self.stats["failures"],
            "views_per_hour": round(views_per_hour, 2),
            "claps_per_hour": round(claps_per_hour, 2),
            "comments_per_hour": round(comments_per_hour, 2),
            "success_rate": round((self.stats["views"] / max(self.stats["views"] + self.stats["failures"], 1)) * 100, 2),
            "active_proxies": proxy_stats["active_proxies"],
            "total_proxies": proxy_stats["total_proxies"],
            "proxy_success_rate": round(proxy_stats["success_rate"] * 100, 2)
        }
            
    async def view_worker(self):
        """Worker task to send view requests."""
        while True:
            try:
                # Get a proxy
                proxy = None
                if not self.use_tor:
                    proxy = self.proxy_pool.get_proxy()
                    if not proxy:
                        logging.warning("No working proxies available for view worker, waiting...")
                        await asyncio.sleep(30)
                        continue
                elif self.use_tor:
                    # Renew Tor IP occasionally (every 5-10 requests)
                    if random.randint(1, 10) <= 2:  # 20% chance
                        self.tor_controller.renew_ip()
                        await asyncio.sleep(1)  # Allow time for IP to change
                
                # Send the view request
                await self.simple_view_request(self.target_url, proxy)
                
                # Random delay between requests
                delay = CONFIG["delay_between_requests"]() if callable(CONFIG["delay_between_requests"]) else CONFIG["delay_between_requests"]
                await asyncio.sleep(delay)
                
            except Exception as e:
                logging.error(f"View worker error: {e}")
                await asyncio.sleep(5)
                
    async def interaction_worker(self):
        """Worker task for full browser interactions."""
        while True:
            try:
                # Get an article URL
                try:
                    article_url = await self.article_queue.get()
                except asyncio.QueueEmpty:
                    # If queue is empty, use target URL
                    article_url = self.target_url
                
                # Get a proxy
                proxy = None
                if not self.use_tor:
                    proxy = self.proxy_pool.get_proxy()
                    if not proxy:
                        logging.warning("No working proxies available for interaction worker, waiting...")
                        await asyncio.sleep(30)
                        continue
                elif self.use_tor:
                    # Always renew Tor IP before browser interaction
                    self.tor_controller.renew_ip()
                    await asyncio.sleep(1)  # Allow time for IP to change
                
                # Get an account (50% chance)
                account = None
                if random.random() < 0.5:
                    account = self.account_manager.get_account()
                
                # Perform the interaction
                await self.interact_with_article(article_url, proxy, account)
                
                # Mark task as done if it came from queue
                if article_url != self.target_url:
                    self.article_queue.task_done()
                
                # Random delay between interactions (longer than view delays)
                delay = CONFIG["delay_between_requests"]() if callable(CONFIG["delay_between_requests"]) else CONFIG["delay_between_requests"]
                delay *= random.uniform(2.0, 4.0)  # 2-4x longer delay for full interactions
                await asyncio.sleep(delay)
                
            except Exception as e:
                logging.error(f"Interaction worker error: {e}")
                await asyncio.sleep(10)
                
    async def stats_reporter(self):
        """Regular reporting of statistics."""
        report_interval = 300  # Report every 5 minutes
        
        while True:
            try:
                # Get current stats
                stats = self.get_run_stats()
                
                # Log stats
                logging.info(f"=== ViewBot Stats [{stats['runtime']}] ===")
                logging.info(f"Views: {stats['views']} ({stats['views_per_hour']}/hour)")
                logging.info(f"Claps: {stats['claps']} ({stats['claps_per_hour']}/hour)")
                logging.info(f"Comments: {stats['comments']} ({stats['comments_per_hour']}/hour)")
                logging.info(f"Follows: {stats['follows']}")
                logging.info(f"Success rate: {stats['success_rate']}%")
                logging.info(f"Proxies: {stats['active_proxies']}/{stats['total_proxies']} ({stats['proxy_success_rate']}% success)")
                
                # Send webhook notification if configured
                if self.webhook_manager:
                    self.webhook_manager.send_notification(
                        f"ViewBot Stats Report - Runtime: {stats['runtime']}\n" +
                        f"Views: {stats['views']} ({stats['views_per_hour']}/hour)\n" +
                        f"Engagements: {stats['claps']} claps, {stats['comments']} comments, {stats['follows']} follows\n" +
                        f"Success rate: {stats['success_rate']}%"
                    )
                
                await asyncio.sleep(report_interval)
                
            except Exception as e:
                logging.error(f"Stats reporter error: {e}")
                await asyncio.sleep(60)
                
    async def main(self):
        """Main entry point for the ViewBot."""
        try:
            # Print banner
            print("""
            ╔═══════════════════════════════════════════════╗
            ║    SupremeViewBot v1.0.0 - Medium Optimizer   ║
            ╚═══════════════════════════════════════════════╝
            """)
            
            logging.info(f"Starting ViewBot targeting: {self.target_url}")
            logging.info(f"Configuration: {self.config}")
            
            # Start background tasks
            tasks = []
            
            # Start view workers
            view_workers = self.config["max_concurrent_threads"]
            logging.info(f"Starting {view_workers} view workers...")
            for _ in range(view_workers):
                tasks.append(asyncio.create_task(self.view_worker()))
                
            # Start interaction workers (fewer than view workers)
            interaction_workers = max(1, view_workers // 3)
            logging.info(f"Starting {interaction_workers} interaction workers...")
            for _ in range(interaction_workers):
                tasks.append(asyncio.create_task(self.interaction_worker()))
                
            # Start stats reporter
            tasks.append(asyncio.create_task(self.stats_reporter()))
            
            # Wait for all tasks
            await asyncio.gather(*tasks)
            
        except KeyboardInterrupt:
            logging.info("ViewBot stopped by user")
            
            # Print final stats
            stats = self.get_run_stats()
            print("\n=== Final ViewBot Stats ===")
            print(f"Runtime: {stats['runtime']}")
            print(f"Views: {stats['views']} ({stats['views_per_hour']}/hour)")
            print(f"Claps: {stats['claps']} ({stats['claps_per_hour']}/hour)")
            print(f"Comments: {stats['comments']} ({stats['comments_per_hour']}/hour)")
            print(f"Follows: {stats['follows']}")
            print(f"Success rate: {stats['success_rate']}%")
            
        except Exception as e:
            logging.error(f"Main loop error: {e}")
            raise

# Async HTTP client for simple view requests
class AsyncViewClient:
    def __init__(self, target_url, proxy_pool=None, user_agent_manager=None, use_tor=False):
        self.target_url = target_url
        self.proxy_pool = proxy_pool or ProxyPool()
        self.user_agent_manager = user_agent_manager or UserAgentManager()
        self.use_tor = use_tor
        self.tor_controller = TorController() if use_tor else None
        
        # Stats
        self.successful_requests = 0
        self.failed_requests = 0
        
    async def send_requests(self, num_requests, delay_range=(1, 5)):
        """Send multiple async requests with delays between them."""
        tasks = []
        for _ in range(num_requests):
            # Get proxy
            proxy = None
            if not self.use_tor:
                proxy = self.proxy_pool.get_proxy()
                if not proxy:
                    logging.warning("No working proxies available, skipping request")
                    continue
            elif self.use_tor and self.tor_controller:
                # 20% chance to renew Tor IP
                if random.random() < 0.2:
                    self.tor_controller.renew_ip()
                    await asyncio.sleep(1)
            
            # Schedule request
            tasks.append(self.send_request(proxy))
            
            # Random delay
            await asyncio.sleep(random.uniform(*delay_range))
            
        # Wait for all requests to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successful and failed requests
        for result in results:
            if isinstance(result, Exception):
                self.failed_requests += 1
            elif result:
                self.successful_requests += 1
            else:
                self.failed_requests += 1
                
        return self.successful_requests, self.failed_requests
    
    async def send_request(self, proxy=None):
        """Send a single async request."""
        headers = {
            "User-Agent": self.user_agent_manager.get_random(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        # Random cookies
        cookies = {
            "sid": f"1:{random.randint(1000000000, 9999999999)}",
            "_ga": f"GA1.2.{random.randint(1000000000, 9999999999)}.{int(time.time()-random.randint(1000000, 9999999))}",
        }
        
        # Random chance to add referrer
        if random.random() < 0.3:
            referrers = [
                "https://www.google.com/search?q=programming+tips",
                "https://twitter.com/search?q=coding",
                "https://www.reddit.com/r/programming/",
                "https://news.ycombinator.com/",
                "https://medium.com/tag/programming",
                "https://www.linkedin.com/feed/"
            ]
            headers["Referer"] = random.choice(referrers)
            
        try:
            proxy_url = None
            if self.use_tor:
                proxy_url = "http://127.0.0.1:9050"
            elif proxy:
                proxy_url = proxy
                
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(cookies=cookies, timeout=timeout) as session:
                async with session.get(self.target_url, headers=headers, proxy=proxy_url, allow_redirects=True) as response:
                    if response.status == 200:
                        logging.info(f"Request successful via {proxy_url or 'direct'}")
                        if proxy and not self.use_tor:
                            self.proxy_pool.report_success(proxy)
                        return True
                    else:
                        logging.warning(f"Request failed: {response.status}")
                        if proxy and not self.use_tor:
                            self.proxy_pool.report_failure(proxy)
                        return False
        except Exception as e:
            logging.error(f"Request error: {e}")
            if proxy and not self.use_tor:
                self.proxy_pool.report_failure(proxy)
            return False

# Command-line interface
def parse_arguments():
    """Parse command-line arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Supreme ViewBot - Medium Article Optimizer')
    
    parser.add_argument('--url', type=str, help='Target URL to boost')
    parser.add_argument('--threads', type=int, help='Number of concurrent threads')
    parser.add_argument('--requests', type=int, help='Requests per thread')
    parser.add_argument('--delay', type=float, help='Delay between requests (seconds)')
    parser.add_argument('--tor', action='store_true', help='Use Tor for routing')
    parser.add_argument('--no-freedium', action='store_true', help='Disable Freedium for paywall bypass')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--captcha-key', type=str, help='2CAPTCHA API key')
    parser.add_argument('--webhook', type=str, help='Discord webhook URL')
    parser.add_argument('--view-only', action='store_true', help='Only send view requests, no interactions')
    parser.add_argument('--proxy-file', type=str, help='File containing proxy list')
    parser.add_argument('--account-file', type=str, help='File containing account credentials')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO', help='Logging level')
    
    return parser.parse_args()

# Main entry point
def main():
    """Main entry point for the script."""
    # Parse arguments
    args = parse_arguments()
    
    # Update config with command-line arguments
    if args.url:
        CONFIG["target_url"] = args.url
    if args.threads:
        CONFIG["max_concurrent_threads"] = args.threads
    if args.requests:
        CONFIG["requests_per_thread"] = lambda: args.requests
    if args.delay:
        CONFIG["delay_between_requests"] = lambda: args.delay
    if args.tor:
        CONFIG["use_tor"] = True
    if args.no_freedium:
        CONFIG["use_freedium"] = False
    if args.captcha_key:
        CONFIG["captcha_api_key"] = args.captcha_key
    if args.webhook:
        CONFIG["webhook_url"] = args.webhook
    if args.log_level:
        CONFIG["log_level"] = getattr(logging, args.log_level)
    
    # Set up logging
    logging.basicConfig(
        level=CONFIG["log_level"],
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("viewbot.log"),
            logging.StreamHandler()
        ]
    )
    
    # Initialize the bot
    viewbot = ViewBot(CONFIG)
    
    # Run the bot
    if args.view_only:
        # Simple view-only mode
        async def run_view_only():
            client = AsyncViewClient(
                CONFIG["target_url"],
                proxy_pool=viewbot.proxy_pool,
                user_agent_manager=viewbot.user_agent_manager,
                use_tor=CONFIG["use_tor"]
            )
            
            num_requests = CONFIG["requests_per_thread"]() if callable(CONFIG["requests_per_thread"]) else CONFIG["requests_per_thread"]
            num_requests *= CONFIG["max_concurrent_threads"]
            
            delay_min = CONFIG["delay_between_requests"]() if callable(CONFIG["delay_between_requests"]) else CONFIG["delay_between_requests"]
            delay_max = delay_min * 1.5
            
            logging.info(f"Running in view-only mode, sending {num_requests} requests...")
            success, failed = await client.send_requests(num_requests, (delay_min, delay_max))
            
            logging.info(f"View-only mode complete. Successful: {success}, Failed: {failed}")
            
        asyncio.run(run_view_only())
    else:
        # Full interaction mode
        asyncio.run(viewbot.main())

if __name__ == "__main__":
    main()

# Random delay function with jitter
def random_delay():
    base_delay = random.uniform(DELAY_MIN, DELAY_MAX)
    jitter = random.uniform(-1, 1)  # Add ±1 second jitter
    return max(0.5, base_delay + jitter)  # Ensure at least 0.5s delay

# Generate random cookies to appear more human-like
def generate_random_cookies():
    return {
        "sid": f"1:{random.randint(1000000000, 9999999999)}",
        "_ga": f"GA1.2.{random.randint(1000000000, 9999999999)}.{int(time.time()-random.randint(1000000, 9999999))}",
        "_gid": f"GA1.2.{random.randint(1000000000, 9999999999)}.{int(time.time())}",
        "xsrf": base64.b64encode(os.urandom(16)).decode('utf-8'),
        "_med": "refer",
        "_parsely_visitor": f"{{{random.randint(1000000000, 9999999999)}}}",
        "sz": f"{random.randint(1, 100)}",
    }

# Generate domain-specific cookies for Medium
def generate_medium_cookies():
    cookies = generate_random_cookies()
    
    # Add Medium-specific cookies
    cookies.update({
        "uid": f"{random.randint(10000, 99999)}",
        "optimizelyEndUserId": f"{random.randint(1000000000, 9999999999)}",
        "lightstep_session_id": f"{random.randint(1000000000, 9999999999)}",
        "lightstep_guid": f"{random.randint(1000000000, 9999999999)}"
    })
    
    return cookies

# Single async request function
async def send_view_request(session, url, proxy=None):
    # Generate random user agent
    user_agent = random.choice(USER_AGENTS)
    
    # Generate random referrer (30% chance of having a referrer)
    referrer = random.choice(REFERRERS) if random.random() < 0.3 else None
    
    # Generate random cookies
    cookies = generate_medium_cookies()
    
    # Prepare headers
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0"
    }
    
    # Add referrer if selected
    if referrer:
        headers["Referer"] = referrer
    
    # Parse domain for later use
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    
    try:
        # Configure proxy
        proxy_url = proxy
        
        # Set up connection timeout
        timeout = aiohttp.ClientTimeout(total=10)
        
        # Send the request
        async with session.get(
            url, 
            headers=headers, 
            cookies=cookies, 
            proxy=proxy_url, 
            timeout=timeout,
            ssl=False  # Disable SSL verification
        ) as response:
            # Log result
            if response.status == 200:
                logging.info(f"✅ Success: status={response.status}, proxy={proxy_url}")
                
                # 20% chance to request assets to appear more realistic
                if random.random() < 0.2:
                    try:
                        # Get page content
                        html = await response.text()
                        
                        # Parse HTML
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Find a few asset URLs
                        asset_urls = []
                        
                        # Add 2-3 JS files
                        for script in soup.find_all('script', src=True)[:3]:
                            src = script.get('src')
                            if src:
                                # Make absolute URL if needed
                                if src.startswith('//'):
                                    src = 'https:' + src
                                elif src.startswith('/'):
                                    src = f"https://{domain}{src}"
                                    
                                asset_urls.append(src)
                        
                        # Add 1-2 CSS files
                        for link in soup.find_all('link', rel='stylesheet', href=True)[:2]:
                            href = link.get('href')
                            if href:
                                # Make absolute URL if needed
                                if href.startswith('//'):
                                    href = 'https:' + href
                                elif href.startswith('/'):
                                    href = f"https://{domain}{href}"
                                    
                                asset_urls.append(href)
                        
                        # Request 2-3 random assets
                        if asset_urls:
                            for asset_url in random.sample(asset_urls, min(3, len(asset_urls))):
                                try:
                                    async with session.get(
                                        asset_url, 
                                        headers=headers, 
                                        cookies=cookies, 
                                        proxy=proxy_url,
                                        timeout=aiohttp.ClientTimeout(total=5),
                                        ssl=False
                                    ) as asset_response:
                                        logging.debug(f"Asset request: {asset_url} - Status: {asset_response.status}")
                                except Exception as e:
                                    logging.debug(f"Asset request failed: {str(e)[:100]}...")
                    except Exception as e:
                        logging.debug(f"Error processing assets: {str(e)[:100]}...")
                
                return True
            else:
                logging.warning(f"❌ Failed: status={response.status}, proxy={proxy_url}")
                return False
    except Exception as e:
        error_msg = str(e)
        logging.error(f"❌ Error: {error_msg[:100]}..., proxy={proxy}")
        return False

# Main async function to send multiple requests
async def send_multiple_requests(url, proxies, num_requests):
    success_count = 0
    failure_count = 0
    request_count = 0
    
    # If we have fewer proxies than requests, we'll need to reuse them
    if proxies and len(proxies) < num_requests:
        # Create a cycle of proxies
        from itertools import cycle
        proxy_cycle = cycle(proxies)
        proxy_list = [next(proxy_cycle) for _ in range(num_requests)]
    else:
        # Use each proxy once
        proxy_list = proxies[:num_requests] if proxies else [None] * num_requests
    
    # Randomize proxy usage for unpredictability
    random.shuffle(proxy_list)
    
    # Connection pooling with SSL verification disabled
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=False, limit=10)
    ) as session:
        tasks = []
        
        for i in range(num_requests):
            proxy = proxy_list[i] if proxy_list else None
            
            # Create task
            task = asyncio.create_task(send_view_request(session, url, proxy))
            tasks.append(task)
            
            request_count += 1
            logging.info(f"Request {request_count}/{num_requests} scheduled with proxy: {proxy}")
            
            # Random delay between requests
            await asyncio.sleep(random_delay())
        
        # Wait for tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successes and failures
        for result in results:
            if isinstance(result, Exception):
                failure_count += 1
            elif result:
                success_count += 1
            else:
                failure_count += 1
    
        return success_count, failure_count

# Main execution
async def main():
    print("\n" + "="*60)
    print("🚀 Simple Medium ViewBot - View-Only Mode")
    print("="*60 + "\n")
    
    # Load and validate proxies
    proxies = load_proxies()
    if proxies:
        valid_proxies = validate_proxies(proxies)
    else:
        valid_proxies = []
        logging.warning("No proxies loaded, proceeding with direct connections")
    
    logging.info(f"Starting view bot with target: {TARGET_URL}")
    logging.info(f"Sending {NUM_REQUESTS} requests with {len(valid_proxies)} validated proxies")
    
    # Record start time
    start_time = time.time()
    
    # Send requests
    success, failure = await send_multiple_requests(TARGET_URL, valid_proxies, NUM_REQUESTS)
    
    # Calculate runtime
    runtime = time.time() - start_time
    
    # Print results
    print("\n" + "="*60)
    print(f"✅ Successful requests: {success}")
    print(f"❌ Failed requests: {failure}")
    print(f"⏱️ Total runtime: {runtime:.2f} seconds")
    print(f"🚀 Success rate: {(success / NUM_REQUESTS) * 100:.2f}%")
    print(f"⚡ Requests per minute: {(success + failure) / (runtime / 60):.2f}")
    print("="*60 + "\n")
    
    logging.info(f"ViewBot completed. Success: {success}, Failure: {failure}, Runtime: {runtime:.2f}s")

if __name__ == "__main__":
    try:
        # Enable SSL warnings removal (for cleaner logs)
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Run the main async function
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️ ViewBot stopped by user")
    except Exception as e:
        print(f"\n⚠️ Error: {e}")
