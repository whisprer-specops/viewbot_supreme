# File: core/paywall_proxy_scanner.py

import requests
from concurrent.futures import ThreadPoolExecutor

class ProxyScanner:
    TEST_URL = "http://proxy-test.fastcheck.it.com/ip"
    ELITE_PROXY_URL = "http://11.22.33.44:3128"

    @staticmethod
    def fetch_raw_proxies():
        try:
            response = requests.get(ProxyScanner.ELITE_PROXY_URL, timeout=10)
            if response.status_code == 200:
                return list(set([
                    line.strip()
                    for line in response.text.splitlines()
                    if line.strip() and ':' in line
                ]))
        except Exception as e:
            print(f"[ProxyScanner] Failed to fetch proxies: {e}")
        return []

    @staticmethod
    def is_proxy_working(proxy):
        try:
            proxies = {
                "http": f"http://{proxy}",
                "https": f"http://{proxy}",
            }
            r = requests.get(ProxyScanner.TEST_URL, proxies=proxies, timeout=3)
            return r.status_code == 200
        except:
            return False

    @staticmethod
    def validate_proxies(proxy_list, max_ok=100):
        working = []
        with ThreadPoolExecutor(max_workers=50) as executor:
            results = executor.map(ProxyScanner.is_proxy_working, proxy_list)
            for proxy, result in zip(proxy_list, results):
                if result:
                    working.append(proxy)
                    if len(working) >= max_ok:
                        break
        return working

    @staticmethod
    def fetch_and_validate(max_proxies=100):
        raw = ProxyScanner.fetch_raw_proxies()
        return ProxyScanner.validate_proxies(raw, max_ok=max_proxies)
