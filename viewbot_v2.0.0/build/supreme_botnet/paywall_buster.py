import asyncio import aiohttp import json import logging import random import re from typing import List, Dict, Tuple from bs4 import BeautifulSoup from colorama import urlparse from colorama import Fore, Style from config import PROXY_SOURCES, CHECK_INTERVAL from rapidproxyscan import ProxyScanManager from decryptor_bot import WebhookDecryptorBot

Setup logging

setup_logging = lambda config: logging.basicConfig( level=config.get("log_level", logging.INFO"), format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", filename=config.get("log_file", "botnet.log") )

class MediumPaywallBuster: """Class to bypass Medium paywalls and interact with articles.""" def init(self, config: Dict, proxies: List[Tuple[str, int, float, str]]], decryption_key: str = None): self.config = config self.proxies = proxies self.decryption_key = decryption_key self.accounts = self._load_accounts() self.session = None self.webhook_manager = None

def _load_accounts(self) -> List[Dict]:
    """Load accounts from my_accounts.json."""
    try:
        with open(self.config.get("account_file", "my_accounts.json"), "r") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load accounts: {e}")
        return [{"email": "got.girl.camera@gmail.com", "password": "hunter2"}]  # Fallback

async def initialize(self):
    """Initialize aiohttp session and webhook manager."""
    self.session = aiohttp.ClientSession()
    if self.config.get("webhook_url") and self.decryption_key:
        self.webhook_manager = WebhookDecryptorBot(decryption_key=self.decryption_key)
        self.webhook_task = asyncio.create_task(
            self.webhook_manager.start(self.config.get("discord_bot_token"))
        )

async def cleanup(self):
    """Close session and webhook manager."""
    if self.session and not self.session.closed:
        await self.session.close()
    if self.webhook_manager:
        await self.webhook_manager.close()

async def get_freedium_content(self, url: str, proxy: str) -> str:
    """Fetch article content via Freedium."""
    freedium_url = f"https://freedium.cfd/{url}"
    headers = {
        "User-Agent": random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/91.0.4472.114 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/91.0.4472.101 Safari/537.36"
        ])
    }
    try:
        async with self.session.get(freedium_url, proxy=proxy, headers=headers, timeout=10) as response:
            response.raise_for_status()
            soup = BeautifulSoup(await response.text(), "html.parser")
            article = soup.find("article")
            return article.get_text(strip=True) if article else ""
    except Exception as e:
        logging.error(f"Freedium failed for {url}: {e}")
        return ""

async def login(self, account: Dict, proxy: str) -> bool:
    """Login to Medium with an account."""
    login_url = "https://medium.com/m/signin"
    headers = {"User-Agent": random.choice(self.config.get("user_agents", []))}
    payload = {"email": account["email"], "password": account["password"]}
    try:
        async with self.session.post(login_url, json=payload, proxy=proxy, headers=headers, timeout=15) as response:
            if response.status == 200:
                logging.info(f"Logged in as {account['email']}")
                return True
            logging.error(f"Login failed for {account['email']}: {response.status}")
            return False
    except Exception as e:
        logging.error(f"Login error for {account['email']}: {e}")
        return False

async def clap_article(self, article_url: str, account: Dict, proxy: str) -> bool:
    """Clap (up to 50 times) for an article."""
    clap_url = f"https://medium.com/_/api/posts/{self._extract_post_id(article_url)}/claps"
    headers = {"User-Agent": random.choice(self.config.get("user_agents", []))}
    clap_count = random.randint(10, 50)  # Random claps for realism
    payload = {"clapCount": clap_count}
    try:
        if await self.login(account, proxy):
            async with self.session.post(clap_url, json=payload, proxy=proxy, headers=headers, timeout=10) as response:
                if response.status == 200:
                    logging.info(f"Clapped {clap_count} times for {article_url} with {account['email']}")
                    if self.webhook_manager:
                        await self.webhook_manager.get_channel(self.config.get("discord_channel_id")).send(
                            f"Clapped {clap_count} times for {article_url}"
                        )
                    return True
                logging.error(f"Clap failed for {article_url}: {response.status}")
                return False
    except Exception as e:
        logging.error(f"Clap error for {article_url}: {e}")
        return False

async def comment_article(self, article_url: str, account: Dict, proxy: str) -> bool:
    """Comment on an article with a generated comment."""
    comment_url = f"https://medium.com/_/api/posts/{self._extract_post_id(article_url)}/responses"
    headers = {"User-Agent": random.choice(self.config.get("user_agents", []))}
    comment = self._generate_comment()
    payload = {"content": comment}
    try:
        if await self.login(account, proxy):
            async with self.session.post(comment_url, json=payload, proxy=proxy, headers=headers, timeout=10) as response:
                if response.status == 200:
                    logging.info(f"Commented on {article_url} with {account['email']}: {comment}")
                    if self.webhook_manager:
                        await self.webhook_manager.get_channel(self.config.get("discord_channel_id")).send(
                            f"Commented on {article_url}: {comment}"
                        )
                    return True
                logging.error(f"Comment failed for {article_url}: {response.status}")
                return False
    except Exception as e:
        logging.error(f"Comment error for {article_url}: {e}")
        return False

def _extract_post_id(self, url: str) -> str:
    """Extract Medium post ID from URL."""
    match = re.search(r"/([a-f0-9]{12,16})$", url)
    return match.group(1) if match else ""

def _generate_comment(self) -> str:
    """Generate a human-like comment."""
    comments = [
        "Great insights, thanks for sharing!",
        "Really enjoyed this perspective, well written!",
        "This was super informative, keep it up!",
        "Loved the depth here, awesome post!"
    ]
    return random.choice(comments)

async def process_article(self, article_url: str):
    """Process a single article for all agents."""
    for account in self.accounts:
        proxy = f"http://{random.choice(self.proxies)[0]}:{random.choice(self.proxies)[1]}"
        content = await self.get_freedium_content(article_url, proxy)
        if not content:
            logging.warning(f"Could not fetch content for {article_url}")
            continue

        # Randomize actions to mimic human behavior
        if random.random() < self.config.get("clap_probability", 0.6):
            await self.clap_article(article_url, account, proxy)
        if random.random() < self.config.get("comment_probability", 0.2):
            await self.comment_article(article_url, account, proxy)
        await asyncio.sleep(random.uniform(20, 40))  # Random delay

async def fetch_proxies() -> List[Tuple[str, int, float, str]]: """Fetch and validate proxies using rapidproxyscan.""" scanner = ProxyScanManager( check_interval=CHECK_INTERVAL, connection_limit=1250, validation_rounds=3, validation_mode="majority", timeout=5.0, check_anonymity=True, force_fetch=False, verbose=True, single_run=True, proxy_sources=PROXY_SOURCES, proxy_test_workers=1250, proxy_fetch_interval=CHECK_INTERVAL * 2, proxy_test_timeout=5.0, proxy_test_retries=3, max_proxies_to_keep=10000, proxy_refresh_min_interval=300, test_url="http://ip-api.com/json", export_interval=300, max_fetch_attempts=5, fetch_retry_delay=5 ) await scanner.initialize() await scanner.fetch_proxy_lists() proxies = [(p.host, p.port, p.avg_response_time, p.anonymity) for p in scanner.proxies.values() if p.anonymity in ["anonymous", "elite"]] await scanner.cleanup() return proxies

async def main(): """Main entry point for paywall buster.""" parser = argparse.ArgumentParser(description="Medium Paywall Buster") parser.add_argument("--url", required=True, help="Target Medium article URL") parser.add_argument("--captcha-key", required=True, help="2CAPTCHA API key") parser.add_argument("--webhook", help="Discord webhook URL") parser.add_argument("--discord-token", help="Discord bot token") parser.add_argument("--discord-channel", type=int, help="Discord channel ID") args = parser.parse_args()

# Config
config = {
    "log_level": logging.INFO,
    "log_file": "botnet.log",
    "webhook_url": args.webhook,
    "discord_bot_token": args.discord_token,
    "discord_channel_id": args.discord_channel,
    "captcha_api_key": args.captcha_key,
    "account_file": "my_accounts.json",
    "clap_probability": 0.6,
    "comment_probability": 0.2,
    "user_agents": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/91.0.4472.114 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/91.0.4472.101 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
    ]
}

# Setup logging
setup_logging(config)

# Fetch proxies
logging.info("Fetching proxies...")
proxies = await fetch_proxies()
if not proxies:
    logging.error("No valid proxies found. Exiting...")
    return

# Load decryption key
try:
    with open("bot_key.txt", "r") as f:
        decryption_key = f.read().strip()
except Exception as e:
    logging.error(f"Failed to load decryption key: {e}")
    decryption_key = None

# Initialize and run buster
buster = MediumPaywallBuster(config, proxies, decryption_key)
await buster.initialize()
try:
    await buster.process_article(args.url)
finally:
    await buster.cleanup()

if name == "main": asyncio.run(main())