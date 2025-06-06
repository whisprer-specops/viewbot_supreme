# core/proxy_scanner.py

import requests
import concurrent.futures
import random
import time
import logging

class ProxyScanner:
    def __init__(self, sources=None, timeout=5, threads=50, max_results=50, prioritized=False):
        default_sources = [
            "https://your-eliteproxyswitcher-url.com/elite.txt",  # <- top dog
            "https://free-proxy-list.net/",
            "https://www.sslproxies.org/",
            "https://www.socks-proxy.net/",
            "https://proxy-daily.com/",
            "https://spys.one/en/",
            "https://hidemy.name/en/proxy-list/",
            "https://proxyscrape.com/free-proxy-list",
            "https://api.proxyscrape.com/?request=getproxies&proxytype=http",
            "https://openproxy.space/list/http",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
            "https://github.com/clarketm/proxy-list/raw/master/proxy-list-raw.txt",
            "https://www.proxy-list.download/api/v1/get?type=http",
            "https://proxynova.com/proxy-server-list/",
            "https://free-proxy.cz/en/"
        ]
        self.sources = sources or default_sources
        if prioritized:
            self.sources = sorted(self.sources, key=lambda x: 0 if "eliteproxyswitcher" in x else 1)

        self.timeout = timeout
        self.threads = threads
        self.max_results = max_results
        self.good_proxies = []

    def fetch_sources(self):
        proxies = set()
        for url in self.sources:
            try:
                res = requests.get(url, timeout=self.timeout)
                lines = res.text.strip().splitlines()
                for line in lines:
                    if ":" in line and "." in line:
                        proxies.add(line.strip())
            except Exception as e:
                logging.warning(f"[ProxyScanner] Failed to fetch from {url}: {e}")
        return list(proxies)

    def test_proxy(self, proxy):
        test_url = "https://api.ipify.org"
        proxies = {
            "http": f"http://{proxy}",
            "https": f"http://{proxy}"
        }
        try:
            r = requests.get(test_url, proxies=proxies, timeout=self.timeout)
            if r.status_code == 200 and len(r.text.strip()) > 6:
                return proxy
        except:
            return None
        return None

    def scan(self):
        raw = self.fetch_sources()
        logging.info(f"[ProxyScanner] Fetched {len(raw)} proxies, scanning...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.threads) as executor:
            results = list(executor.map(self.test_proxy, raw))
        self.good_proxies = list(filter(None, results))
        random.shuffle(self.good_proxies)
        return self.good_proxies[:self.max_results]

    def fetch_sources(self):
        proxies = set()
        for url in self.sources:
            try:
                logging.info(f"[ProxyScanner] Fetching from: {url}")
                res = requests.get(url, timeout=self.timeout)
                lines = res.text.strip().splitlines()
                for line in lines:
                    if ":" in line and "." in line:
                        proxies.add(line.strip())
            except Exception as e:
                logging.warning(f"[ProxyScanner] Failed from {url}: {e}")
        return list(proxies)

    def export(self, filepath):
        with open(filepath, "w") as f:
            for proxy in self.good_proxies:
                f.write(proxy.strip() + "\n")
        logging.info(f"[ProxyScanner] Exported {len(self.good_proxies)} proxies → {filepath}")
