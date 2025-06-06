#!/usr/bin/env python3
"""
Ultra Simple ViewBot - Medium View Generator
Minimalistic version with no dependencies except requests
"""

import os
import random
import time
import logging
import requests
import base64
import threading
from concurrent.futures import ThreadPoolExecutor

# Basic Configuration
TARGET_URL = "https://medium.com/@cgpt/is-vibe-coding-cheating-or-the-future-of-programming-in-the-workplace-216fe9d5084d"
NUM_REQUESTS = 50  # Total number of requests to send
MAX_WORKERS = 5    # Maximum concurrent requests
DELAY_MIN = 3      # Minimum delay between requests (seconds)
DELAY_MAX = 8      # Maximum delay between requests (seconds)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename="viewbot_simple.log",
    filemode="a"
)

# Also print to console
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

# User agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.113 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.102 Safari/537.36"
]

# Referrers
REFERRERS = [
    "https://www.google.com/search?q=future+of+programming",
    "https://twitter.com/search?q=vibe%20coding",
    "https://www.reddit.com/r/programming/",
    "https://news.ycombinator.com/",
    None  # Sometimes no referrer
]

# Load proxies
def load_proxies(proxy_file="proxies.txt"):
    proxies = []
    try:
        with open(proxy_file, "r") as f:
            for line in f:
                proxy = line.strip()
                if proxy:
                    proxies.append(proxy)
        logging.info(f"Loaded {len(proxies)} proxies from {proxy_file}")
        return proxies
    except Exception as e:
        logging.error(f"Error loading proxies: {e}")
        return []

# Generate random cookies
def generate_random_cookies():
    return {
        "sid": f"1:{random.randint(1000000000, 9999999999)}",
        "_ga": f"GA1.2.{random.randint(1000000000, 9999999999)}.{int(time.time()-random.randint(1000000, 9999999))}",
        "_gid": f"GA1.2.{random.randint(1000000000, 9999999999)}.{int(time.time())}",
        "xsrf": base64.b64encode(os.urandom(16)).decode('utf-8'),
    }

# Send a single view request
def send_view_request(url, proxy=None):
    # Generate random user agent and referrer
    user_agent = random.choice(USER_AGENTS)
    referrer = random.choice(REFERRERS)
    
    # Prepare headers
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    # Add referrer if selected
    if referrer:
        headers["Referer"] = referrer
    
    # Random cookies
    cookies = generate_random_cookies()
    
    # Configure proxy
    proxies = None
    if proxy:
        proxies = {
            "http": proxy,
            "https": proxy
        }
    
    try:
        # Send the request with a timeout
        response = requests.get(
            url, 
            headers=headers, 
            cookies=cookies, 
            proxies=proxies, 
            timeout=10,
            verify=False  # Disable SSL verification
        )
        
        # Log result
        if response.status_code == 200:
            logging.info(f"✅ Success: status={response.status_code}, proxy={proxy}")
            return True
        else:
            logging.warning(f"❌ Failed: status={response.status_code}, proxy={proxy}")
            return False
            
    except Exception as e:
        error_msg = str(e)
        logging.error(f"❌ Error: {error_msg[:100]}..., proxy={proxy}")
        return False

# Worker function
def worker(url, proxy=None):
    try:
        result = send_view_request(url, proxy)
        # Random delay between requests
        time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
        return result
    except Exception as e:
        logging.error(f"Worker error: {e}")
        return False

# Main function
def main():
    print("\n" + "="*60)
    print("🚀 Ultra Simple Medium ViewBot")
    print("="*60 + "\n")
    
    # Disable SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Load proxies
    proxies = load_proxies()
    
    # If no proxies found, use direct connection
    if not proxies:
        logging.warning("No proxies found, will use direct connection")
        proxies = [None] * NUM_REQUESTS
    
    # Reuse proxies if we have fewer than requests
    if len(proxies) < NUM_REQUESTS:
        from itertools import cycle
        proxy_cycle = cycle(proxies)
        proxies = [next(proxy_cycle) for _ in range(NUM_REQUESTS)]
    
    # Shuffle proxies
    random.shuffle(proxies)
    
    logging.info(f"Starting view bot targeting: {TARGET_URL}")
    logging.info(f"Sending {NUM_REQUESTS} requests with {MAX_WORKERS} concurrent workers")
    
    # Record start time
    start_time = time.time()
    
    # Success counter
    success_count = 0
    failed_count = 0
    
    # Use thread pool for concurrent requests
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for i in range(NUM_REQUESTS):
            proxy = proxies[i] if i < len(proxies) else None
            future = executor.submit(worker, TARGET_URL, proxy)
            futures.append(future)
            
        # Process results as they complete
        for i, future in enumerate(futures):
            try:
                result = future.result()
                if result:
                    success_count += 1
                else:
                    failed_count += 1
                    
                # Print progress
                if (i + 1) % 5 == 0 or (i + 1) == NUM_REQUESTS:
                    print(f"Progress: {i+1}/{NUM_REQUESTS} requests completed")
                    
            except Exception as e:
                logging.error(f"Error getting result: {e}")
                failed_count += 1
    
    # Calculate runtime
    runtime = time.time() - start_time
    
    # Print results
    print("\n" + "="*60)
    print(f"✅ Successful requests: {success_count}")
    print(f"❌ Failed requests: {failed_count}")
    print(f"⏱️ Total runtime: {runtime:.2f} seconds")
    print(f"🚀 Success rate: {(success_count / NUM_REQUESTS) * 100:.2f}%")
    print(f"⚡ Requests per minute: {(success_count + failed_count) / (runtime / 60):.2f}")
    print("="*60 + "\n")
    
    logging.info(f"ViewBot completed. Success: {success_count}, Failed: {failed_count}, Runtime: {runtime:.2f}s")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ ViewBot stopped by user")
    except Exception as e:
        print(f"\n⚠️ Error: {e}")