import time
import random
import asyncio
import logging
import aiohttp
from bs4 import BeautifulSoup
from utils.stats import StatsTracker # Added import

class MediumViewBot:
    """
    Medium-specific ViewBot implementation for boosting article views,
    engagement, and discovering new content.
    """

    def __init__(self, config, medium_interactor, browser_manager,
                 proxy_pool, account_manager, tor_controller=None,
                 webhook_manager=None, captcha_solver=None,
                 temp_email_service=None, user_agent_manager=None):
        """
        Initialize the Medium ViewBot.

        Args:
            config: Configuration dictionary
            medium_interactor: MediumInteractor instance
            browser_manager: BrowserManager instance
            proxy_pool: ProxyPool instance
            account_manager: AccountManager instance
            tor_controller: Optional TorController instance
            webhook_manager: Optional WebhookManager instance
            captcha_solver: Optional CaptchaSolver instance
            temp_email_service: Optional TempEmailService instance
            user_agent_manager: Optional UserAgentManager instance
        """
        self.config = config
        self.target_url = config["target_url"]
        self.use_tor = config.get("use_tor", False)
        self.use_freedium = config.get("use_freedium", False)

        # Components
        self.medium_interactor = medium_interactor
        self.browser_manager = browser_manager
        self.proxy_pool = proxy_pool
        self.account_manager = account_manager
        self.tor_controller = tor_controller
        self.webhook_manager = webhook_manager
        self.captcha_solver = captcha_solver
        self.temp_email_service = temp_email_service
        self.user_agent_manager = user_agent_manager

        # Stats
        self.stats_interval = config.get("stats_interval", 60) # Every 60 seconds
        self.stats_tracker = None # Initialized later

        self.tasks = []
        self.running = False

    async def run(self):
        """Run the Medium ViewBot."""
        self.running = True
        self.stats_tracker = StatsTracker()
        self.stats_tracker.create_counter("total_requests")
        self.stats_tracker.create_counter("successful_requests")
        self.stats_tracker.create_counter("failed_requests")
        self.stats_tracker.create_counter("page_loads")
        self.stats_tracker.create_counter("engagements")

        # Start stats reporting task
        self.tasks.append(asyncio.create_task(self._report_stats_periodically()))

        # Start worker tasks
        num_threads = self.config.get("max_concurrent_threads", 4)
        for _ in range(num_threads):
            self.tasks.append(asyncio.create_task(self._worker()))

        try:
            await asyncio.gather(*self.tasks)
        except asyncio.CancelledError:
            logging.info("MediumViewBot stopped.")
        finally:
            self.running = False
            await self.browser_manager.close_all_browsers() # Added this line
            logging.info("MediumViewBot finished.")

    async def _worker(self):
        """Worker task for processing requests."""
        while self.running:
            try:
                proxy = self.proxy_pool.get_random_proxy() if not self.use_tor else None
                user_agent = self.user_agent_manager.get_random()

                async with self.browser_manager.setup_browser(proxy=proxy, use_tor=self.use_tor, user_agent=user_agent) as driver:
                    if not driver:
                        self.stats_tracker.increment("failed_requests")
                        continue

                    # Navigate and interact
                    if await self.medium_interactor.view_article(driver, self.target_url, self.use_freedium):
                        self.stats_tracker.increment("successful_requests")
                        self.stats_tracker.increment("page_loads")
                        # Simulate engagement based on mode
                        if self.config.get("mode", "full") == "full":
                            if random.random() < 0.7: # 70% chance to clap
                                await self.medium_interactor.clap_article(driver)
                                self.stats_tracker.increment("engagements")
                            if random.random() < 0.3: # 30% chance to comment
                                await self.medium_interactor.post_comment(driver, "Great article!")
                                self.stats_tracker.increment("engagements")
                            if random.random() < 0.2: # 20% chance to follow author
                                await self.medium_interactor.follow_author(driver)
                                self.stats_tracker.increment("engagements")
                    else:
                        self.stats_tracker.increment("failed_requests")

                    # Introduce delay between requests
                    delay = random.uniform(self.config["delay_between_requests"](),
                                           self.config["delay_between_requests"]() * 1.5)
                    await asyncio.sleep(delay)

            except Exception as e:
                logging.error(f"MediumViewBot worker error: {e}")
                self.stats_tracker.increment("failed_requests")
                await asyncio.sleep(5) # Prevent rapid failure loop

    async def _report_stats_periodically(self):
        """Report statistics periodically."""
        while self.running:
            await asyncio.sleep(self.stats_interval)
            stats = self.stats_tracker.get_stats()
            logging.info(f"Current Stats: {stats}")
            if self.webhook_manager:
                self.webhook_manager.send_notification(f"Current MediumViewBot Stats: {stats}")


class AsyncViewClient:
    """
    Lightweight asynchronous client for view-only mode.
    """
    def __init__(self, target_url, proxy_pool, user_agent_manager, use_tor, config=None, stats_tracker=None):
        self.target_url = target_url
        self.proxy_pool = proxy_pool
        self.user_agent_manager = user_agent_manager
        self.use_tor = use_tor
        self.config = config or {}
        self.stats_tracker = stats_tracker # Initialized stats_tracker
        self.headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    async def send_request(self):
        """Send a single HTTP request."""
        proxy = self.proxy_pool.get_random_proxy() if not self.use_tor else None
        user_agent = self.user_agent_manager.get_random()
        self.headers["User-Agent"] = user_agent

        connector = None
        proxy_auth = None

        if proxy:
            if "@" in proxy: # Handle authenticated proxies
                auth_part, proxy_addr = proxy.split("@")
                _, auth_string = auth_part.split("://")
                username, password = auth_string.split(":")
                proxy_auth = aiohttp.BasicAuth(username, password)
                proxy = f"http://{proxy_addr}"

        if self.use_tor:
            # For Tor, use the default proxy settings if Tor is configured
            # Assumes Tor is running on localhost:9050 (SOCKS5)
            # No specific aiohttp proxy configuration needed beyond
            # routing system traffic through Tor, or by setting up a socks5 proxy in connector
            connector = aiohttp.TCPConnector(enable_cleanup=True, limit_per_host=self.config.get("max_concurrent_threads", 4))
        elif proxy:
            connector = aiohttp.TCPConnector(enable_cleanup=True, limit_per_host=self.config.get("max_concurrent_threads", 4))


        try:
            async with aiohttp.ClientSession(headers=self.headers, connector=connector) as session:
                async with session.get(self.target_url, proxy=proxy, proxy_auth=proxy_auth,
                                       verify_ssl=self.config.get("verify_ssl", False),
                                       timeout=self.config.get("request_timeout", 30)) as response:
                    if response.status == 200:
                        logging.info(f"Successfully viewed {self.target_url} (via {proxy or 'direct'})")
                        if self.stats_tracker: # Increment stats
                            self.stats_tracker.increment("successful_requests")
                        return True
                    else:
                        logging.warning(f"Request failed: {response.status} (via {proxy or 'direct'})")
                        if proxy and not self.use_tor:
                            self.proxy_pool.report_failure(proxy)
                        if self.stats_tracker: # Increment stats
                            self.stats_tracker.increment("failed_requests")
                        return False
        except aiohttp.ClientError as e:
            logging.error(f"Request error (aiohttp): {e} (via {proxy or 'direct'})")
            if proxy and not self.use_tor:
                self.proxy_pool.report_failure(proxy)
            if self.stats_tracker: # Increment stats
                self.stats_tracker.increment("failed_requests")
            return False
        except asyncio.TimeoutError:
            logging.error(f"Request timed out (via {proxy or 'direct'})")
            if proxy and not self.use_tor:
                self.proxy_pool.report_failure(proxy)
            if self.stats_tracker: # Increment stats
                self.stats_tracker.increment("failed_requests")
            return False
        except Exception as e:
            logging.error(f"Unexpected request error: {e} (via {proxy or 'direct'})")
            if proxy and not self.use_tor:
                self.proxy_pool.report_failure(proxy)
            if self.stats_tracker: # Increment stats
                self.stats_tracker.increment("failed_requests")
            return False


async def run_view_only_mode(config, proxy_pool, user_agent_manager, tor_controller=None, webhook_manager=None):
    """
    Run the ViewBot in view-only mode.

    Args:
        config: Configuration dictionary
        proxy_pool: ProxyPool instance
        user_agent_manager: UserAgentManager instance
        tor_controller: Optional TorController instance
        webhook_manager: Optional WebhookManager instance

    Returns:
        tuple: (successful_requests, failed_requests)
    """
    target_url = config["target_url"]
    use_tor = config.get("use_tor", False)

    stats_tracker = StatsTracker() # Initialize StatsTracker
    stats_tracker.create_counter("total_requests")
    stats_tracker.create_counter("successful_requests")
    stats_tracker.create_counter("failed_requests")


    client = AsyncViewClient(
        target_url,
        proxy_pool=proxy_pool,
        user_agent_manager=user_agent_manager,
        use_tor=use_tor,
        config=config,
        stats_tracker=stats_tracker # Pass stats_tracker to client
    )

    num_requests = config["requests_per_thread"]() if callable(config["requests_per_thread"]) else config["requests_per_thread"]
    num_requests *= config["max_concurrent_threads"]

    delay_min = config["delay_between_requests"]() if callable(config["delay_between_requests"]) else config["delay_between_requests"]
    delay_max = delay_min * 1.5

    logging.info(f"Running in view-only mode, sending {num_requests} requests...")

    async def _view_only_worker():
        while True:
            stats_tracker.increment("total_requests") # Increment total requests
            await client.send_request()
            await asyncio.sleep(random.uniform(delay_min, delay_max))

    tasks = []
    for _ in range(config["max_concurrent_threads"]):
        tasks.append(asyncio.create_task(_view_only_worker()))

    async def _report_stats_periodically_view_only():
        while True:
            await asyncio.sleep(config.get("stats_interval", 60)) # Use stats_interval from config
            current_stats = stats_tracker.get_stats()
            logging.info(f"Current View-Only Stats: {current_stats}")
            if webhook_manager:
                webhook_manager.send_notification(f"Current View-Only Mode Stats: {current_stats}")

    tasks.append(asyncio.create_task(_report_stats_periodically_view_only())) # Add stats reporting task

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        logging.info("View-only mode stopped.")
    finally:
        final_stats = stats_tracker.get_stats()
        logging.info(f"View-only mode finished. Successful: {final_stats.get('successful_requests', 0)}, Failed: {final_stats.get('failed_requests', 0)}")
        if webhook_manager:
            webhook_manager.send_notification(f"View-only mode summary: Successful: {final_stats.get('successful_requests', 0)}, Failed: {final_stats.get('failed_requests', 0)}")

    return final_stats.get('successful_requests', 0), final_stats.get('failed_requests', 0)

async def extra_view_request(self, url, cookies, headers, proxy=None):
    if random.random() < 0.3:
        referrers = [
            "https://www.google.com/search?q=medium+article",
            "https://www.reddit.com/r/programming/",
            "https://twitter.com/search?q=medium",
            "https://www.linkedin.com/",
            "https://www.facebook.com/",
            "https://medium.com/",
            "https://news.ycombinator.com/"
        ]
        headers["Referer"] = random.choice(referrers)

    proxy_url = None
    if self.use_tor:
        proxy_url = "http://127.0.0.1:9050"
    elif proxy:
        proxy_url = proxy

    timeout = aiohttp.ClientTimeout(total=30)
    ssl_context = False

    async with aiohttp.ClientSession(cookies=cookies, timeout=timeout) as session:
        async with session.get(
            url, 
            headers=headers, 
            proxy=proxy_url, 
            allow_redirects=True, 
            ssl=ssl_context
        ) as response:
            if response.status == 200:
                self.stats["views"] += 1
                logging.info(f"View request successful: {response.status}")

                if random.random() < 0.2:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    asset_urls = [tag['src'] for tag in soup.find_all(src=True)]
                    for asset_url in random.sample(asset_urls, min(5, len(asset_urls))):
                        if not asset_url.startswith(('http', 'https')):
                            asset_url = f"https://medium.com{asset_url}"
                        try:
                            async with session.get(asset_url, headers=headers, proxy=proxy_url, ssl=ssl_context) as _:
                                pass
                        except Exception as e:
                            logging.debug(f"Asset request failed: {e}")
                if proxy and not self.use_tor:
                    self.proxy_pool.report_success(proxy)
                return True
            else:
                logging.warning(f"View request failed: {response.status}")
                if proxy and not self.use_tor:
                    self.proxy_pool.report_failure(proxy)
                return False