import time
import random
import asyncio
import logging
import aiohttp
from bs4 import BeautifulSoup
import base64

class YouTubeViewBot:
    """
    YouTube-specific ViewBot implementation for boosting video views,
    engagement, and discovering new content.
    """
    
    def __init__(self, config, youtube_interactor, browser_manager, 
                 proxy_pool, account_manager=None, tor_controller=None, 
                 webhook_manager=None, captcha_solver=None,
                 user_agent_manager=None):
        """
        Initialize the YouTube ViewBot.
        
        Args:
            config: Configuration dictionary
            youtube_interactor: YouTubeInteractor instance
            browser_manager: BrowserManager instance
            proxy_pool: ProxyPool instance
            account_manager: Optional AccountManager instance
            tor_controller: Optional TorController instance
            webhook_manager: Optional WebhookManager instance
            captcha_solver: Optional CaptchaSolver instance
            user_agent_manager: Optional UserAgentManager instance
        """
        self.config = config
        self.target_url = config["target_url"]
        self.use_tor = config.get("use_tor", False)
        
        # Components
        self.youtube_interactor = youtube_interactor
        self.browser_manager = browser_manager
        self.proxy_pool = proxy_pool
        self.account_manager = account_manager
        self.tor_controller = tor_controller
        self.webhook_manager = webhook_manager
        self.captcha_solver = captcha_solver
        self.user_agent_manager = user_agent_manager
        
        # Initialize video queue
        self.video_queue = asyncio.Queue()
        self.visited_videos = set()
        
        # Add initial target URL to queue
        self.queue_video(self.target_url)
        
        # Stats tracking
        self.stats = {
            "views": 0,
            "likes": 0,
            "comments": 0,
            "subscribes": 0,
            "failures": 0,
            "start_time": time.time()
        }
        
    def queue_video(self, video_url, priority=1):
        """
        Add a video to the queue if not already visited.
        
        Args:
            video_url: URL of the video to queue
            priority: Priority level (lower is higher priority)
            
        Returns:
            bool: True if video was added, False if already visited
        """
        if video_url not in self.visited_videos:
            asyncio.create_task(self.video_queue.put((priority, video_url)))
            self.visited_videos.add(video_url)
            return True
        return False
        
    async def get_next_video(self):
        """
        Get the next video from the queue.
        
        Returns:
            str: Video URL or target URL if queue is empty
        """
        try:
            _, video_url = await self.video_queue.get()
            return video_url
        except asyncio.QueueEmpty:
            return self.target_url
            
    def mark_video_done(self):
        """Mark the current video as processed."""
        self.video_queue.task_done()
        
    async def interact_with_video(self, video_url, proxy=None, account=None):
        """
        Full video interaction flow.
        
        Args:
            video_url: URL of the video to interact with
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
                
            # Load the page
            logging.info(f"Loading video: {video_url}")
            driver.get(video_url)
            
            # Wait for page to load
            time.sleep(random.uniform(3, 7))
            
            # Check for CAPTCHA
            if not self.youtube_interactor._detect_and_solve_captcha(driver, video_url):
                logging.warning("CAPTCHA detected but not solved")
                
            # Log in if account provided
            if account:
                # YouTube login implementation would go here
                # This would need to be added to the YouTubeInteractor class
                pass
                
            # Extract video info before interaction
            before_stats = self.youtube_interactor.extract_video_info(driver)
            
            # Simulate video viewing
            self.youtube_interactor.simulate_human_viewing(driver)
            
            # Random chance to like based on configuration
            like_probability = self.config.get("like_probability", 0.7)
            if random.random() < like_probability:
                if self.youtube_interactor.like_video(driver):
                    self.stats["likes"] += 1
            
            # Random chance to comment based on configuration
            comment_probability = self.config.get("comment_probability", 0.3)
            if random.random() < comment_probability:
                # Use custom comment text if configured
                comment_text = self.config.get("comment_text", "Great video! Really enjoyed this content.")
                if self.youtube_interactor.post_comment(driver, comment_text):
                    self.stats["comments"] += 1
                    
            # Random chance to subscribe based on configuration
            subscribe_probability = self.config.get("subscribe_probability", 0.1)
            if random.random() < subscribe_probability:
                if self.youtube_interactor.subscribe_to_channel(driver):
                    self.stats["subscribes"] += 1
                    
            # Find and queue next video
            next_video = self.youtube_interactor.find_next_video(driver)
            if next_video:
                self.queue_video(next_video)
                
            # Extract video info after interaction
            after_stats = self.youtube_interactor.extract_video_info(driver)
            
            # Navigate to next video and send notification
            if random.random() < 0.5:  # 50% chance to navigate to next video
                next_video_url = self.youtube_interactor.navigate_to_next_video(driver)
                if next_video_url and self.webhook_manager:
                    # Send webhook notification about navigation
                    self.webhook_manager.send_notification(
                        f"Bot has navigated to next video: {next_video_url}"
                    )
            
            # Send webhook notification if configured
            if self.webhook_manager:
                # Prepare stats comparison
                before_after = {
                    "title": after_stats.get("title", "Unknown Video"),
                    "channel": after_stats.get("channel", "Unknown Channel"),
                    "url": video_url,
                    "before": before_stats,
                    "after": after_stats,
                    "actions": {
                        "viewed": True,
                        "liked": self.stats["likes"] > 0,
                        "commented": self.stats["comments"] > 0,
                        "subscribed": self.stats["subscribes"] > 0
                    }
                }
                
                # Send notification
                self.webhook_manager.send_notification(
                    f"Interacted with video: {before_after['title']} by {before_after['channel']}. " +
                    f"Actions: viewed=True, " +
                    f"liked={before_after['actions']['liked']}, " +
                    f"commented={before_after['actions']['commented']}, " +
                    f"subscribed={before_after['actions']['subscribed']}"
                )
                
            # Report success
            self.stats["views"] += 1
            success = True
            return True
            
        except Exception as e:
            logging.error(f"Error interacting with video: {e}")
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
            if account and self.account_manager:
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
            "VISITOR_INFO1_LIVE": f"{random.randint(1000000000, 9999999999)}",
            "YSC": f"{base64.b64encode(os.urandom(16)).decode('utf-8')[:10]}",
            "PREF": f"f4={random.randint(1000, 9999)}&f5={random.randint(1000, 9999)}",
            "LOGIN_INFO": f"AFmmF2swRQIhAI{base64.b64encode(os.urandom(16)).decode('utf-8')[:30]}",
        }
        
        # Add referrers - 40% chance of having a referrer for YouTube
        if random.random() < 0.4:
            referrers = [
                "https://www.google.com/search?q=youtube+videos",
                "https://www.reddit.com/r/videos/",
                "https://twitter.com/search?q=youtube",
                "https://www.facebook.com/",
                "https://www.youtube.com/feed/trending",
                "https://www.youtube.com/feed/subscriptions",
                "https://www.youtube.com/feed/explore"
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
                # First request for the main video page
                async with session.get(url, headers=headers, proxy=proxy_url, allow_redirects=True, ssl=not self.config.get("verify_ssl", False)) as response:
                    if response.status == 200:
                        self.stats["views"] += 1
                        logging.info(f"View request successful: {response.status}")
                        
                        # 30% chance to make additional requests to simulate video playback
                        if random.random() < 0.3:
                            # Parse HTML to find video ID for additional requests
                            html = await response.text()
                            
                            # Extract video ID
                            video_id = None
                            if "v=" in url:
                                video_id = url.split("v=")[1].split("&")[0]
                            else:
                                import re
                                match = re.search(r'"videoId":"([^"]+)"', html)
                                if match:
                                    video_id = match.group(1)
                            
                            if video_id:
                                # Make additional requests to simulate video player loading
                                player_url = f"https://www.youtube.com/youtubei/v1/player?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"
                                player_data = {
                                    "videoId": video_id,
                                    "context": {
                                        "client": {
                                            "clientName": "WEB",
                                            "clientVersion": "2.20220203.01.00"
                                        }
                                    }
                                }
                                
                                # Send player request
                                try:
                                    async with session.post(player_url, json=player_data, headers=headers, proxy=proxy_url) as player_response:
                                        logging.debug(f"Player request: {player_response.status}")
                                except Exception as e:
                                    logging.debug(f"Player request failed: {e}")
                                
                                # Simulate video progress events
                                for _ in range(3):
                                    progress = random.randint(10, 90)  # Random progress percentage
                                    next_url = f"https://www.youtube.com/api/stats/watchtime?ns=yt&el=detailpage&cpn={random.randint(1000000000, 9999999999)}&docid={video_id}&ver=2&cmt={progress}&ei={random.randint(1000000000, 9999999999)}"
                                    try:
                                        async with session.get(next_url, headers=headers, proxy=proxy_url) as progress_response:
                                            logging.debug(f"Progress request: {progress_response.status}")
                                    except Exception as e:
                                        logging.debug(f"Progress request failed: {e}")
                                    
                                    await asyncio.sleep(random.uniform(1, 3))
                        
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
        likes_per_hour = (self.stats["likes"] / runtime) * 3600 if runtime > 0 else 0
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
            "likes": self.stats["likes"],
            "comments": self.stats["comments"],
            "subscribes": self.stats["subscribes"],
            "failures": self.stats["failures"],
            "views_per_hour": round(views_per_hour, 2),
            "likes_per_hour": round(likes_per_hour, 2),
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
                
                # Get a video URL (either target or from queue)
                video_url = await self.get_next_video()
                
                # Send the view request
                await self.simple_view_request(video_url, proxy)
                
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
                # Get a video URL
                video_url = await self.get_next_video()
                
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
                
                # Get an account (30% chance)
                account = None
                if random.random() < 0.3 and self.account_manager:
                    account = self.account_manager.get_account()
                
                # Perform the interaction
                await self.interact_with_video(video_url, proxy, account)
                
                # Mark task as done if it came from queue
                if video_url != self.target_url:
                    self.mark_video_done()
                
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
                logging.info(f"Likes: {stats['likes']} ({stats['likes_per_hour']}/hour)")
                logging.info(f"Comments: {stats['comments']} ({stats['comments_per_hour']}/hour)")
                logging.info(f"Subscribes: {stats['subscribes']}")
                logging.info(f"Success rate: {stats['success_rate']}%")
                logging.info(f"Proxies: {stats['active_proxies']}/{stats['total_proxies']} ({stats['proxy_success_rate']}% success)")
                
                # Send webhook notification if configured
                if self.webhook_manager:
                    self.webhook_manager.send_notification(
                        f"YouTube ViewBot Stats Report - Runtime: {stats['runtime']}\n" +
                        f"Views: {stats['views']} ({stats['views_per_hour']}/hour)\n" +
                        f"Engagements: {stats['likes']} likes, {stats['comments']} comments, {stats['subscribes']} subscribes\n" +
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
            ║    SupremeViewBot v1.0.0 - YouTube Optimizer  ║
            ╚═══════════════════════════════════════════════╝
            """)
            
            logging.info(f"Starting YouTube ViewBot targeting: {self.target_url}")
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
            print(f"Likes: {stats['likes']} ({stats['likes_per_hour']}/hour)")
            print(f"Comments: {stats['comments']} ({stats['comments_per_hour']}/hour)")
            print(f"Subscribes: {stats['subscribes']}")
            print(f"Success rate: {stats['success_rate']}%")
            
        except Exception as e:
            logging.error(f"Main loop error: {e}")
            raise


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
    # Import required modules
    import aiohttp
    import random
    import logging
    import time
    
    class SimpleYouTubeViewClient:
        """Simple client for YouTube view boosting."""
        
        def __init__(self, target_url, proxy_pool, user_agent_manager, use_tor=False, config=None):
            self.target_url = target_url
            self.proxy_pool = proxy_pool
            self.user_agent_manager = user_agent_manager
            self.use_tor = use_tor
            self.tor_controller = tor_controller
            self.config = config or {}
            
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
                tasks.append(self.send_request(self.target_url, proxy))
                
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
        
        async def send_request(self, url, proxy=None):
            """Send a single async request to view a YouTube video."""
            headers = {
                "User-Agent": self.user_agent_manager.get_random(),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Cache-Control": "max-age=0"
            }
            
            # YouTube-specific cookies to appear more legitimate
            cookies = {
                "VISITOR_INFO1_LIVE": f"{random.randint(1000000000, 9999999999)}",
                "YSC": f"{base64.b64encode(os.urandom(16)).decode('utf-8')[:10]}",
                "PREF": f"f4={random.randint(1000, 9999)}&f5={random.randint(1000, 9999)}"
            }
            
            # Add referrer sometimes (30% chance)
            if random.random() < 0.3:
                referrers = [
                    "https://www.google.com/search?q=youtube+videos",
                    "https://www.reddit.com/r/videos/",
                    "https://twitter.com/search?q=youtube",
                    "https://www.facebook.com/"
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
                        url, 
                        headers=headers, 
                        proxy=proxy_url, 
                        allow_redirects=True,
                        ssl=not self.config.get("verify_ssl", False)
                    ) as response:
                        if response.status == 200:
                            logging.info(f"Request successful via {proxy_url or 'direct'}")
                            
                            # If successful, try to simulate some video viewing
                            html = await response.text()
                            
                            # Extract video ID
                            video_id = None
                            if "v=" in url:
                                video_id = url.split("v=")[1].split("&")[0]
                            else:
                                import re
                                match = re.search(r'"videoId":"([^"]+)"', html)
                                if match:
                                    video_id = match.group(1)
                            
                            # If we found a video ID, make additional requests
                            if video_id and random.random() < 0.5:  # 50% chance
                                # Make "progress" requests to simulate watching
                                for progress in [25, 50, 75]:
                                    try:
                                        progress_url = f"https://www.youtube.com/api/stats/watchtime?ns=yt&el=detailpage&cpn={random.randint(1000000000, 9999999999)}&docid={video_id}&ver=2&cmt={progress}&ei={random.randint(1000000000, 9999999999)}"
                                        async with session.get(progress_url, headers=headers, proxy=proxy_url) as progress_response:
                                            await progress_response.read()  # Consume response
                                    except:
                                        pass  # Ignore errors in progress requests
                                    
                                    await asyncio.sleep(random.uniform(1, 3))
                            
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
    
    # Run the simple client
    target_url = config["target_url"]
    use_tor = config.get("use_tor", False)
    
    client = SimpleYouTubeViewClient(
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
    
    logging.info(f"Running YouTube bot in view-only mode, sending {num_requests} requests...")
    success, failed = await client.send_requests(num_requests, (delay_min, delay_max))
    
    logging.info(f"View-only mode complete. Successful: {success}, Failed: {failed}")
    
    return success, failed
