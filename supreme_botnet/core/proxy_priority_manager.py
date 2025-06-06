import requests
import time
import logging
import random
from concurrent.futures import ThreadPoolExecutor

FAST_TEST_URL = "https://api.ipify.org?format=json"
ELITE_PROXY_LIST_URL = "http://11.22.33.44:3128/elite.txt"
FALLBACK_SOURCES = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://www.proxy-list.download/api/v1/get?type=http",
]

MAX_ATTEMPTS = 3
TIMEOUT = 5
THREADS = 50
MAX_GOOD = 50

def fetch_proxy_list(url):
    try:
        res = requests.get(url, timeout=TIMEOUT)
        lines = res.text.strip().splitlines()
        return [line.strip() for line in lines if ":" in line]
    except Exception as e:
        logging.warning(f"[Fetch] Failed to get proxies from {url}: {e}")
        return []

def validate_proxy(proxy):
    try:
        proxies = {
            "http": f"http://{proxy}",
            "https": f"http://{proxy}"
        }
        res = requests.get(FAST_TEST_URL, proxies=proxies, timeout=TIMEOUT)
        if res.status_code == 200:
            return proxy
    except:
        return None
    return None

def scan_and_validate(proxies):
    logging.info(f"[Scanner] Validating {len(proxies)} proxies...")
    valid = []
    with ThreadPoolExecutor(max_workers=THREADS) as pool:
        results = list(pool.map(validate_proxy, proxies))
    valid = [p for p in results if p]
    logging.info(f"[Scanner] {len(valid)} valid proxies found.")
    return valid[:MAX_GOOD]

def get_best_proxies():
    for attempt in range(1, MAX_ATTEMPTS + 1):
        logging.info(f"[Elite Attempt {attempt}] Trying elite list...")
        elite_proxies = fetch_proxy_list(ELITE_PROXY_LIST_URL)
        if elite_proxies:
            good = scan_and_validate(elite_proxies)
            if good:
                logging.info(f"[Elite] Using elite proxies.")
                return good
        logging.warning(f"[Elite] Attempt {attempt} failed. Retrying in 3s...")
        time.sleep(3)

    logging.info("[Fallback] Using public proxy sources.")
    fallback_proxies = []
    for src in FALLBACK_SOURCES:
        fallback_proxies.extend(fetch_proxy_list(src))
    return scan_and_validate(fallback_proxies)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    good_proxies = get_best_proxies()
    with open("data/working_proxies.txt", "w") as f:
        for proxy in good_proxies:
            f.write(proxy + "\n")
    print(f"\n✅ Saved {len(good_proxies)} working proxies to data/working_proxies.txt")
