import argparse
import logging
from core.proxy_manager import ProxyManager
import time
import threading

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

def bot_worker(bot_id, proxy, url):
    print(f"[BOT {bot_id}] Using proxy: {proxy}")
    proxies = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
    try:
        response = requests.get(url, proxies=proxies, timeout=10)
        print(f"[BOT {bot_id}] Status: {response.status_code}")
        if response.ok:
            print(f"[BOT {bot_id}] Success! Got {len(response.text)} bytes")
        else:
            print(f"[BOT {bot_id}] Failed with status code {response.status_code}")
    except Exception as e:
        print(f"[BOT {bot_id}] Exception: {e}")

def wait_for_proxies(manager, required=3, timeout=30):
    for _ in range(timeout):
        if manager.get_pool_size() >= required:
            return True
        time.sleep(1)
    return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="Target URL")
    parser.add_argument("--count", type=int, default=3, help="Number of bots to simulate")
    parser.add_argument("--refresh-proxies", action="store_true", help="Force refresh proxies")
    args = parser.parse_args()

    logging.info("[INFO] Fetching proxies...")
    proxy_manager = ProxyManager(refresh_interval_min=15, max_proxies=100)

    if args.refresh_proxies:
        proxy_manager.fetch_proxies(force_refresh=True)

    logging.info("[RUNNER] Waiting for at least 3 proxies...")
    if not wait_for_proxies(proxy_manager, required=args.count, timeout=30):
        logging.error("Not enough proxies available. Exiting.")
        return

    logging.info(f"[RUNNER] Proxy pool size: {proxy_manager.get_pool_size()}")

    for i in range(args.count):
        proxy = proxy_manager.get_proxy()
        print(f"[BOT {i+1}] Got proxy: {proxy}")

if __name__ == "__main__":
    main()
