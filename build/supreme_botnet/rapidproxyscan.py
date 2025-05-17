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
import sys # Added for sys.exit in utilities
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from colorama import Fore, Style, init
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Tuple, Set, Optional, Union, Any
from collections import defaultdict

# Import your config.py file to access the global constants
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

# ===========================================================================
# PROXY RELATED CLASSES
# ===========================================================================

class ProxyInfo:
    """
    Represents detailed information about a single proxy.
    """
    def __init__(self, host: str, port: int, protocol: str = "http", country: str = "Unknown",
                 avg_response_time: float = 0, reliability: float = 0, anonymity: str = "unknown"):
        self.host = host
        self.port = port
        self.protocol = protocol
        self.country = country
        self.avg_response_time = avg_response_time
        self.reliability = reliability
        self.anonymity = anonymity
        self.last_tested = 0 # Timestamp of last test

    def to_dict(self) -> Dict[str, Any]:
        """Converts proxy information to a dictionary."""
        return {
            "host": self.host,
            "port": self.port,
            "protocol": self.protocol,
            "country": self.country,
            "avg_response_time": self.avg_response_time,
            "reliability": self.reliability,
            "anonymity": self.anonymity,
            "last_tested": self.last_tested
        }
    
    def __repr__(self) -> str:
        """String representation of the ProxyInfo object."""
        return f"ProxyInfo({self.host}:{self.port} [{self.protocol}])"

    def __hash__(self) -> int:
        """Enables hashing for use in sets/dictionaries."""
        return hash((self.host, self.port, self.protocol))

    def __eq__(self, other: Any) -> bool:
        """Enables equality comparison."""
        if not isinstance(other, type(self)): return NotImplemented
        return self.host == other.host and self.port == other.port and self.protocol == other.protocol

# ===========================================================================
# OPTIMIZER INTEGRATION (Placeholder for your advanced logic)
# ===========================================================================

class OptimizerIntegration:
    """
    Placeholder for the advanced optimization logic of RapidProxyScan.
    This class would implement custom endpoint creation, CDN selection,
    DNS pre-resolution, header compression, binary protocols, etc.
    """
    def __init__(self):
        logger.debug("OptimizerIntegration initialized.")

    async def initialize(self):
        """Initializes any resources required by the optimizer."""
        logger.info("Optimizer: Initializing...")
        await asyncio.sleep(0.1) # Simulate async initialization
        logger.info("Optimizer: Initialization complete.")

    async def optimize_proxy_test(self, session: aiohttp.ClientSession, proxy_info: ProxyInfo) -> Dict[str, Any]:
        """
        Determines optimal test configuration for a given proxy.
        Returns a dictionary with 'url', 'headers', 'is_fast_track', 'use_binary_protocol'.
        """
        optimized_url = proxy_info.test_url # Default to the proxy's test URL
        headers = self._get_random_headers() # Use internal method for headers

        # Example optimization logic (to be replaced by actual implementation)
        is_fast_track = random.choice([True, False])
        use_binary_protocol = random.choice([True, False])

        logger.debug(f"Optimizer: Optimizing test for {proxy_info.host}:{proxy_info.port}")
        return {
            'url': optimized_url,
            'headers': headers,
            'is_fast_track': is_fast_track,
            'use_binary_protocol': use_binary_protocol
        }

    async def post_test_processing(self, proxy_info: ProxyInfo, success: bool, response_time: float, endpoint: str):
        """
        Processes the results after a proxy test.
        Updates proxy_info's reliability, avg_response_time etc.
        """
        logger.debug(f"Optimizer: Post-test processing for {proxy_info.host}:{proxy_info.port}")
        # Update proxy_info based on test results
        if success:
            proxy_info.reliability = min(100, proxy_info.reliability + 5)
            proxy_info.avg_response_time = (proxy_info.avg_response_time + response_time) / 2 if proxy_info.avg_response_time else response_time
        else:
            proxy_info.reliability = max(0, proxy_info.reliability - 10)
        proxy_info.last_tested = time.time()
        
        # Example: Log the outcome or trigger further actions
        if success:
            logger.info(f"Optimizer: Proxy {proxy_info.host}:{proxy_info.port} passed test ({response_time:.2f}ms).")
        else:
            logger.warning(f"Optimizer: Proxy {proxy_info.host}:{proxy_info.port} failed test.")

    async def export_specialized_formats(self, proxies_to_export: List[ProxyInfo]) -> List[str]:
        """
        Exports verified proxies in specialized formats for viewbot/Supreme environments.
        Returns a list of paths to the exported files.
        """
        logger.info("Optimizer: Exporting specialized formats (placeholder)...")
        # Placeholder: Actual implementation would generate specific file formats.
        # For now, just print a message.
        if proxies_to_export:
            logger.info(f"Optimizer: Would export {len(proxies_to_export)} proxies to specialized formats.")
        return []

    def _get_random_headers(self) -> Dict[str, str]:
        """Helper to get random headers for optimization."""
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0"
        }

# ===========================================================================
# PROXY SCANNER MANAGER
# ===========================================================================

class ProxyScanManager:
    """Main proxy scan manager class for RapidProxyScan."""
    def __init__(self, 
                 check_interval: int,
                 connection_limit: int,
                 validation_rounds: int,
                 validation_mode: str,
                 timeout: float,
                 check_anonymity: bool,
                 force_fetch: bool,
                 verbose: bool,
                 single_run: bool,
                 # Parameters sourced from config.py's global constants
                 proxy_sources: List[str], 
                 proxy_test_workers: int,
                 proxy_fetch_interval: int,
                 proxy_test_timeout: float,
                 proxy_test_retries: int,
                 max_proxies_to_keep: int,
                 proxy_refresh_min_interval: int,
                 test_url: str,
                 export_interval: int,
                 max_fetch_attempts: int,
                 fetch_retry_delay: int
                ):
        # Assign all passed configuration parameters as instance attributes
        self.check_interval = check_interval
        self.connection_limit = connection_limit
        self.validation_rounds = validation_rounds
        self.validation_mode = validation_mode
        self.timeout = timeout
        self.check_anonymity = check_anonymity
        self.force_fetch = force_fetch
        self.single_run = single_run # 'args' object is no longer passed directly to __init__
        
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

        # Initialize other dynamic attributes to None or empty before use
        self.session: Optional[aiohttp.ClientSession] = None
        self.proxy_fetch_executor: Optional[ThreadPoolExecutor] = None
        self.proxy_test_executor: Optional[ThreadPoolExecutor] = None
        self.proxies: Dict[str, ProxyInfo] = defaultdict(ProxyInfo)
        self.verified_proxies: Set[str] = set()
        self.lock: asyncio.Lock = asyncio.Lock()
        self.proxy_queue: asyncio.Queue = asyncio.Queue()
        self.proxy_test_queue: asyncio.Queue = asyncio.Queue()
        self.optimizer: OptimizerIntegration = OptimizerIntegration()
        
        # Set logging level based on verbose flag
        if verbose: # Use the passed verbose argument directly
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

    def _get_random_headers(self) -> Dict[str, str]:
        """
        Generates a dictionary of random HTTP headers, including a User-Agent.
        """
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1", # Do Not Track Request Header
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0"
        }

    async def initialize(self):
        """
        Initializes the scanner's resources, including aiohttp session,
        thread pools, and fetches initial proxy lists.
        """
        self.session = aiohttp.ClientSession() # Create a new aiohttp ClientSession
        # Create thread pools for fetching and testing proxies, using configured workers
        self.proxy_fetch_executor = ThreadPoolExecutor(max_workers=self.max_fetch_attempts) 
        self.proxy_test_executor = ThreadPoolExecutor(max_workers=self.proxy_test_workers)
        
        print(f"{Fore.CYAN}Fetching initial proxy lists...{Style.RESET_ALL}")
        logger.info("Fetching initial proxy lists...")
        await self.fetch_proxy_lists()

        print(f"{Fore.GREEN}Scanner initialized successfully.{Style.RESET_ALL}")
        logger.info("Scanner initialized successfully.")

    async def cleanup(self):
        """
        Cleans up scanner resources by closing the aiohttp session
        and shutting down thread pools.
        """
        print(f"{Fore.CYAN}Initiating cleanup...{Style.RESET_ALL}")
        logger.info("Initiating cleanup...")

        # Close the aiohttp session if it exists and is not already closed
        if self.session and not self.session.closed:
            await self.session.close()
            print(f"{Fore.GREEN}aiohttp session closed.{Style.RESET_ALL}")
            logger.info("aiohttp session closed.")

        # Shutdown the proxy fetch thread pool if it exists
        if hasattr(self, 'proxy_fetch_executor') and self.proxy_fetch_executor:
            self.proxy_fetch_executor.shutdown(wait=True) # Wait for current tasks to complete
            print(f"{Fore.GREEN}Proxy fetch executor shut down.{Style.RESET_ALL}")
            logger.info("Proxy fetch executor shut down.")

        # Shutdown the proxy test thread pool if it exists
        if hasattr(self, 'proxy_test_executor') and self.proxy_test_executor:
            self.proxy_test_executor.shutdown(wait=True) # Wait for current tasks to complete
            print(f"{Fore.GREEN}Proxy test executor shut down.{Style.RESET_ALL}")
            logger.info("Proxy test executor shut down.")
        
        print(f"{Fore.GREEN}Cleanup complete.{Style.RESET_ALL}")
        logger.info("Cleanup complete.")
    
    async def export_results(self, force: bool = False, output_dir: str = "exported_proxies", filename_prefix: str = "proxies"):
        """
        Exports the verified proxies to text and CSV files.
        Verified proxies are stored in self.verified_proxies (set of "host:port" strings).
        Detailed proxy information is retrieved from self.proxies (dict of {address: ProxyInfo}).

        Args:
            force (bool): If True, forces export even if no new proxies are found (e.g., on program exit).
            output_dir (str): Directory to save the exported files.
            filename_prefix (str): Prefix for the output filenames.
        """
        if not self.verified_proxies and not force:
            print(f"{Fore.YELLOW}No new verified proxies to export. Skipping export.{Style.RESET_ALL}")
            logger.info("No new verified proxies to export.")
            return

        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        txt_filename = os.path.join(output_dir, f"{filename_prefix}_{timestamp}.txt")
        csv_filename = os.path.join(output_dir, f"{filename_prefix}_{timestamp}.csv")

        exported_count = 0
        try:
            with open(txt_filename, 'w') as f_txt:
                for proxy_address in sorted(list(self.verified_proxies)):
                    f_txt.write(f"{proxy_address}\n")
                    exported_count += 1
            print(f"{Fore.GREEN}Exported {exported_count} verified proxies to {txt_filename}{Style.RESET_ALL}")
            logger.info(f"Exported {exported_count} verified proxies to {txt_filename}")

            if self.verified_proxies:
                proxies_to_export_info = [self.proxies[addr] for addr in self.verified_proxies if addr in self.proxies]
                
                if proxies_to_export_info:
                    csv_headers = list(proxies_to_export_info[0].to_dict().keys())
                    
                    with open(csv_filename, 'w', newline='') as f_csv:
                        writer = csv.DictWriter(f_csv, fieldnames=csv_headers)
                        writer.writeheader()
                        for proxy_info in proxies_to_export_info:
                            writer.writerow(proxy_info.to_dict())
                    print(f"{Fore.GREEN}Exported detailed proxy info to {csv_filename}{Style.RESET_ALL}")
                    logger.info(f"Exported detailed proxy info to {csv_filename}")

        except IOError as e:
            print(f"{Fore.RED}Error exporting proxies: {e}{Style.RESET_ALL}")
            logger.error(f"Error exporting proxies: {e}")
        except Exception as e:
            print(f"{Fore.RED}An unexpected error occurred during export: {e}{Style.RESET_ALL}")
            logger.error(f"An unexpected error occurred during proxy export: {e}")

    async def fetch_proxy_lists(self):
        """
        Fetches proxy lists from configured sources.
        """
        logger.info(f"Attempting to fetch proxy lists from {len(self.proxy_sources)} sources.")
        fetched_proxies_count = 0
        for source_url in self.proxy_sources:
            print(f"{Fore.YELLOW}Fetching from: {source_url}{Style.RESET_ALL}")
            try:
                async with self.session.get(source_url, timeout=self.timeout) as response:
                    response.raise_for_status() # Raise an exception for HTTP errors
                    content = await response.text()
                    new_proxies = self.parse_proxy_list(content, source_url)
                    for host, port in new_proxies:
                        proxy_address = f"{host}:{port}"
                        if proxy_address not in self.proxies:
                            self.proxies[proxy_address] = ProxyInfo(host, port)
                            await self.proxy_queue.put(self.proxies[proxy_address])
                            fetched_proxies_count += 1
                logger.info(f"Fetched {len(new_proxies)} proxies from {source_url}.")
            except aiohttp.ClientError as e:
                logger.error(f"Failed to fetch from {source_url}: {e}")
            except Exception as e:
                logger.error(f"An error occurred while processing {source_url}: {e}")
        print(f"{Fore.CYAN}Total new proxies added to queue: {fetched_proxies_count}{Style.RESET_ALL}")
        logger.info(f"Total new proxies added to queue: {fetched_proxies_count}")

    def parse_proxy_list(self, content: str, source_url: str) -> List[Tuple[str, int]]:
        """
        Parses content from a proxy list URL.
        Currently supports plain text (host:port) and basic HTML parsing.
        """
        proxies = []
        # Attempt to parse as plain text (one proxy per line)
        lines = content.splitlines()
        for line in lines:
            match = re.match(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)', line.strip())
            if match:
                try:
                    host = match.group(1)
                    port = int(match.group(2))
                    proxies.append((host, port))
                except ValueError:
                    logger.debug(f"Skipping invalid proxy format: {line}")
            else:
                # Attempt basic HTML parsing for common table structures
                soup = BeautifulSoup(content, 'html.parser')
                for td in soup.find_all('td'):
                    text = td.get_text(strip=True)
                    match = re.match(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)', text)
                    if match:
                        try:
                            host = match.group(1)
                            port = int(match.group(2))
                            if (host, port) not in proxies: # Avoid duplicates from HTML
                                proxies.append((host, port))
                        except ValueError:
                            pass # Ignore if port is not an int
        return proxies

    async def test_proxy_worker(self):
        """Worker function to test proxies from the queue."""
        while True:
            proxy_info = await self.proxy_test_queue.get()
            if proxy_info is None: # Sentinel value to stop worker
                break
            
            try:
                success, response_time, anonymity = await self.test_proxy(proxy_info)
                if success:
                    if self.check_anonymity:
                        proxy_info.anonymity = anonymity
                    async with self.lock:
                        self.verified_proxies.add(f"{proxy_info.host}:{proxy_info.port}")
                        logger.info(f"{Fore.GREEN}Verified: {proxy_info.host}:{proxy_info.port} ({response_time:.2f}ms, Anonymity: {proxy_info.anonymity}){Style.RESET_ALL}")
                
                await self.optimizer.post_test_processing(proxy_info, success, response_time, self.test_url) # Pass the endpoint

            except Exception as e:
                logger.error(f"Error testing proxy {proxy_info.host}:{proxy_info.port}: {e}")
            finally:
                self.proxy_test_queue.task_done()

    async def test_proxy(self, proxy_info: ProxyInfo) -> Tuple[bool, float, str]:
        """
        Tests a single proxy for connectivity and response time.
        Returns (success, response_time, anonymity_level).
        """
        start_time = time.monotonic()
        anonymity_level = "unknown" # Default
        proxy_url = f"{proxy_info.protocol}://{proxy_info.host}:{proxy_info.port}"
        
        # Use optimizer for test configuration
        test_config = await self.optimizer.optimize_proxy_test(self.session, proxy_info)

        try:
            async with self.session.get(
                test_config['url'],
                proxy=proxy_url,
                headers=test_config['headers'],
                timeout=self.proxy_test_timeout,
                allow_redirects=True
            ) as response:
                response.raise_for_status() # Raise exception for bad status codes
                response_time = (time.monotonic() - start_time) * 1000 # in ms
                
                # Check anonymity if enabled
                if self.check_anonymity:
                    anonymity_level = await self.check_proxy_anonymity(proxy_info, response)
                
                return True, response_time, anonymity_level
        except (aiohttp.ClientError, asyncio.TimeoutError, socket.gaierror, ConnectionRefusedError) as e:
            logger.debug(f"Proxy {proxy_url} failed test: {e}")
            return False, 0, "unknown"
        except Exception as e:
            logger.error(f"Unexpected error during proxy test {proxy_url}: {e}")
            return False, 0, "unknown"

    async def check_proxy_anonymity(self, proxy_info: ProxyInfo, response: aiohttp.ClientResponse) -> str:
        """
        Checks the anonymity level of a proxy based on response headers.
        (Highly dependent on the test URL's response and common proxy headers)
        """
        # This is a simplified placeholder. Real anonymity checks are complex.
        # A more robust check would involve making requests to specific "what's my IP" services
        # and checking for headers like X-Forwarded-For, Via, Proxy-Connection.
        headers = response.headers
        ip_data = {}
        try:
            # Assuming the test_url returns JSON with IP info (like ip-api.com/json)
            ip_data = await response.json()
        except (aiohttp.ContentTypeError, json.JSONDecodeError):
            logger.debug(f"Could not decode JSON for anonymity check for {proxy_info.host}:{proxy_info.port}")

        client_ip = ip_data.get('query') # Assuming this field in ip-api.com
        
        # If our real IP is exposed in X-Forwarded-For or Via headers, it's not anonymous
        # This requires getting the actual client's IP *before* using the proxy
        # For simplicity, we will check if common proxy headers are present.
        if 'X-Forwarded-For' in headers or 'Via' in headers or 'Proxy-Connection' in headers:
            return "transparent"
        
        if client_ip and client_ip != proxy_info.host:
            return "anonymous" # Proxy IP seen, but no revealing headers
        
        # If the proxy IP is the only one seen, it's highly anonymous
        if client_ip == proxy_info.host:
            return "elite"
            
        return "unknown" # Cannot determine

    async def start_scanning_loop(self):
        """
        Manages the main proxy scanning loop.
        """
        last_fetch_time = 0
        last_export_time = 0
        
        # Start proxy test workers
        workers = [asyncio.create_task(self.test_proxy_worker()) for _ in range(self.proxy_test_workers)]
        
        while True:
            current_time = time.time()

            # Fetch new proxies periodically
            if current_time - last_fetch_time >= self.proxy_fetch_interval or self.force_fetch:
                await self.fetch_proxy_lists()
                last_fetch_time = current_time
                self.force_fetch = False # Reset force_fetch after fetching

            # Queue proxies for testing (those not tested recently)
            async with self.lock:
                for addr, proxy_info in list(self.proxies.items()):
                    if current_time - proxy_info.last_tested >= self.proxy_refresh_min_interval:
                        await self.proxy_test_queue.put(proxy_info)
                        proxy_info.last_tested = current_time # Mark as queued for test

            # Perform exports periodically
            if current_time - last_export_time >= self.export_interval and self.verified_proxies:
                await self.export_results()
                last_export_time = current_time
                self.verified_proxies.clear() # Clear after export if desired

            # If single_run mode, break after one cycle (after initial fetch/test)
            if self.single_run:
                await self.proxy_queue.join() # Wait for any pending fetches
                await self.proxy_test_queue.join() # Wait for all tests to complete
                await self.export_results(force=True) # Final export
                break

            # If there are no proxies to test and not in single_run mode, wait for a bit
            if self.proxy_queue.empty() and self.proxy_test_queue.empty():
                print(f"{Fore.MAGENTA}No proxies in queue. Waiting for {self.check_interval} seconds...{Style.RESET_ALL}")
                await asyncio.sleep(self.check_interval)
            else:
                # Briefly sleep to allow other tasks to run
                await asyncio.sleep(1)
        
        # Send sentinel values to stop workers
        for _ in workers:
            await self.proxy_test_queue.put(None)
        await asyncio.gather(*workers) # Wait for workers to finish processing sentinels

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