import os
import threading
import random
import time
import logging
import requests
from stem import Signal
from stem.control import Controller
import aiohttp
import asyncio

class ProxyPool:
    """
    Advanced proxy management system with weighted rotation, health tracking,
    and automatic validation.
    """
    
    def __init__(self, proxy_file=None, max_failures=3, config=None):
        self.proxies = []
        self.max_failures = max_failures
        self.lock = threading.Lock()
        self.config = config or {}
        
        # Try to load from proxy file
        if proxy_file and os.path.exists(proxy_file):
            self.load_from_file(proxy_file)
            
        # If no proxies loaded, use default proxies
        if not self.proxies:
            default_proxies = [
                "http://8.130.34.237:5555", "http://8.130.36.245:80", 
                "http://8.130.37.235:9080", "http://8.130.39.117:8001",
                "http://8.146.200.53:8080", "http://8.148.24.225:9080"
            ]
            
            for proxy in default_proxies:
                self.add_proxy(proxy)
                
        # Pre-validate proxies asynchronously
        threading.Thread(target=self._prevalidate_proxies).start()
    
    def _prevalidate_proxies(self):
        """Test all proxies before using them in main operation."""
        logging.info(f"Pre-validating {len(self.proxies)} proxies...")
        validated_proxies = []
        
        for proxy_data in self.proxies[:]:
            proxy_url = proxy_data["proxy"]
            if self._test_proxy(proxy_url):
                validated_proxies.append(proxy_data)
            else:
                logging.info(f"Removing invalid proxy during pre-validation: {proxy_url}")
        
        with self.lock:
            self.proxies = validated_proxies
            
        logging.info(f"Pre-validation complete. {len(self.proxies)} valid proxies available.")
    
    def _test_proxy(self, proxy_url):
        """Test if a proxy works with a simple request."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.113 Safari/537.36"
            }
            
            proxies = {
                "http": proxy_url,
                "https": proxy_url
            }
            
            # Use a 5 second timeout for validation
            response = requests.get(
                "https://www.google.com", 
                proxies=proxies, 
                headers=headers, 
                timeout=5,
                verify=self.config.get("verify_ssl", True)
            )
            
            return response.status_code == 200
        except Exception as e:
            return False
    
    def load_from_file(self, filename):
        try:
            with open(filename, 'r') as f:
                for line in f:
                    proxy = line.strip()
                    if proxy:
                        self.add_proxy(proxy)
            logging.info(f"Loaded {len(self.proxies)} proxies from {filename}")
        except Exception as e:
            logging.error(f"Failed to load proxies from file: {e}")
    
    def add_proxy(self, proxy_url):
        with self.lock:
            if not any(p["proxy"] == proxy_url for p in self.proxies):
                self.proxies.append({
                    "proxy": proxy_url, 
                    "weight": 1.0, 
                    "failures": 0,
                    "success_count": 0,
                    "last_used": 0
                })
    
    def get_proxy(self):
        with self.lock:
            now = time.time()
            # Filter by failures and add cooldown
            available = [p for p in self.proxies 
                        if p["failures"] < self.max_failures 
                        and now - p["last_used"] > 10]  # 10 second cooldown
            
            if not available:
                return None
                
            # Calculate weighted probabilities
            total_weight = sum(p["weight"] for p in available)
            if total_weight == 0:
                return None
                
            choice = random.uniform(0, total_weight)
            cumulative = 0
            
            selected_proxy = None
            for proxy in available:
                cumulative += proxy["weight"]
                if choice <= cumulative:
                    selected_proxy = proxy
                    break
                    
            if selected_proxy:
                selected_proxy["last_used"] = now
                return selected_proxy["proxy"]
                
            return available[-1]["proxy"] if available else None

    async def report_failure(self, proxy):
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            self.failed_proxies.add(proxy)

            webhook_url = os.getenv("DECRYPT_BOT_PROXY_WEBHOOK")
        if not webhook_url:
            return

        try:
            async with aiohttp.ClientSession() as session:
                payload = {"content": f"🔌 Proxy removed: `{proxy}`"}
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200 or response.status == 204:
                        json_resp = await response.json()
                        message_id = json_resp.get("id")
                        channel_id = json_resp.get("channel_id")
                        
                        # Schedule deletion in 20 minutes (1200 seconds)
                        if message_id and channel_id:
                            await asyncio.sleep(1200)
                            delete_url = f"https://discord.com/api/v10/channels/{channel_id}/messages/{message_id}"
                            headers = {"Authorization": f"Bot {os.getenv('DECRYPT_BOT_TOKEN')}"}
                            await session.delete(delete_url, headers=headers)
        except Exception as e:
            print(f"[Proxy Warning] Failed to notify webhook: {e}")


    def report_success(self, proxy_url):
        with self.lock:
            for proxy in self.proxies:
                if proxy["proxy"] == proxy_url:
                    proxy["failures"] = 0
                    proxy["success_count"] += 1
                    proxy["weight"] = min(proxy["weight"] * 1.2, 2.0)  # Increase weight on success
                    break
                    
    def get_stats(self):
        with self.lock:
            active = len([p for p in self.proxies if p["failures"] < self.max_failures])
            total = len(self.proxies)
            success_rate = sum(p["success_count"] for p in self.proxies) / max(1, sum(p["success_count"] + p["failures"] for p in self.proxies))
            return {
                "active_proxies": active,
                "total_proxies": total,
                "success_rate": success_rate
            }


class TorController:
    """
    Controller for Tor network integration, providing IP rotation capabilities.
    """
    
    def __init__(self, port=9051, password=None):
        self.port = port
        self.password = password
        
    def renew_ip(self):
        """
        Signal the Tor controller to get a new circuit and thus a new IP address.
        """
        try:
            with Controller.from_port(port=self.port) as controller:
                if self.password:
                    controller.authenticate(password=self.password)
                else:
                    controller.authenticate()
                controller.signal(Signal.NEWNYM)
                logging.info("Renewed Tor IP")
                return True
        except Exception as e:
            logging.error(f"Failed to renew Tor IP: {e}")
            return False