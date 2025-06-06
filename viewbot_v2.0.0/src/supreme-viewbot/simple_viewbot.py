"""
Simple ViewBot - Medium View Booster
Optimized for stability and higher success rate
"""

import os
import random
import time
import asyncio
import aiohttp
import logging
import requests
from urllib.parse import urlparse

# Simplified configuration
TARGET_URL = "https://medium.com/@cgpt/is-vibe-coding-cheating-or-the-future-of-programming-in-the-workplace-216fe9d5084d"
NUM_REQUESTS = 100
DELAY_MIN = 5  # seconds
DELAY_MAX = 15  # seconds
LOG_FILE = "simple_viewbot.log"

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

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

# User agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.113 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Samsung Galaxy S24 Ultra) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.99 Mobile Safari/537.36"
]

# Referrers
REFERRERS = [
    "https://www.google.com/search?q=future+of+programming",
    "https://www.google.com/search?q=vibe+coding+cheating",
    "https://twitter.com/search?q=vibe%20coding",
    "https://www.reddit.com/r/programming/",
    "https://news.ycombinator.com/",
    "https://www.linkedin.com/feed/",
    "https://medium.com/tag/programming",
    None  # Sometimes no referrer
]

# Test proxy function
def test_proxy(proxy_url, timeout=5):
    try:
        proxies = {
            "http": proxy_url,
            "https": proxy_url
        }
        headers = {
            "User-Agent": random.choice(USER_AGENTS)
        }
        response = requests.get(
            "https://www.google.com", 
            proxies=proxies, 
            headers=headers, 
            timeout=timeout,
            verify=False  # Disable SSL verification
        )
        return response.status_code == 200
    except:
        return False

# Validate proxies before using them
def validate_proxies(proxies, max_workers=10):
    valid_proxies = []
    logging.info(f"Validating {len(proxies)} proxies...")
    
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(test_proxy, proxies))
        
    valid_proxies = [proxy for proxy, is_valid in zip(proxies, results) if is_valid]
    logging.info(f"Found {len(valid_proxies)} working proxies out of {len(proxies)}")
    return valid_proxies

# Random delay function with jitter
def random_delay():
    base_delay = random.uniform(DELAY_MIN, DELAY_MAX)
    jitter = random.uniform(-1, 1)  # Add ±1