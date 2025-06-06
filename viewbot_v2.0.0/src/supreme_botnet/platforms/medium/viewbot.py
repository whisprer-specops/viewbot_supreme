import time
import random
import asyncio
import logging
import aiohttp
import os
from bs4 import BeautifulSoup
import base64

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
        
        # Initialize article queue
        self.article_queue = asyncio.Queue()
        self.visited_articles = set()
        
        # Load starting articles
        for article in config.get("starting_articles", []):
            self.queue_article(article)
        
        # Stats tracking
        self.stats = {
            "views": 0,
            "claps": 0,
            "comments": 0,
            "follows": 0,
            "failures": 0,
            "start_time": time.time()
        }
        
    def queue_article(self, article_url, priority=1):
        """
        Add an article to the queue if not already visited.
        
        Args:
            article_url: URL of the article to queue
            priority: Priority level (lower is higher priority)
            
        Returns:
            bool: True if article was added, False if already visited
        """
        if article_url not in self.visited_articles:
            asyncio.create_task(self.article_queue.put((priority, article_url)))
            self.visited_articles.add(article_url)
            return True
        return False
        
    async def get_next_article(self):
        """
        Get the next article from the queue.
        
        Returns:
            str: Article URL or target URL if queue is empty
        """
        try:
            _, article_url = await self.article_queue.get()
            return article_url
        except asyncio.QueueEmpty:
            return self.target_url
            
    def mark_article_done(self):
        """Mark the current article as processed."""
        self.article_queue.task_done()
        
    async def interact_with_article(self, article_url, proxy=None, account=None):
        """
        Full article interaction flow.
        
        Args:
            article_url: URL of the article to interact with
            proxy: Optional proxy to use
            account: Optional account credentials
            
        Returns:
            bool: True if interaction was successful, False otherwise
        """
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
            
            # Random chance to clap based on configuration
            clap_probability = self.config.get("clap_probability", 0.6)
            if random.random() < clap_probability:
                if self.medium_interactor.clap_for_article(driver):
                    self.stats["claps"] += 1
            
            # Random chance to comment based on configuration
            comment_probability = self.config.get("comment_probability", 0.2)
            if random.random() < comment_probability:
                if self.medium_interactor.post_comment(driver):
                    self.stats["comments"] += 1
                    
            # Random chance to follow author based on configuration
            follow_probability = self.config.get("follow_probability", 0.3)
            if random.random() < follow_probability:
                if self.medium_interactor.follow_author(driver):
                    self.stats["follows"] += 1
                    
            # Find next article
            next_article = self.medium_interactor.find_next_article(driver)
            if next_article:
                self.queue_article(next_article)
                
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
        """
            Send a simple async HTTP request to register a view.

            Args:
                url: URL to view
                proxy: Optional proxy to use

            Returns:
                bool: True if request was successful, False otherwise
            """
    # Get user agent
    user_agent = self.user_agent_manager.get_random() if self.user_agent_manager else "Mozilla/5.0"
    
    headers = {
        "User-Agent": user_agent,
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
    
    # Add cookies to simulate logged-in state (these are dummy cookies)
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
            ssl_context = False  # Explicitly disable SSL verification
            
            async with aiohttp.ClientSession(cookies=cookies, timeout=timeout) as session:
                async with session.get(
                    self.target_url, 
                    headers=headers, 
                    proxy=proxy_url, 
                    allow_redirects=True,
                    ssl=ssl_context
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

    logging.info(f"Running in view-only mode, sending {num_requests} requests...")
    success, failed = await client.send_requests(num_requests, (delay_min, delay_max))
    
    logging.info(f"View-only mode complete. Successful: {success}, Failed: {failed}")
    
    return success, failed

