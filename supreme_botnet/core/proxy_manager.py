import random
import threading
import time
import logging

class ProxyManager:
    def __init__(self, proxy_file="working_proxies.txt", disable_refresh=False):
        self.proxies = []
        self.index = 0
        self.lock = threading.Lock()
        self.disable_refresh = disable_refresh
        self.load_from_file(proxy_file)

        logging.info(f"[ProxyManager] Loaded {len(self.proxies)} proxies: {self.proxies[:5]}")

        if not self.disable_refresh:
            logging.info("[ProxyManager] Auto-refresh thread started.")
            self.start_auto_refresh()

    def load_from_file(self, filepath):
        try:
            with open(filepath, 'r') as f:
                self.proxies = [line.strip() for line in f if line.strip()]
        except Exception as e:
            logging.error(f"[ProxyManager] Failed to load proxies from {filepath}: {e}")
            self.proxies = []

    def start_auto_refresh(self, interval=900):
        def refresh():
            while True:
                time.sleep(interval)
                logging.info("[ProxyManager] Refreshing proxy list.")
                self.load_from_file("working_proxies.txt")

        t = threading.Thread(target=refresh, daemon=True)
        t.start()

    def get_proxy(self):
        with self.lock:
            if not self.proxies:
                logging.warning("[ProxyManager] No proxies available.")
                return None
            proxy = self.proxies[self.index % len(self.proxies)]
            self.index += 1
            return proxy

    def get_proxies(self):
        return self.proxies
