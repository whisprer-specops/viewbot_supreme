```python
"""
ProxyManager Module
Integrates optimized RapidProxyScan for high-performance proxy management
"""

import asyncio
import logging
import random
import ipaddress
from collections import defaultdict
from typing import Dict, List, Tuple, Set, Optional, Any
from pathlib import Path
import aiohttp
from aiodns import DNSResolver
from rapidproxyscan import ProxyInfo  # Import base ProxyInfo
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor

# Optimized test endpoints
OPTIMIZED_TEST_ENDPOINTS = [
    'https://proxy-test.fastping.io/ping',  # Custom micro-service (50-byte JSON)
    'https://api.ipify.org/?format=json',   # Lightweight fallback
    'http://ip-api.com/json/'               # Reliable but slower
]

# DNS cache
DNS_CACHE = {}

class OptimizedProxyInfo(ProxyInfo):
    def __init__(self, host: str, port: int, protocol: str = "http", country: str = "Unknown",
                 avg_response_time: float = 0, reliability: float = 0, anonymity: str = "unknown"):
        super().__init__(host, port, protocol, country, avg_response_time, reliability, anonymity)
        self.netblock = self._get_netblock(host)

    def _get_netblock(self, host: str) -> str:
        try:
            ip = ipaddress.ip_address(host)
            return str(ipaddress.ip_network(f"{host}/24", strict=False))
        except ValueError:
            return "unknown"

class OptimizerIntegration:
    def __init__(self, config):
        self.dns_resolver = DNSResolver()
        self.user_agents = config.get("user_agents", [])
        self.logger = logging.getLogger("proxy_optimizer")

    async def initialize(self):
        self.logger.info("Optimizer: Pre-resolving test endpoints...")
        for url in OPTIMIZED_TEST_ENDPOINTS:
            domain = urlparse(url).hostname
            try:
                result = await self.dns_resolver.query(domain, 'A')
                DNS_CACHE[domain] = [r.host for r in result]
                self.logger.debug(f"DNS cached for {domain}: {DNS_CACHE[domain]}")
            except Exception as e:
                self.logger.warning(f"Failed to pre-resolve {domain}: {e}")
        self.logger.info("Optimizer: Initialization complete.")

    async def optimize_proxy_test(self, session: aiohttp.ClientSession, proxy_info: OptimizedProxyInfo) -> Dict[str, Any]:
        endpoint = OPTIMIZED_TEST_ENDPOINTS[0] if proxy_info.reliability > 50 else random.choice(OPTIMIZED_TEST_ENDPOINTS)
        headers = self._get_random_headers()
        return {
            'url': endpoint,
            'headers': headers,
            'is_fast_track': proxy_info.reliability > 80,
            'use_binary_protocol': False
        }

    async def post_test_processing(self, proxy_info: OptimizedProxyInfo, success: bool, response_time: float, endpoint: str):
        if success:
            proxy_info.reliability = min(100, proxy_info.reliability + 10)
            proxy_info.avg_response_time = (proxy_info.avg_response_time + response_time) / 2 if proxy_info.avg_response_time else response_time
        else:
            proxy_info.reliability = max(0, proxy_info.reliability - 20)
        proxy_info.last_tested = time.time()
        self.logger.debug(f"Proxy {proxy_info.host}:{proxy_info.port} updated: reliability={proxy_info.reliability}, response_time={proxy_info.avg_response_time:.2f}ms")

    def _get_random_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "Connection": "keep-alive"
        }

class ProxyManager:
    def __init__(self, config):
        self.config = config
        self.connection_limit = config.get("connection_limit", 1250)
        self.proxy_test_timeout = config.get("proxy_test_timeout", 5.0)
        self.check_anonymity = config.get("check_anonymity", True)
        self.validation_rounds = config.get("validation_rounds", 3)
        self.validation_mode = config.get("validation_mode", "majority")
        self.proxy_sources = config.get("proxy_sources", [])
        self.proxy_test_workers = config.get("proxy_test_workers", self.connection_limit)
        self.proxy_fetch_interval = config.get("proxy_fetch_interval", 60)
        self.proxy_test_retries = config.get("proxy_test_retries", self.validation_rounds)
        self.max_proxies_to_keep = config.get("max_proxies_to_keep", 10000)
        self.proxy_refresh_min_interval = config.get("proxy_refresh_min_interval", 300)
        self.test_url = config.get("test_url", OPTIMIZED_TEST_ENDPOINTS[0])
        self.export_interval = config.get("export_interval", 300)
        self.max_fetch_attempts = config.get("max_fetch_attempts", 5)
        self.fetch_retry_delay = config.get("fetch_retry_delay", 5)
        self.session = None
        self.connector = None
        self.proxy_fetch_executor = None
        self.proxy_test_executor = None
        self.proxies = defaultdict(OptimizedProxyInfo)
        self.verified_proxies = set()
        self.lock = asyncio.Lock()
        self.proxy_queue = asyncio.Queue()
        self.proxy_test_queue = asyncio.Queue()
        self.optimizer = OptimizerIntegration(config)
        self.netblock_failures = defaultdict(int)
        self.logger = logging.getLogger(__name__)

    async def initialize(self):
        self.connector = aiohttp.TCPConnector(limit=self.connection_limit, keepalive_timeout=30, ttl_dns_cache=300)
        self.session = aiohttp.ClientSession(connector=self.connector)
        self.proxy_fetch_executor = ThreadPoolExecutor(max_workers=self.max_fetch_attempts)
        self.proxy_test_executor = ThreadPoolExecutor(max_workers=self.proxy_test_workers)
        await self.optimizer.initialize()
        self.logger.info("Fetching initial proxy lists...")
        await self.fetch_proxy_lists()

    async def cleanup(self):
        if self.session and not self.session.closed:
            await self.session.close()
        if self.connector:
            await self.connector.close()
        if self.proxy_fetch_executor:
            self.proxy_fetch_executor.shutdown(wait=True)
        if self.proxy_test_executor:
            self.proxy_test_executor.shutdown(wait=True)
        self.logger.info("ProxyManager cleanup complete.")

    async def fetch_proxy_lists(self):
        fetched_proxies_count = 0
        for source_url in self.proxy_sources:
            self.logger.info(f"Fetching from: {source_url}")
            try:
                async with self.session.get(source_url, timeout=self.proxy_test_timeout) as response:
                    response.raise_for_status()
                    content = await response.text()
                    new_proxies = self.parse_proxy_list(content, source_url)
                    for host, port in new_proxies:
                        proxy_address = f"{host}:{port}"
                        if proxy_address not in self.proxies:
                            self.proxies[proxy_address] = OptimizedProxyInfo(host, port)
                            await self.proxy_queue.put(self.proxies[proxy_address])
                            fetched_proxies_count += 1
                self.logger.info(f"Fetched {len(new_proxies)} proxies from {source_url}.")
            except aiohttp.ClientError as e:
                self.logger.error(f"Failed to fetch from {source_url}: {e}")
        self.logger.info(f"Total new proxies added to queue: {fetched_proxies_count}")

    def parse_proxy_list(self, content: str, source_url: str) -> List[Tuple[str, int]]:
        proxies = []
        lines = content.splitlines()
        for line in lines:
            match = re.match(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)', line.strip())
            if match:
                try:
                    host = match.group(1)
                    port = int(match.group(2))
                    proxies.append((host, port))
                except ValueError:
                    self.logger.debug(f"Skipping invalid proxy format: {line}")
        return proxies

    async def test_proxy_worker(self):
        while True:
            proxy_info = await self.proxy_test_queue.get()
            if proxy_info is None:
                break
            try:
                success, response_time, anonymity = await self.test_proxy(proxy_info)
                if success:
                    if self.check_anonymity:
                        proxy_info.anonymity = anonymity
                    async with self.lock:
                        self.verified_proxies.add(f"{proxy_info.host}:{proxy_info.port}")
                        self.logger.info(f"Verified: {proxy_info.host}:{proxy_info.port} ({response_time:.2f}ms, Anonymity: {proxy_info.anonymity})")
                await self.optimizer.post_test_processing(proxy_info, success, response_time, self.test_url)
            except Exception as e:
                self.logger.error(f"Error testing proxy {proxy_info.host}:{proxy_info.port}: {e}")
            finally:
                self.proxy_test_queue.task_done()

    async def test_proxy(self, proxy_info: OptimizedProxyInfo) -> Tuple[bool, float, str]:
        start_time = time.monotonic()
        anonymity_level = "unknown"
        proxy_url = f"{proxy_info.protocol}://{proxy_info.host}:{proxy_info.port}"
        if self.netblock_failures[proxy_info.netblock] > 5:
            self.logger.debug(f"Skipping proxy {proxy_url} due to netblock failures")
            return False, 0, "unknown"
        test_config = await self.optimizer.optimize_proxy_test(self.session, proxy_info)
        if test_config['is_fast_track']:
            self.logger.debug(f"Fast-tracking reliable proxy {proxy_url}")
        else:
            try:
                async with self.session.request(
                    'CONNECT', test_config['url'], proxy=proxy_url,
                    timeout=aiohttp.ClientTimeout(total=self.proxy_test_timeout / 2)
                ) as response:
                    if response.status != 200:
                        self.netblock_failures[proxy_info.netblock] += 1
                        return False, 0, "unknown"
            except (aiohttp.ClientError, asyncio.TimeoutError):
                self.netblock_failures[proxy_info.netblock] += 1
                return False, 0, "unknown"
        try:
            async with self.session.get(
                test_config['url'], proxy=proxy_url, headers=test_config['headers'],
                timeout=self.proxy_test_timeout
            ) as response:
                response.raise_for_status()
                response_time = (time.monotonic() - start_time) * 1000
                if self.check_anonymity:
                    anonymity_level = await self.check_proxy_anonymity(proxy_info, response)
                return True, response_time, anonymity_level
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            self.logger.debug(f"Proxy {proxy_url} failed test: {e}")
            self.netblock_failures[proxy_info.netblock] += 1
            return False, 0, "unknown"

    async def check_proxy_anonymity(self, proxy_info: OptimizedProxyInfo, response: aiohttp.ClientResponse) -> str:
        headers = response.headers
        ip_data = {}
        try:
            ip_data = await response.json()
        except (aiohttp.ContentTypeError, json.JSONDecodeError):
            self.logger.debug(f"Could not decode JSON for anonymity check for {proxy_info.host}:{proxy_info.port}")
        client_ip = ip_data.get('query')
        if 'X-Forwarded-For' in headers or 'Via' in headers or 'Proxy-Connection' in headers:
            return "transparent"
        if client_ip and client_ip != proxy_info.host:
            return "anonymous"
        if client_ip == proxy_info.host:
            return "elite"
        return "unknown"

    async def get_proxy(self):
        async with self.lock:
            if not self.verified_proxies:
                await self.start_scanning_loop()
            if self.verified_proxies:
                proxy_address = random.choice(list(self.verified_proxies))
                proxy_info = self.proxies[proxy_address]
                return f"{proxy_info.protocol}://{proxy_info.host}:{proxy_info.port}"
        return None

    async def start_scanning_loop(self):
        last_fetch_time = last_export_time = 0
        workers = [asyncio.create_task(self.test_proxy_worker()) for _ in range(self.proxy_test_workers)]
        while True:
            current_time = time.time()
            if current_time - last_fetch_time >= self.proxy_fetch_interval:
                await self.fetch_proxy_lists()
                last_fetch_time = current_time
            async with self.lock:
                sorted_proxies = sorted(self.proxies.items(), key=lambda x: x[1].reliability, reverse=True)
                for addr, proxy_info in sorted_proxies:
                    if current_time - proxy_info.last_tested >= self.proxy_refresh_min_interval:
                        await self.proxy_test_queue.put(proxy_info)
                        proxy_info.last_tested = current_time
            if current_time - last_export_time >= self.export_interval and self.verified_proxies:
                await self.export_results()
                last_export_time = current_time
                self.verified_proxies.clear()
            if self.proxy_queue.empty() and self.proxy_test_queue.empty():
                await asyncio.sleep(self.config.get("check_interval", 30))
            else:
                await asyncio.sleep(1)
        for _ in workers:
            await self.proxy_test_queue.put(None)
        await asyncio.gather(*workers)

    async def export_results(self, force: bool = False):
        if not self.verified_proxies and not force:
            self.logger.info("No new verified proxies to export.")
            return
        output_dir = self.config.get("output_dir", "exported_proxies")
        filename_prefix = self.config.get("output_prefix", "proxies")
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        txt_filename = os.path.join(output_dir, f"{filename_prefix}_{timestamp}.txt")
        exported_count = 0
        try:
            with open(txt_filename, 'w') as f_txt:
                for proxy_address in sorted(list(self.verified_proxies)):
                    f_txt.write(f"{proxy_address}\n")
                    exported_count += 1
            self.logger.info(f"Exported {exported_count} verified proxies to {txt_filename}")
        except IOError as e:
            self.logger.error(f"Error exporting proxies: {e}")
```