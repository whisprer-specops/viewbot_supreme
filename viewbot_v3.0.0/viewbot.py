# platforms/medium/viewbot.py
import time
import random
import asyncio
import logging
import aiohttp
from bs4 import BeautifulSoup
import base64
from core.proxy_manager import ProxyManager
from core.account import AccountManager
from core.browser import BrowserManager
from core.captcha import CaptchaSolver
from core.email import TempEmailService
from core.user_agent import UserAgentManager
from core.secure_webhook import SecureWebhookManager
from core.secure_encryption import PersistentKeyManager
from platforms.medium.interactor import MediumInteractor
from utils.stats import StatsTracker

class MediumViewBot:
    """Medium-specific ViewBot for boosting article views and engagement."""
    def __init__(self, config, medium_interactor, browser_manager, 
                 proxy_manager, account_manager, tor_controller=None, 
                 webhook_manager=None, captcha_solver=None, 
                 temp_email_service=None, user_agent_manager=None):
        self.config = config
        self.target_url = config["target_url"]
        self.use_tor = config.get("use_tor", False)
        self.use_freedium = config.get("use_freedium", False)
        self.medium_interactor = medium_interactor
        self.browser_manager = browser_manager
        self.proxy_manager = proxy_manager
        self.account_manager = account_manager
        self.tor_controller = tor_controller
        self.webhook_manager = webhook_manager or SecureWebhookManager(
            webhook_url=config.get("webhook_url"),
            key_manager=PersistentKeyManager(service_name="medium_webhook", config_dir=config.get("config_dir"))
        )
        self.captcha_solver = captcha_solver
        self.temp_email_service = temp_email_service
        self.user_agent_manager = user_agent_manager
        self.stats_tracker = StatsTracker()
        self.stats_tracker.create_counter("views")
        self.stats_tracker.create_counter("claps")
        self.stats_tracker.create_counter("comments")
        self.stats_tracker.create_counter("follows")
        self.stats_tracker.create_counter("failures")
        self.article_queue = asyncio.Queue()
        self.visited_articles = set()
        for article in config.get("starting_articles", []):
            self.queue_article(article)

    def queue_article(self, article_url, priority=1):
        if article_url not in self.visited_articles:
            asyncio.create_task(self.article_queue.put((priority, article_url)))
            self.visited_articles.add(article_url)
            return True
        return False

    async def get_next_article(self):
        try:
            _, article_url = await self.article_queue.get()
            return article_url
        except asyncio.QueueEmpty:
            return self.target_url

    def mark_article_done(self):
        self.article_queue.task_done()

    async def interact_with_article(self, article_url, proxy=None, account=None):
        driver = None
        success = False
        try:
            use_mobile = random.random() < 0.3
            driver = self.browser_manager.setup_browser(
                proxy=proxy, 
                use_tor=self.use_tor,
                use_mobile=use_mobile
            )
            if not driver:
                logging.error("Failed to create browser")
                return False
            url = self.medium_interactor.get_freedium_url(article_url) if self.use_freedium else article_url
            logging.info(f"Loading article: {url}")
            driver.get(url)
            if not self.medium_interactor._detect_and_solve_captcha(driver, url):
                logging.warning("CAPTCHA detected but not solved")
            if "paywall" in driver.page_source.lower() or "member-only" in driver.page_source.lower():
                logging.info("Paywall detected, trying alternative access")
                if account:
                    logging.info(f"Attempting login with account: {account['username']}")
                    if not self.medium_interactor.login_with_credentials(driver, account['username'], account['password']):
                        logging.info("Account login failed, trying email login")
                        if not await self.medium_interactor.login_with_email(driver, article_url):
                            logging.error("Could not bypass paywall")
                            return False
                else:
                    logging.info("No account available, trying email login")
                    if not await self.medium_interactor.login_with_email(driver, article_url):
                        logging.error("Could not bypass paywall")
                        return False
                driver.get(url)
                time.sleep(3)
            before_stats = self.medium_interactor.extract_medium_stats(driver)
            self.medium_interactor.simulate_human_reading(driver)
            if random.random() < self.config.get("clap_probability", 0.6):
                if self.medium_interactor.clap_for_article(driver):
                    self.stats_tracker.increment("claps")
            if random.random() < self.config.get("comment_probability", 0.2):
                if self.medium_interactor.post_comment(driver):
                    self.stats_tracker.increment("comments")
            if random.random() < self.config.get("follow_probability", 0.3):
                if self.medium_interactor.follow_author(driver):
                    self.stats_tracker.increment("follows")
            next_article = self.medium_interactor.find_next_article(driver)
            if next_article:
                self.queue_article(next_article)
            after_stats = self.medium_interactor.extract_medium_stats(driver)
            if self.webhook_manager:
                before_after = {
                    "title": after_stats.get("title", "Unknown Article"),
                    "url": article_url,
                    "before": before_stats,
                    "after": after_stats,
                    "actions": {
                        "read": True,
                        "clapped": self.stats_tracker.get_stats().get("claps") > 0,
                        "commented": self.stats_tracker.get_stats().get("comments") > 0,
                        "followed": self.stats_tracker.get_stats().get("follows") > 0
                    }
                }
                self.webhook_manager.send_notification(
                    f"Interacted with article: {before_after['title']}. " +
                    f"Actions: read={before_after['actions']['read']}, " +
                    f"clapped={before_after['actions']['clapped']}, " +
                    f"commented={before_after['actions']['commented']}, " +
                    f"followed={before_after['actions']['followed']}"
                )
            self.stats_tracker.increment("views")
            success = True
            return True
        except Exception as e:
            logging.error(f"Error interacting with article: {e}")
            self.stats_tracker.increment("failures")
            return False
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            if account:
                self.account_manager.release_account(account['username'], success)
            if proxy and not self.use_tor:
                if success:
                    self.proxy_manager.report_success(proxy)
                else:
                    self.proxy_manager.report_failure(proxy)

    async def simple_view_request(self, url, proxy=None):
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
        cookies = {
            "sid": f"1:{random.randint(1000000000, 9999999999)}",
            "_ga": f"GA1.2.{random.randint(1000000000, 9999999999)}.{int(time.time()-random.randint(1000000, 9999999))}",
            "_gid": f"GA1.2.{random.randint(1000000000, 9999999999)}.{int(time.time())}",
            "xsrf": base64.b64encode(os.urandom(16)).decode('utf-8'),
            "_med": "refer",
            "_parsely_visitor": f"{{{random.randint(1000000000, 9999999999)}}}",
            "sz": f"{random.randint(1, 100)}",
        }
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
            ssl_context = False
            async with aiohttp.ClientSession(cookies=cookies, timeout=timeout) as session:
                async with session.get(
                    url, headers=headers, proxy=proxy_url, allow_redirects=True, ssl=ssl_context
                ) as response:
                    if response.status == 200:
                        self.stats_tracker.increment("views")
                        logging.info(f"View request successful: {response.status}")
                        if random.random() < 0.2:
                            html = await response.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            asset_urls = []
                            for script in soup.find_all('script', src=True):
                                asset_urls.append(script['src'])
                            for link in soup.find_all('link', rel='stylesheet', href=True):
                                asset_urls.append(link['href'])
                            for img in soup.find_all('img', src=True):
                                asset_urls.append(img['src'])
                            if asset_urls:
                                for asset_url in random.sample(asset_urls, min(5, len(asset_urls))):
                                    if not asset_url.startswith('http'):
                                        if asset_url.startswith('//'):
                                            asset_url = 'https:' + asset_url
                                        elif asset_url.startswith('/'):
                                            asset_url = 'https://medium.com' + asset_url
                                    try:
                                        async with session.get(
                                            asset_url, headers=headers, proxy=proxy_url, ssl=ssl_context
                                        ) as asset_response:
                                            logging.debug(f"Asset request: {asset_url} - Status: {asset_response.status}")
                                    except Exception as e:
                                        logging.debug(f"Asset request failed: {e}")
                        if proxy and not self.use_tor:
                            self.proxy_manager.report_success(proxy)
                        return True
                    else:
                        logging.warning(f"View request failed: {response.status}")
                        if proxy and not self.use_tor:
                            self.proxy_manager.report_failure(proxy)
                        return False
        except Exception as e:
            logging.error(f"Error sending view request: {e}")
            if proxy and not self.use_tor:
                self.proxy_manager.report_failure(proxy)
            self.stats_tracker.increment("failures")
            return False

    def get_run_stats(self):
        return self.stats_tracker.get_stats()

    async def view_worker(self):
        while True:
            try:
                proxy = None
                if not self.use_tor:
                    proxy_info = await self.proxy_manager.get_proxy()
                    if not proxy_info:
                        logging.warning("No working proxies available for view worker, waiting...")
                        await asyncio.sleep(30)
                        continue
                    proxy = f"http://{proxy_info[0]}:{proxy_info[1]}"
                elif self.tor_controller:
                    if random.randint(1, 10) <= 2:
                        self.tor_controller.renew_ip()
                        await asyncio.sleep(1)
                await self.simple_view_request(self.target_url, proxy)
                delay = self.config["delay_between_requests"]() if callable(self.config["delay_between_requests"]) else self.config["delay_between_requests"]
                await asyncio.sleep(delay)
            except Exception as e:
                logging.error(f"View worker error: {e}")
                await asyncio.sleep(5)

    async def interaction_worker(self):
        while True:
            try:
                article_url = await self.get_next_article()
                proxy = None
                if not self.use_tor:
                    proxy_info = await self.proxy_manager.get_proxy()
                    if not proxy_info:
                        logging.warning("No working proxies available for interaction worker, waiting...")
                        await asyncio.sleep(30)
                        continue
                    proxy = f"http://{proxy_info[0]}:{proxy_info[1]}"
                elif self.tor_controller:
                    self.tor_controller.renew_ip()
                    await asyncio.sleep(1)
                account = None
                if random.random() < 0.5 and self.account_manager:
                    account = self.account_manager.get_account()
                await self.interact_with_article(article_url, proxy, account)
                if article_url != self.target_url:
                    self.mark_article_done()
                delay = self.config["delay_between_requests"]() if callable(self.config["delay_between_requests"]) else self.config["delay_between_requests"]
                delay *= random.uniform(2.0, 4.0)
                await asyncio.sleep(delay)
            except Exception as e:
                logging.error(f"Interaction worker error: {e}")
                await asyncio.sleep(10)

    async def stats_reporter(self):
        report_interval = 300
        while True:
            try:
                stats = self.get_run_stats()
                logging.info(f"=== ViewBot Stats [{stats['runtime']}] ===")
                logging.info(f"Views: {stats['views']} ({stats['views_per_hour']}/hour)")
                logging.info(f"Claps: {stats['claps']} ({stats['claps_per_hour']}/hour)")
                logging.info(f"Comments: {stats['comments']} ({stats['comments_per_hour']}/hour)")
                logging.info(f"Follows: {stats['follows']} ({stats['follows_per_hour']}/hour)")
                logging.info(f"Success rate: {round((stats['views'] / max(stats['views'] + stats['failures'], 1)) * 100, 2)}%")
                if self.webhook_manager:
                    self.webhook_manager.send_notification(
                        f"ViewBot Stats Report - Runtime: {stats['runtime']}\n" +
                        f"Views: {stats['views']} ({stats['views_per_hour']}/hour)\n" +
                        f"Engagements: {stats['claps']} claps, {stats['comments']} comments, {stats['follows']} follows\n" +
                        f"Success rate: {round((stats['views'] / max(stats['views'] + stats['failures'], 1)) * 100, 2)}%"
                    )
                await asyncio.sleep(report_interval)
            except Exception as e:
                logging.error(f"Stats reporter error: {e}")
                await asyncio.sleep(60)

    async def run(self):
        print("""
        ╔══════════════════════════════════════════════╗
        ║    SupremeViewBot v1.0.0 - Medium Optimizer   ║
        ╚══════════════════════════════════════════════╝
        """)
        logging.info(f"Starting ViewBot targeting: {self.target_url}")
        logging.info(f"Configuration: {self.config}")
        tasks = []
        view_workers = self.config["max_concurrent_threads"]
        logging.info(f"Starting {view_workers} view workers...")
        for _ in range(view_workers):
            tasks.append(asyncio.create_task(self.view_worker()))
        interaction_workers = max(1, view_workers // 3)
        logging.info(f"Starting {interaction_workers} interaction workers...")
        for _ in range(interaction_workers):
            tasks.append(asyncio.create_task(self.interaction_worker()))
        tasks.append(asyncio.create_task(self.stats_reporter()))
        await asyncio.gather(*tasks)

class AsyncViewClient:
    def __init__(self, target_url, proxy_manager=None, user_agent_manager=None, use_tor=False, config=None):
        self.target_url = target_url
        self.proxy_manager = proxy_manager
        self.user_agent_manager = user_agent_manager
        self.use_tor = use_tor
        self.tor_controller = None
        if use_tor:
            from core.proxy import TorController
            self.tor_controller = TorController()
        self.config = config or {}
        self.stats_tracker = StatsTracker()
        self.stats_tracker.create_counter("views")
        self.stats_tracker.create_counter("failures")

    async def send_requests(self, num_requests, delay_range=(1, 5)):
        tasks = []
        for _ in range(num_requests):
            proxy = None
            if not self.use_tor:
                proxy_info = await self.proxy_manager.get_proxy()
                if not proxy_info:
                    logging.warning("No working proxies available, skipping request")
                    continue
                proxy = f"http://{proxy_info[0]}:{proxy_info[1]}"
            elif self.tor_controller:
                if random.random() < 0.2:
                    self.tor_controller.renew_ip()
                    await asyncio.sleep(1)
            tasks.append(self.send_request(proxy))
            await asyncio.sleep(random.uniform(*delay_range))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception) or not result:
                self.stats_tracker.increment("failures")
            else:
                self.stats_tracker.increment("views")
        stats = self.stats_tracker.get_stats()
        return stats["views"], stats["failures"]

    async def send_request(self, proxy=None):
        headers = {
            "User-Agent": self.user_agent_manager.get_random() if self.user_agent_manager else "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        cookies = {
            "sid": f"1:{random.randint(1000000000, 9999999999)}",
            "_ga": f"GA1.2.{random.randint(1000000000, 9999999999)}.{int(time.time()-random.randint(1000000, 9999999))}",
        }
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
            ssl_context = False
            async with aiohttp.ClientSession(cookies=cookies, timeout=timeout) as session:
                async with session.get(
                    self.target_url, headers=headers, proxy=proxy_url, allow_redirects=True, ssl=ssl_context
                ) as response:
                    if response.status == 200:
                        logging.info(f"Request successful via {proxy_url or 'direct'}")
                        if proxy and not self.use_tor:
                            self.proxy_manager.report_success(proxy)
                        self.stats_tracker.increment("views")
                        return True
                    else:
                        logging.warning(f"Request failed: {response.status}")
                        if proxy and not self.use_tor:
                            self.proxy_manager.report_failure(proxy)
                        self.stats_tracker.increment("failures")
                        return False
        except Exception as e:
            logging.error(f"Request error: {e}")
            if proxy and not self.use_tor:
                self.proxy_manager.report_failure(proxy)
            self.stats_tracker.increment("failures")
            return False

async def run_view_only_mode(config, proxy_manager, user_agent_manager, tor_controller=None, webhook_manager=None):
    target_url = config["target_url"]
    use_tor = config.get("use_tor", False)
    client = AsyncViewClient(
        target_url,
        proxy_manager=proxy_manager,
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
    if webhook_manager:
        webhook_manager.send_notification(
            f"ViewBot Complete - View-only Mode\n" +
            f"Target: {target_url}\n" +
            f"Successful Requests: {success}\n" +
            f"Failed Requests: {failed}\n" +
            f"Success Rate: {round((success / max(success + failed, 1)) * 100, 2)}%"
        )
    return success, failed