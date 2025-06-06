# core/vote_booster.py
import asyncio
import aiohttp
import json
import logging
import random
from typing import List, Dict, Tuple
from selenium.webdriver.common.by import By
from colorama import Fore, Style
from decryptor_bot import WebhookDecryptorBot
from core.account import AccountManager
from core.captcha import CaptchaSolver
from core.email_handler import TempEmailService
from core.browser import BrowserManager
from core.user_agent import UserAgentManager
from core.secure_webhook import SecureWebhookManager
from core.secure_encryption import PersistentKeyManager
from config import (
    VOTE_ENDPOINT, VOTE_PAYLOAD, VOTE_AUTH_REQUIRED, VOTE_DELAY_MIN, VOTE_DELAY_MAX,
    VOTE_PROBABILITY, VOTE_MAX_PER_PROXY, VOTE_MAX_PER_ACCOUNT, VOTE_BROWSER_BASED,
    VOTE_LOGIN_URL, VOTE_CSRF_TOKEN_SELECTOR, ACCOUNT_FILE, AUTO_CREATE_ACCOUNTS,
    SIGNUP_URL, SIGNUP_PAYLOAD, CAPTCHA_API_KEY, CAPTCHA_ENABLED, CAPTCHA_SITE_KEY,
    CAPTCHA_PAGE_URL, TEMP_EMAIL_API, EMAIL_TIMEOUT, EMAIL_INTERVAL, BROWSER_HEADLESS,
    BROWSER_TIMEOUT, VERIFY_SSL, USE_TOR, USE_EXTENSION, EXTENSION_PATH,
    DISCORD_BOT_TOKEN, DISCORD_CHANNEL_ID, WEBHOOK_URL
)

class VoteBooster:
    """Class to boost votes on a target platform."""
    def __init__(self, config: Dict, proxy_manager, decryption_key: str = None):
        self.config = config
        self.proxy_manager = proxy_manager
        self.decryption_key = decryption_key
        self.account_manager = AccountManager(account_file=config.get("account_file", ACCOUNT_FILE))
        self.captcha_solver = CaptchaSolver(api_key=config.get("captcha_api_key", CAPTCHA_API_KEY)) if config.get("captcha_enabled", CAPTCHA_ENABLED) else None
        self.email_service = TempEmailService(api_base=config.get("temp_email_api", TEMP_EMAIL_API)) if config.get("auto_create_accounts", AUTO_CREATE_ACCOUNTS) else None
        self.user_agent_manager = UserAgentManager()
        self.browser_manager = BrowserManager(
            headless=config.get("browser_headless", BROWSER_HEADLESS),
            user_agent_manager=self.user_agent_manager,
            config=config
        ) if config.get("vote_browser_based", VOTE_BROWSER_BASED) else None
        self.session = None
        self.webhook_manager = None
        self.discord_bot = None
        self.proxy_vote_count = {}
        self.account_vote_count = {}

    async def initialize(self):
        """Initialize resources."""
        logging.info("Initializing VoteBooster...")
        self.session = aiohttp.ClientSession()
        if self.config.get("webhook_url", WEBHOOK_URL):
            key_manager = PersistentKeyManager(service_name="vote_webhook", config_dir=self.config.get("config_dir"))
            self.webhook_manager = SecureWebhookManager(webhook_url=self.config.get("webhook_url", WEBHOOK_URL), key_manager=key_manager)
        if self.config.get("discord_bot_token", DISCORD_BOT_TOKEN) and self.decryption_key:
            self.discord_bot = WebhookDecryptorBot(
                decryption_key=self.decryption_key,
                command_prefix=self.config.get("command_prefix", "!")
            )
            self.discord_bot.register_vote_callback(self.handle_vote_instruction)
            self.discord_task = asyncio.create_task(
                self.discord_bot.run(self.config.get("discord_bot_token", DISCORD_BOT_TOKEN))
            )
        logging.info("VoteBooster initialized.")

    async def cleanup(self):
        """Close resources."""
        logging.info("Cleaning up VoteBooster...")
        if self.session and not self.session.closed:
            await self.session.close()
        if self.discord_bot:
            await self.discord_bot.close()
        logging.info("VoteBooster cleanup complete.")

    async def create_account(self) -> Dict:
        """Create a new account using temporary email."""
        if not self.email_service or not self.config.get("signup_url", SIGNUP_URL):
            logging.error("Account creation not configured")
            return None
        email = self.email_service.get_email()
        if not email:
            logging.error("Failed to get temporary email")
            return None
        payload = self.config.get("signup_payload", SIGNUP_PAYLOAD).copy()
        payload["email"] = email
        headers = {"User-Agent": self.user_agent_manager.get_random()}
        try:
            async with self.session.post(
                self.config.get("signup_url", SIGNUP_URL),
                json=payload,
                headers=headers,
                timeout=15
            ) as response:
                if response.status == 200:
                    verify_url = await self.email_service.check_inbox(
                        timeout=self.config.get("email_timeout", EMAIL_TIMEOUT),
                        interval=self.config.get("email_interval", EMAIL_INTERVAL)
                    )
                    if verify_url:
                        async with self.session.get(verify_url, headers=headers, timeout=15) as verify_response:
                            if verify_response.status == 200:
                                account = {"username": email, "password": payload.get("password", "hunter2")}
                                self.account_manager.add_account(email, payload.get("password", "hunter2"))
                                logging.info(f"Created account: {email}")
                                return account
                    logging.error("No verification email found")
                logging.error(f"Signup failed: {response.status}")
        except Exception as e:
            logging.error(f"Account creation error: {e}")
        return None

    async def login(self, account: Dict, proxy: str, driver=None) -> bool:
        """Login to the voting platform."""
        if not self.config.get("vote_auth_required", VOTE_AUTH_REQUIRED):
            return True
        login_url = self.config.get("vote_login_url", VOTE_LOGIN_URL)
        headers = {"User-Agent": self.user_agent_manager.get_random()}
        payload = {"username": account["username"], "password": account["password"]}
        if self.config.get("vote_browser_based", VOTE_BROWSER_BASED) and driver:
            try:
                driver.get(login_url)
                driver.find_element(By.NAME, "username").send_keys(account["username"])
                driver.find_element(By.NAME, "password").send_keys(account["password"])
                if self.config.get("vote_csrf_token_selector", VOTE_CSRF_TOKEN_SELECTOR):
                    csrf_token = driver.find_element(By.CSS_SELECTOR, self.config.get("vote_csrf_token_selector")).get_attribute("value")
                    payload["csrf_token"] = csrf_token
                driver.find_element(By.CSS_SELECTOR, "button[type=submit]").click()
                await asyncio.sleep(5)
                if "login" not in driver.current_url.lower():
                    logging.info(f"Logged in as {account['username']} via browser")
                    return True
                logging.error(f"Browser login failed for {account['username']}")
                return False
            except Exception as e:
                logging.error(f"Browser login error for {account['username']}: {e}")
                return False
        else:
            try:
                async with self.session.post(login_url, json=payload, proxy=proxy, headers=headers, timeout=15) as response:
                    if response.status == 200:
                        logging.info(f"Logged in as {account['username']}")
                        return True
                    logging.error(f"Login failed for {account['username']}: {response.status}")
                    return False
            except Exception as e:
                logging.error(f"Login error for {account['username']}: {e}")
                return False

    async def handle_captcha(self, driver, proxy: str) -> bool:
        """Handle reCAPTCHA if present."""
        if not self.captcha_solver or not self.config.get("captcha_enabled", CAPTCHA_ENABLED):
            return True
        site_key = self.config.get("captcha_site_key", CAPTCHA_SITE_KEY)
        page_url = self.config.get("captcha_page_url", CAPTCHA_PAGE_URL) or driver.current_url
        solution = self.captcha_solver.solve_recaptcha(site_key, page_url)
        if solution and self.captcha_solver.apply_solution(driver, solution):
            logging.info("CAPTCHA solved successfully")
            return True
        logging.error("CAPTCHA solving failed")
        return False

    async def cast_vote(self, vote_url: str, account: Dict, proxy: str) -> bool:
        """Cast a vote using the specified proxy and account."""
        proxy_key = proxy
        if proxy_key not in self.proxy_vote_count:
            self.proxy_vote_count[proxy_key] = 0
        if self.proxy_vote_count[proxy_key] >= self.config.get("vote_max_per_proxy", VOTE_MAX_PER_PROXY):
            logging.warning(f"Proxy {proxy} has reached max votes ({self.config.get('vote_max_per_proxy', VOTE_MAX_PER_PROXY)})")
            return False

        if self.config.get("vote_auth_required", VOTE_AUTH_REQUIRED):
            account_key = account["username"]
            if account_key not in self.account_vote_count:
                self.account_vote_count[account_key] = 0
            if self.account_vote_count[account_key] >= self.config.get("vote_max_per_account", VOTE_MAX_PER_ACCOUNT):
                logging.warning(f"Account {account_key} has reached max votes ({self.config.get('vote_max_per_account', VOTE_MAX_PER_ACCOUNT)})")
                return False

        headers = {"User-Agent": self.user_agent_manager.get_random()}
        payload = self.config.get("vote_payload", VOTE_PAYLOAD)
        driver = None
        if self.config.get("vote_browser_based", VOTE_BROWSER_BASED):
            proxy_info = proxy.replace("http://", "").split(":")
            driver = self.browser_manager.setup_browser(
                proxy=proxy,
                use_tor=self.config.get("use_tor", USE_TOR),
                use_extension=self.config.get("use_extension", USE_EXTENSION),
                extension_path=self.config.get("extension_path", EXTENSION_PATH),
                use_mobile=random.choice([True, False])
            )
            if not driver:
                logging.error("Failed to setup browser")
                return False
            try:
                if self.config.get("vote_auth_required", VOTE_AUTH_REQUIRED):
                    if not await self.login(account, proxy, driver):
                        return False
                driver.get(vote_url)
                if self.config.get("captcha_enabled", CAPTCHA_ENABLED):
                    if not await self.handle_captcha(driver, proxy):
                        return False
                # Placeholder for browser interaction (e.g., click vote button)
                vote_button_selector = self.config.get("vote_button_selector")  # Add to config if needed
                if vote_button_selector:
                    driver.find_element(By.CSS_SELECTOR, vote_button_selector).click()
                await asyncio.sleep(5)
                if "success" in driver.current_url.lower() or "thank" in driver.current_url.lower():
                    self.proxy_vote_count[proxy_key] += 1
                    if self.config.get("vote_auth_required", VOTE_AUTH_REQUIRED):
                        self.account_vote_count[account_key] += 1
                    logging.info(f"Vote cast for {vote_url} with {account['username']} via {proxy} (browser)")
                    if self.webhook_manager:
                        self.webhook_manager.send_notification(f"🗳 Vote cast for {vote_url} via {proxy}")
                    return True
                logging.error("Browser vote failed")
                return False
            except Exception as e:
                logging.error(f"Browser vote error for {vote_url}: {e}")
                return False
            finally:
                if driver:
                    driver.quit()
        else:
            try:
                if self.config.get("vote_auth_required", VOTE_AUTH_REQUIRED):
                    if not await self.login(account, proxy):
                        return False
                async with self.session.post(
                    vote_url, json=payload, proxy=proxy, headers=headers, timeout=10
                ) as response:
                    if response.status == 200:
                        self.proxy_vote_count[proxy_key] += 1
                        if self.config.get("vote_auth_required", VOTE_AUTH_REQUIRED):
                            self.account_vote_count[account_key] += 1
                        logging.info(f"Vote cast for {vote_url} with {account['username']} via {proxy}")
                        if self.webhook_manager:
                            self.webhook_manager.send_notification(f"🗳 Vote cast for {vote_url} via {proxy}")
                        return True
                    logging.error(f"Vote failed for {vote_url}: {response.status}")
                    return False
            except Exception as e:
                logging.error(f"Vote error for {vote_url}: {e}")
                return False

    async def process_votes(self, vote_url: str):
        """Process votes for the target URL."""
        logging.info(f"Starting vote boosting for {vote_url}")
        while True:
            await self.proxy_manager.update_proxies()
            if self.config.get("auto_create_accounts", AUTO_CREATE_ACCOUNTS):
                new_account = await self.create_account()
                if new_account:
                    logging.info(f"Using new account: {new_account['username']}")
            for _ in range(len(self.account_manager.accounts) or 1):
                account = self.account_manager.get_account()
                if not account and not self.config.get("auto_create_accounts", AUTO_CREATE_ACCOUNTS):
                    logging.warning("No accounts available")
                    break
                if random.random() < self.config.get("vote_probability", VOTE_PROBABILITY):
                    proxy_info = await self.proxy_manager.get_proxy()
                    if not proxy_info:
                        logging.warning("No proxies available, waiting...")
                        await asyncio.sleep(5)
                        continue
                    proxy = f"http://{proxy_info[0]}:{proxy_info[1]}"
                    success = await self.cast_vote(vote_url, account or {"username": "anonymous", "password": ""}, proxy)
                    if account:
                        self.account_manager.release_account(account["username"], success=success)
                    delay = random.uniform(
                        self.config.get("vote_delay_min", VOTE_DELAY_MIN),
                        self.config.get("vote_delay_max", VOTE_DELAY_MAX)
                    )
                    await asyncio.sleep(delay)
            if self.config.get("single_run", SINGLE_RUN):
                break
        logging.info(f"Completed vote boosting for {vote_url}")

    async def handle_vote_instruction(self, vote_url: str, payload: Dict):
        """Handle vote instructions from Discord."""
        logging.info(f"Received vote instruction: {vote_url}, payload: {payload}")
        self.config["vote_endpoint"] = vote_url
        self.config["vote_payload"] = payload
        await self.process_votes(vote_url)