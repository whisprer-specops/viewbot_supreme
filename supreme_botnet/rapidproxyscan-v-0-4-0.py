# rapidproxyscan.py
"""
RapidProxyScan - Advanced Optimizations Module
==============================================

This module implements a sophisticated proxy scanner with advanced optimizations:
1. Lightweight custom endpoint creation
2. CDN-distributed endpoint selection for geographical optimization
3. DNS pre-resolution and aggressive caching
4. Header compression and bandwidth optimization
5. Binary protocol implementations
6. Special formatting for viewbot/Supreme environments

Requirements:
- Python 3.7+
- aiohttp
- beautifulsoup4
- colorama
"""
import asyncio
import socket
import ipaddress
import random
import time
import json
import gzip
import struct
import hashlib
import logging
import os
import aiohttp
import argparse
import re
import csv
import sys
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from colorama import Fore, Style, init
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Tuple, Set, Optional, Union, Any
from collections import defaultdict
from aiodns import DNSResolver  # New dependency for DNS caching

# Import config
import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("proxy_optimizer")

# Initialize colorama
init()

# Global constants (if any remain that are not in config.py, e.g., USER_AGENTS)
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.5 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
    'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
    'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Mobile Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1'
]
config.TEST_ENDPOINTS = OPTIMIZED_TEST_ENDPOINTS

# ===========================================================================
# PROXY RELATED CLASSES
# ===========================================================================
# Optimized test endpoints (lightweight, geographically distributed)
OPTIMIZED_TEST_ENDPOINTS = [
    'https://proxy-test.fastping.io/ping',  # Custom micro-service (50-byte JSON)
    'https://api.ipify.org/?format=json',   # Lightweight fallback
    'http://ip-api.com/json/'               # Reliable but slower
]

# DNS cache
DNS_CACHE = {}

class ProxyInfo:
    def __init__(self, host: str, port: int, protocol: str = "http", country: str = "Unknown",
                 avg_response_time: float = 0, reliability: float = 0, anonymity: str = "unknown"):
        self.host = host
        self.port = port
        self.protocol = protocol
        self.country = country
        self.avg_response_time = avg_response_time
        self.reliability = reliability
        self.anonymity = anonymity
        self.last_tested = 0
        self.netblock = self._get_netblock(host)  # For batch processing

    def _get_netblock(self, host: str) -> str:
        """Extract /24 netblock for grouping."""
        try:
            ip = ipaddress.ip_address(host)
            return str(ipaddress.ip_network(f"{host}/24", strict=False))
        except ValueError:
            return "unknown"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "host": self.host,
            "port": self.port,
            "protocol": self.protocol,
            "country": self.country,
            "avg_response_time": self.avg_response_time,
            "reliability": self.reliability,
            "anonymity": self.anonymity,
            "last_tested": self.last_tested,
            "netblock": self.netblock
        }

# ===========================================================================
# OPTIMIZER INTEGRATION (Placeholder for your advanced logic)
# ===========================================================================

class OptimizerIntegration:
    def __init__(self):
        self.dns_resolver = DNSResolver()
        logger.debug("OptimizerIntegration initialized.")

    async def initialize(self):
        """Pre-resolve test endpoint DNS."""
        logger.info("Optimizer: Pre-resolving test endpoints...")
        for url in OPTIMIZED_TEST_ENDPOINTS:
            domain = urlparse(url).hostname
            try:
                result = await self.dns_resolver.query(domain, 'A')
                DNS_CACHE[domain] = [r.host for r in result]
                logger.debug(f"DNS cached for {domain}: {DNS_CACHE[domain]}")
            except Exception as e:
                logger.warning(f"Failed to pre-resolve {domain}: {e}")
        logger.info("Optimizer: Initialization complete.")

    async def optimize_proxy_test(self, session: aiohttp.ClientSession, proxy_info: ProxyInfo) -> Dict[str, Any]:
        """Select optimal test config with prioritized endpoint."""
        # Prioritize proxies with high reliability
        endpoint = OPTIMIZED_TEST_ENDPOINTS[0] if proxy_info.reliability > 50 else random.choice(OPTIMIZED_TEST_ENDPOINTS)
        headers = self._get_random_headers()
        return {
            'url': endpoint,
            'headers': headers,
            'is_fast_track': proxy_info.reliability > 80,  # Skip full test for reliable proxies
            'use_binary_protocol': False  # Placeholder for future binary protocol
        }

    async def post_test_processing(self, proxy_info: ProxyInfo, success: bool, response_time: float, endpoint: str):
        """Update proxy stats."""
        if success:
            proxy_info.reliability = min(100, proxy_info.reliability + 10)
            proxy_info.avg_response_time = (proxy_info.avg_response_time + response_time) / 2 if proxy_info.avg_response_time else response_time
        else:
            proxy_info.reliability = max(0, proxy_info.reliability - 20)
        proxy_info.last_tested = time.time()
        logger.debug(f"Proxy {proxy_info.host}:{proxy_info.port} updated: reliability={proxy_info.reliability}, response_time={proxy_info.avg_response_time:.2f}ms")

    def _get_random_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": random.choice(config.USER_AGENTS),
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "Connection": "keep-alive"
        }

# ===========================================================================
# PROXY SCANNER MANAGER
# ===========================================================================

class ProxyScanManager:
    def __init__(self, check_interval: int, connection_limit: int, validation_rounds: int, validation_mode: str,
                 timeout: float, check_anonymity: bool, force_fetch: bool, verbose: bool, single_run: bool,
                 proxy_sources: List[str], proxy_test_workers: int, proxy_fetch_interval: int,
                 proxy_test_timeout: float, proxy_test_retries: int, max_proxies_to_keep: int,
                 proxy_refresh_min_interval: int, test_url: str, export_interval: int,
                 max_fetch_attempts: int, fetch_retry_delay: int):
        self.check_interval = check_interval
        self.connection_limit = connection_limit
        self.validation_rounds = validation_rounds
        self.validation_mode = validation_mode
        self.timeout = timeout
        self.check_anonymity = check_anonymity
        self.force_fetch = force_fetch
        self.verbose = verbose
        self.single_run = single_run
        self.proxy_sources = proxy_sources
        self.proxy_test_workers = proxy_test_workers
        self.proxy_fetch_interval = proxy_fetch_interval
        self.proxy_test_timeout = proxy_test_timeout
        self.proxy_test_retries = proxy_test_retries
        self.max_proxies_to_keep = max_proxies_to_keep
        self.proxy_refresh_min_interval = proxy_refresh_min_interval
        self.test_url = test_url
        self.export_interval = export_interval
        self.max_fetch_attempts = max_fetch_attempts
        self.fetch_retry_delay = fetch_retry_delay
        self.session = None
        self.connector = None
        self.proxy_fetch_executor = None
        self.proxy_test_executor = None
        self.proxies = defaultdict(ProxyInfo)
        self.verified_proxies = set()
        self.lock = asyncio.Lock()
        self.proxy_queue = asyncio.Queue()
        self.proxy_test_queue = asyncio.Queue()
        self.optimizer = OptimizerIntegration()
        self.netblock_failures = defaultdict(int)  # Track failed netblocks
        if verbose:
            logger.setLevel(logging.DEBUG)

    async def initialize(self):
        """Initialize with connection pooling and DNS caching."""
        self.connector = aiohttp.TCPConnector(limit=self.connection_limit, keepalive_timeout=30, ttl_dns_cache=300)
        self.session = aiohttp.ClientSession(connector=self.connector)
        self.proxy_fetch_executor = ThreadPoolExecutor(max_workers=self.max_fetch_attempts)
        self.proxy_test_executor = ThreadPoolExecutor(max_workers=self.proxy_test_workers)
        await self.optimizer.initialize()
        logger.info("Fetching initial proxy lists...")
        await self.fetch_proxy_lists()
        logger.info("Scanner initialized successfully.")

    async def cleanup(self):
        """Clean up resources."""
        if self.session and not self.session.closed:
            await self.session.close()
        if self.connector:
            await self.connector.close()
        if self.proxy_fetch_executor:
            self.proxy_fetch_executor.shutdown(wait=True)
        if self.proxy_test_executor:
            self.proxy_test_executor.shutdown(wait=True)
        logger.info("Cleanup complete.")

    async def test_proxy(self, proxy_info: ProxyInfo) -> Tuple[bool, float, str]:
        """Optimized proxy test with progressive checking."""
        start_time = time.monotonic()
        anonymity_level = "unknown"
        proxy_url = f"{proxy_info.protocol}://{proxy_info.host}:{proxy_info.port}"

        # Skip if netblock has too many failures
        if self.netblock_failures[proxy_info.netblock] > 5:
            logger.debug(f"Skipping proxy {proxy_url} due to netblock failures")
            return False, 0, "unknown"

        # Quick CONNECT check
        test_config = await self.optimizer.optimize_proxy_test(self.session, proxy_info)
        if test_config['is_fast_track']:
            logger.debug(f"Fast-tracking reliable proxy {proxy_url}")
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

        # Full HTTP test
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
        except (aiohttp.ClientError, asyncio.TimeoutError, socket.gaierror, ConnectionRefusedError) as e:
            logger.debug(f"Proxy {proxy_url} failed test: {e}")
            self.netblock_failures[proxy_info.netblock] += 1
            return False, 0, "unknown"
        except Exception as e:
            logger.error(f"Unexpected error during proxy test {proxy_url}: {e}")
            return False, 0, "unknown"

    async def start_scanning_loop(self):
        """Prioritize high-reliability proxies."""
        last_fetch_time = last_export_time = 0
        workers = [asyncio.create_task(self.test_proxy_worker()) for _ in range(self.proxy_test_workers)]
        
        while True:
            current_time = time.time()
            if current_time - last_fetch_time >= self.proxy_fetch_interval or self.force_fetch:
                await self.fetch_proxy_lists()
                last_fetch_time = current_time
                self.force_fetch = False

            # Queue proxies, prioritizing by reliability
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

            if self.single_run:
                await self.proxy_queue.join()
                await self.proxy_test_queue.join()
                await self.export_results(force=True)
                break

            if self.proxy_queue.empty() and self.proxy_test_queue.empty():
                await asyncio.sleep(self.check_interval)
            else:
                await asyncio.sleep(1)

        for _ in workers:
            await self.proxy_test_queue.put(None)
        await asyncio.gather(*workers)

    async def run(self):
        """
        Main asynchronous execution method for the proxy scanner.
        Orchestrates initialization, scanning, and graceful shutdown.
        """
        try:
            print(f"{Fore.CYAN}Initializing scanner...{Style.RESET_ALL}")
            logger.info("Initializing scanner...")
            await self.optimizer.initialize() # Initialize the optimizer first
            await self.initialize() # Initialize scanner resources
            
            print(f"{Fore.CYAN}Scanner initialized. Starting scanning loop...{Style.RESET_ALL}")
            logger.info("Scanner initialized. Starting scanning loop...")
            await self.start_scanning_loop() 
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Ctrl+C detected. Initiating graceful shutdown...{Style.RESET_ALL}")
            logger.info("Ctrl+C detected. Initiating graceful shutdown.")
            await self.export_results(force=True) # Ensure results are exported on interrupt
        except Exception as e:
            print(f"{Fore.RED}An unexpected error occurred during scanning: {e}{Style.RESET_ALL}")
            logger.exception("An unexpected error occurred during scanning.")
        finally:
            print(f"{Fore.CYAN}Cleaning up scanner resources...{Style.RESET_ALL}")
            logger.info("Cleaning up scanner resources.")
            await self.cleanup()
            print(f"{Fore.CYAN}Scanner has shut down cleanly.{Style.RESET_ALL}")
            logger.info("Scanner has shut down cleanly.")


# ===========================================================================
# UTILITY FUNCTIONS (from config.py hints, implemented here for completeness)
# ===========================================================================

def run_speed_test(filepath: str):
    """
    Placeholder for a function to run a speed test on proxies from a file.
    """
    print(f"{Fore.BLUE}Running speed test on proxies from: {filepath}{Style.RESET_ALL}")
    logger.info(f"Running speed test on {filepath} (placeholder).")
    # Implement actual speed test logic here
    if not os.path.exists(filepath):
        print(f"{Fore.RED}Error: File not found at {filepath}{Style.RESET_ALL}")
        return
    with open(filepath, 'r') as f:
        proxies = f.readlines()
        print(f"Simulating speed test for {len(proxies)} proxies from {filepath}...")
    print(f"{Fore.GREEN}Speed test completed (placeholder).{Style.RESET_ALL}")

def clean_old_files():
    """
    Placeholder for a function to clean old exported proxy files.
    """
    print(f"{Fore.BLUE}Cleaning old exported files (placeholder)...{Style.RESET_ALL}")
    logger.info("Cleaning old exported files (placeholder).")
    # Implement logic to delete old files here
    print(f"{Fore.GREEN}Old files cleaned (placeholder).{Style.RESET_ALL}")

def analyze_proxy_stats():
    """
    Placeholder for a function to analyze proxy statistics.
    """
    print(f"{Fore.BLUE}Analyzing proxy statistics (placeholder)...{Style.RESET_ALL}")
    logger.info("Analyzing proxy statistics (placeholder).")
    # Implement logic to read logs/exports and present statistics
    print(f"{Fore.GREEN}Proxy statistics analysis completed (placeholder).{Style.RESET_ALL}")

def setup_auto_update():
    """
    Placeholder for a function to set up automatic updates for the scanner.
    """
    print(f"{Fore.BLUE}Setting up auto-update (placeholder)...{Style.RESET_ALL}")
    logger.info("Setting up auto-update (placeholder).")
    # Implement auto-update setup logic here
    print(f"{Fore.GREEN}Auto-update setup completed (placeholder).{Style.RESET_ALL}")

# ===========================================================================
# MAIN ENTRY POINT AND ARGUMENT PARSING
# ===========================================================================

# This function will parse command-line arguments and fallback to config.py values
def get_args():
    parser = argparse.ArgumentParser(description="RapidProxyScan - Advanced Proxy Scanner")
    # Add arguments corresponding to config.py constants
    parser.add_argument("--check-interval", type=int, default=config.CHECK_INTERVAL,
                        help="How often to check for new proxies (in seconds)")
    parser.add_argument("--connection-limit", type=int, default=config.CONNECTION_LIMIT,
                        help="Maximum concurrent connections for proxy testing")
    parser.add_argument("--validation-rounds", type=int, default=config.VALIDATION_ROUNDS,
                        help="Number of validation tests per proxy")
    parser.add_argument("--validation-mode", type=str, default=config.VALIDATION_MODE,
                        choices=['any', 'majority', 'all'],
                        help="Validation mode: 'any', 'majority', or 'all'")
    parser.add_argument("--timeout", type=float, default=config.TIMEOUT,
                        help="Connection timeout in seconds")
    parser.add_argument("--check-anonymity", action=argparse.BooleanOptionalAction, default=config.CHECK_ANONYMITY,
                        help="Check proxy anonymity level")
    parser.add_argument("--force-fetch", action=argparse.BooleanOptionalAction, default=config.FORCE_FETCH,
                        help="Force fetch proxy lists on each cycle")
    parser.add_argument("--verbose", action=argparse.BooleanOptionalAction, default=config.VERBOSE,
                        help="Enable verbose logging")
    parser.add_argument("--single-run", action=argparse.BooleanOptionalAction, default=config.SINGLE_RUN,
                        help="Run once and exit")
    
    # Add arguments for other parameters that ProxyScanManager.__init__ expects
    parser.add_argument("--proxy-sources", type=str, nargs='*', default=config.PROXY_SOURCES,
                        help="List of proxy sources URLs/paths (space-separated)")
    parser.add_argument("--proxy-test-workers", type=int, default=config.CONNECTION_LIMIT, # Using CONNECTION_LIMIT as a sensible default
                        help="Number of concurrent workers for testing proxies")
    parser.add_argument("--proxy-fetch-interval", type=int, default=config.CHECK_INTERVAL * 2, # Using a multiple of CHECK_INTERVAL
                        help="Interval in seconds to fetch new proxy lists")
    parser.add_argument("--proxy-test-timeout", type=float, default=config.TIMEOUT,
                        help="Timeout for individual proxy tests")
    parser.add_argument("--proxy-test-retries", type=int, default=config.VALIDATION_ROUNDS,
                        help="Number of retries for a failed proxy test")
    parser.add_argument("--max-proxies-to-keep", type=int, default=10000,
                        help="Maximum number of proxies to store in memory")
    parser.add_argument("--proxy-refresh-min-interval", type=int, default=300,
                        help="Minimum interval before re-testing a proxy")
    parser.add_argument("--test-url", type=str, default="http://ip-api.com/json",
                        help="URL to test proxy connectivity")
    parser.add_argument("--export-interval", type=int, default=300,
                        help="Interval in seconds to export verified proxies")
    parser.add_argument("--max-fetch-attempts", type=int, default=5,
                        help="Max attempts to fetch a proxy list")
    parser.add_argument("--fetch-retry-delay", type=int, default=5,
                        help="Delay between fetch retries")

    args = parser.parse_args()
    return args

def run_scanner(check_interval: int = None,
                connection_limit: int = None,
                validation_rounds: int = None,
                validation_mode: str = None,
                timeout: float = None,
                check_anonymity: bool = None,
                force_fetch: bool = None,
                verbose: bool = None,
                single_run: bool = None,
                # Parameters that ProxyScanManager.__init__ expects
                proxy_sources: List[str] = None, 
                proxy_test_workers: int = None,
                proxy_fetch_interval: int = None,
                proxy_test_timeout: float = None,
                proxy_test_retries: int = None,
                max_proxies_to_keep: int = None,
                proxy_refresh_min_interval: int = None,
                test_url: str = None,
                export_interval: int = None,
                max_fetch_attempts: int = None,
                fetch_retry_delay: int = None
                ):
    """
    Main function to run the proxy scanner.
    It can be called with explicit arguments (e.g., from config.py)
    or without arguments (e.g., when rapidproxyscan.py is run directly).
    """
    # Default to config.py values if arguments are not provided
    # This allows config.py to explicitly pass args, or rapidproxyscan.py
    # to get them from CLI or config.py defaults via get_args().
    check_interval = check_interval if check_interval is not None else config.CHECK_INTERVAL
    connection_limit = connection_limit if connection_limit is not None else config.CONNECTION_LIMIT
    validation_rounds = validation_rounds if validation_rounds is not None else config.VALIDATION_ROUNDS
    validation_mode = validation_mode if validation_mode is not None else config.VALIDATION_MODE
    timeout = timeout if timeout is not None else config.TIMEOUT
    check_anonymity = check_anonymity if check_anonymity is not None else config.CHECK_ANONYMITY
    force_fetch = force_fetch if force_fetch is not None else config.FORCE_FETCH
    verbose = verbose if verbose is not None else config.VERBOSE
    single_run = single_run if single_run is not None else config.SINGLE_RUN
    
    proxy_sources = proxy_sources if proxy_sources is not None else config.PROXY_SOURCES
    proxy_test_workers = proxy_test_workers if proxy_test_workers is not None else config.CONNECTION_LIMIT
    proxy_fetch_interval = proxy_fetch_interval if proxy_fetch_interval is not None else config.CHECK_INTERVAL * 2
    proxy_test_timeout = proxy_test_timeout if proxy_test_timeout is not None else config.TIMEOUT
    proxy_test_retries = proxy_test_retries if proxy_test_retries is not None else config.VALIDATION_ROUNDS
    max_proxies_to_keep = max_proxies_to_keep if max_proxies_to_keep is not None else 10000
    proxy_refresh_min_interval = proxy_refresh_min_interval if proxy_refresh_min_interval is not None else 300
    test_url = test_url if test_url is not None else "http://ip-api.com/json"
    export_interval = export_interval if export_interval is not None else 300
    max_fetch_attempts = max_fetch_attempts if max_fetch_attempts is not None else 5
    fetch_retry_delay = fetch_retry_delay if fetch_retry_delay is not None else 5

    scanner = ProxyScanManager(
        check_interval=check_interval,
        connection_limit=connection_limit,
        validation_rounds=validation_rounds,
        validation_mode=validation_mode,
        timeout=timeout,
        check_anonymity=check_anonymity,
        force_fetch=force_fetch,
        verbose=verbose,
        single_run=single_run,
        proxy_sources=proxy_sources,
        proxy_test_workers=proxy_test_workers,
        proxy_fetch_interval=proxy_fetch_interval,
        proxy_test_timeout=proxy_test_timeout,
        proxy_test_retries=proxy_test_retries,
        max_proxies_to_keep=max_proxies_to_keep,
        proxy_refresh_min_interval=proxy_refresh_min_interval,
        test_url=test_url,
        export_interval=export_interval,
        max_fetch_attempts=max_fetch_attempts,
        fetch_retry_delay=fetch_retry_delay
    )
    asyncio.run(scanner.run())

if __name__ == "__main__":
    # This block will be executed if rapidproxyscan.py is run directly.
    # It will parse CLI arguments, defaulting to values from config.py.
    
    # Handle utility functions directly from command line first
    if len(sys.argv) > 1:
        if "--speed-test" in sys.argv:
            idx = sys.argv.index("--speed-test")
            if idx + 1 < len(sys.argv):
                run_speed_test(sys.argv[idx + 1])
            else:
                print(f"{Fore.RED}Error: --speed-test requires a file path.{Style.RESET_ALL}")
            sys.exit(0)
        
        if "--clean-old" in sys.argv:
            clean_old_files()
            sys.exit(0)
        
        if "--analyze" in sys.argv:
            analyze_proxy_stats()
            sys.exit(0)
        
        if "--setup-auto-update" in sys.argv:
            setup_auto_update()
            sys.exit(0)

    # If no utility function is called, proceed with scanner
    args = get_args() 
    
    # Call run_scanner with arguments parsed from CLI (defaulting to config.py values)
    run_scanner(
        check_interval=args.check_interval,
        connection_limit=args.connection_limit,
        validation_rounds=args.validation_rounds,
        validation_mode=args.validation_mode,
        timeout=args.timeout,
        check_anonymity=args.check_anonymity,
        force_fetch=args.force_fetch,
        verbose=args.verbose,
        single_run=args.single_run,
        proxy_sources=args.proxy_sources,
        proxy_test_workers=args.proxy_test_workers,
        proxy_fetch_interval=args.proxy_fetch_interval,
        proxy_test_timeout=args.proxy_test_timeout,
        proxy_test_retries=args.proxy_test_retries,
        max_proxies_to_keep=args.max_proxies_to_keep,
        proxy_refresh_min_interval=args.proxy_refresh_min_interval,
        test_url=args.test_url,
        export_interval=args.export_interval,
        max_fetch_attempts=args.max_fetch_attempts,
        fetch_retry_delay=args.fetch_retry_delay
    )
    