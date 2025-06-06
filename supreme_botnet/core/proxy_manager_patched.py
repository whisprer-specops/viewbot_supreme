# core/proxy_manager.py

# core/proxy_manager.py

import threading
import time
import logging
import os
from core.proxy_scanner import ProxyScanner
# ===================================================================
# Proxy Test Endpoint Strategy
# ===================================================================
TEST_ENDPOINTS = [
    'https://proxy-test.fastping.it.com',    # Fast custom microservice
    'https://api.ipify.org/?format=json',    # Lightweight fallback
    'http://ip-api.com/json/'                # Reliable but slower
]

# DNS cache to reduce overhead
DNS_CACHE = {}

class ProxyManager:
    def __init__(self, refresh_interval_min=15, max_proxies=100, disable_refresh=False):
        self.pool = []
        self.lock = threading.Lock()
        self.refresh_interval = refresh_interval_min * 60
        self.max_proxies = max_proxies
        self.stop_event = threading.Event()
        self.refresh_failures = 0
        if not disable_refresh:
            self._start_refresh_thread()

    def _start_refresh_thread(self):
        thread = threading.Thread(target=self._refresh_loop, daemon=True)
        thread.start()
        logging.info(f"[ProxyManager] Auto-refresh thread started (every {self.refresh_interval // 60} minutes)")

    def _refresh_loop(self):
        while not self.stop_event.is_set():
            try:
                self.refresh_and_load()
                self.refresh_failures = 0
            except Exception as e:
                self.refresh_failures += 1
                logging.warning(f"[ProxyManager] Proxy refresh failed: {e} (fail #{self.refresh_failures})")
                if self.refresh_failures >= 3:
                    logging.warning("[ProxyManager] 3x scanner failure – falling back to proxies.txt...")
                    self.load_from_file("data/proxies.txt")
                    self.refresh_failures = 0
            time.sleep(self.refresh_interval)

    def refresh_and_load(self):
        logging.info("[ProxyManager] Fetching fresh proxies via scanner...")
        scanner = ProxyScanner(max_results=self.max_proxies)
        new_proxies = scanner.scan()
        if new_proxies:
            with self.lock:
                self.pool = new_proxies
            logging.info(f"[ProxyManager] Refreshed proxy pool with {len(new_proxies)} entries.")
        else:
            raise RuntimeError("No fresh proxies found")

    def load_from_file(self, path):
        if not os.path.exists(path):
            logging.error(f"[ProxyManager] Proxy fallback file not found: {path}")
            return
        with open(path, "r") as f:
            fallback_proxies = [line.strip() for line in f if line.strip()]
        with self.lock:
            self.pool = fallback_proxies
        logging.info(f"[ProxyManager] Loaded {len(fallback_proxies)} proxies from fallback file.")

        # If no proxies loaded from file, use default proxies
        if not self.proxies:
            default_proxies = [
                "http://8.130.34.237:5555", "http://8.130.36.245:80", 
                "http://8.130.37.235:9080", "http://8.130.39.117:8001",
                "http://8.146.200.53:8080", "http://8.148.24.225:9080"
            ]
            
            for proxy in default_proxies:
                self.add_proxy(proxy)

    def get_proxy(self):
        with self.lock:
            if not self.pool:
                logging.warning("[ProxyManager] Proxy pool is empty!")
                return None
            return self.pool.pop(0)

    def get_pool_size(self):
        with self.lock:
            return len(self.pool)

    def stop(self):
        self.stop_event.set()