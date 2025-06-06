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
            self.running = False            logging.info("MediumViewBot finished.")

    async def _worker(self):
        """Worker task for processing requests."""
        while self.running:
            try:
                proxy = self.proxy_pool.get_proxy() if not self.use_tor else None
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
        proxy = self.proxy_pool.get_proxy() if not self.use_tor else None
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

# Add referrers - 30% chance of having a referrer
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

try:
    proxy_url = None
    if self.use_tor:
        proxy_url = "http://127.0.0.1:9050"
    elif proxy:
        proxy_url = proxy
        
    timeout = aiohttp.ClientTimeout(total=30)
    
    # Create SSL context that ignores certificate validation
    ssl_context = False  # This explicitly disables SSL verification
    
    async with aiohttp.ClientSession(cookies=cookies, timeout=timeout) as session:
        # First request just for the main URL
        async with session.get(
            url, 
            headers=headers, 
            proxy=proxy_url, 
            allow_redirects=True, 
            ssl=ssl_context  # Use False to disable SSL verification
        ) as response:
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
                    if asset_urls:
                        for asset_url in random.sample(asset_urls, min(5, len(asset_urls))):
                            # Make sure URL is absolute
                            if not asset_url.startswith('http'):
                                if asset_url.startswith('//'):
                                    asset_url = 'https:' + asset_url
                                elif asset_url.startswith('/'):
                                    asset_url = 'https://medium.com' + asset_url
                                    
                            try:
                                async with session.get(
                                    asset_url, 
                                    headers=headers, 
                                    proxy=proxy_url, 
                                    ssl=ssl_context
                                ) as asset_response:
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
    """
    Get current statistics about the bot run.
    
    Returns:
        dict: Stats dictionary with performance metrics
    """
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
            elif self.use_tor and self.tor_controller:
                # Renew Tor IP occasionally (every 5-10 requests)
                if random.randint(1, 10) <= 2:  # 20% chance
                    self.tor_controller.renew_ip()
                    await asyncio.sleep(1)  # Allow time for IP to change
            
            # Send the view request
            await self.simple_view_request(self.target_url, proxy)
            
            # Random delay between requests
            delay = self.config["delay_between_requests"]() if callable(self.config["delay_between_requests"]) else self.config["delay_between_requests"]
            await asyncio.sleep(delay)
            
        except Exception as e:
            logging.error(f"View worker error: {e}")
            await asyncio.sleep(5)
            
async def interaction_worker(self):
    """Worker task for full browser interactions."""
    while True:
        try:
            # Get an article URL
            article_url = await self.get_next_article()
            
            # Get a proxy
            proxy = None
            if not self.use_tor:
                proxy = self.proxy_pool.get_proxy()
                if not proxy:
                    logging.warning("No working proxies available for interaction worker, waiting...")
                    await asyncio.sleep(30)
                    continue
            elif self.use_tor and self.tor_controller:
                # Always renew Tor IP before browser interaction
                self.tor_controller.renew_ip()
                await asyncio.sleep(1)  # Allow time for IP to change
            
            # Get an account (50% chance)
            account = None
            if random.random() < 0.5 and self.account_manager:
                account = self.account_manager.get_account()
            
            # Perform the interaction
            await self.interact_with_article(article_url, proxy, account)
            
            # Mark task as done if it came from queue
            if article_url != self.target_url:
                self.mark_article_done()
            
            # Random delay between interactions (longer than view delays)
            delay = self.config["delay_between_requests"]() if callable(self.config["delay_between_requests"]) else self.config["delay_between_requests"]
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
            
async def run(self):
    """Main entry point for running the ViewBot."""
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


class AsyncViewClient:
    """
    Async HTTP client for simple view requests, optimized for performance
    when full browser interactions are not needed.
    """
    
    def __init__(self, target_url, proxy_pool=None, user_agent_manager=None, use_tor=False, config=None):
        """
        Initialize the AsyncViewClient.
        
        Args:
            target_url: URL to send view requests to
            proxy_pool: Optional ProxyPool instance
            user_agent_manager: Optional UserAgentManager instance
            use_tor: Whether to route through Tor
            config: Optional configuration dictionary
        """
        self.target_url = target_url
        self.proxy_pool = proxy_pool
        self.user_agent_manager = user_agent_manager
        self.use_tor = use_tor
        self.tor_controller = None
        if use_tor:
            from core.proxy import TorController
            self.tor_controller = TorController()
        self.config = config or {}
        
        # Stats
        self.successful_requests = 0
        self.failed_requests = 0
        
    async def send_requests(self, num_requests, delay_range=(1, 5)):
        """
        Send multiple async requests with delays between them.
        
        Args:
            num_requests: Number of requests to send
            delay_range: Tuple of (min_delay, max_delay) in seconds
            
        Returns:
            tuple: (successful_requests, failed_requests)
        """
        tasks = []
        for _ in range(num_requests):
            # Get proxy
            proxy = None
            if not self.use_tor:
                proxy = self.proxy_pool.get_proxy() if self.proxy_pool else None
                if not proxy and self.proxy_pool:
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
        """
        Send a single async request.
        
        Args:
            proxy: Optional proxy to use
            
        Returns:
            bool: True if request was successful, False otherwise
        """
        headers = {
            "User-Agent": self.user_agent_manager.get_random() if self.user_agent_manager else "Mozilla/5.0",
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
                async with session.get(
                    self.target_url, 
                    headers=headers, 
                    proxy=proxy_url, 
                    allow_redirects=True,
                    ssl=not self.config.get("verify_ssl", False)
                ) as response:
                    if response.status == 200:
                        logging.info(f"Request successful via {proxy_url or 'direct'}")
                        if proxy and not self.use_tor and self.proxy_pool:
                            self.proxy_pool.report_success(proxy)
                        return True
                    else:
                        logging.warning(f"Request failed: {response.status}")
                        if proxy and not self.use_tor and self.proxy_pool:
                            self.proxy_pool.report_failure(proxy)
                        return False
        except Exception as e:
            logging.error(f"Request error: {e}")
            if proxy and not self.use_tor and self.proxy_pool:
                self.proxy_pool.report_failure(proxy)
            return False


async def run_view_only_mode(config, proxy_pool, user_agent_manager, tor_controller=None):
    """
    Run the ViewBot in view-only mode.
    
    Args:
        config: Configuration dictionary
        proxy_pool: ProxyPool instance
        user_agent_manager: UserAgentManager instance
        tor_controller: Optional TorController instance
        
    Returns:
        tuple: (successful_requests, failed_requests)
    """
    target_url = config["target_url"]
    use_tor = config.get("use_tor", False)
    
    client = AsyncViewClient(
        target_url,
        proxy_pool=proxy_pool,
        user_agent_manager=user_agent_manager,
        use_tor=use_tor,
        config=config
    )
    
    num_requests = config["requests_per_thread"]() if callable(config["requests_per_thread"]) else config["requests_per_thread"]
    num_requests *= config["max_concurrent_threads"]
    
    delay_min = config["delay_between_requests"]() if callable(config["delay_between_requests"]) else config["delay_between_requests"]
    delay_max = delay_min * 1.5
    
    logging.info(f"Running in view-only mode, sending {num_requests} requests...")
    success, failed = await client.send_requests(num_requests, (delay_min, delay_max))
    
    logging.info(f"View-only mode complete. Successful: {success}, Failed: {failed}")
    
    return success, failed
