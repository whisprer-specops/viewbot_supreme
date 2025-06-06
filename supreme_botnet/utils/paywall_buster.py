import sys
import os
import logging
import aiohttp
import asyncio
import random
from bs4 import BeautifulSoup
from urllib.parse import urljoin

import sys
import os
import logging
import aiohttp
import asyncio
import random
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Fix for relative imports if run directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.proxy_manager import ProxyManager

class MediumPaywallBuster:
    def __init__(self, config=None, proxies=None):
        self.config = config
        self.proxies = proxies or []
        self.session = None

    async def initialize(self):
        logging.info("[PaywallBuster] Initialized.")

    async def fetch_article_text(self, url):
        proxy = self._pick_proxy()
        logging.info(f"[PaywallBuster] Using proxy: {proxy or 'DIRECT'}")
        html = await self._fetch(url, proxy)
        if not html:
            return "[!] Failed to fetch article content."

        canonical_url = self._extract_canonical_url(html)
        if canonical_url and canonical_url != url:
            logging.info(f"[PaywallBuster] Redirected via canonical URL: {canonical_url}")
            html = await self._fetch(canonical_url, proxy)

        return self._extract_main_text(html)

    def _pick_proxy(self):
        return random.choice(self.proxies) if self.proxies else None

    async def _fetch(self, url, proxy=None):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        try:
            # async with aiohttp.ClientSession(headers=headers) as session:
                connector = aiohttp.TCPConnector(ssl=False)
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.get(url, proxy=f"http://{proxy}" if proxy else None, timeout=15) as resp:
                        if resp.status == 200:
                            return await resp.text()
                    logging.warning(f"[PaywallBuster] Status {resp.status} on {url}")
        except Exception as e:
            logging.warning(f"[PaywallBuster] Fetch failed: {e}")
        return None

    def _extract_canonical_url(self, html):
        soup = BeautifulSoup(html, "html.parser")
        tag = soup.find("link", rel="canonical")
        return tag["href"] if tag and "href" in tag.attrs else None

    def _extract_main_text(self, html):
        soup = BeautifulSoup(html, "html.parser")
        article = soup.find("article") or soup.find("div", {"data-target-id": "post-content"})
        if not article:
            return "[!] No article body found."
        paragraphs = article.find_all("p")
        return "\n\n".join(p.get_text(strip=True) for p in paragraphs)


# CLI entrypoint
if __name__ == "__main__":
    import argparse

    def get_args():
        parser = argparse.ArgumentParser()
        parser.add_argument("--url", required=True, help="Target URL to scrape")
        parser.add_argument("--captcha-key", required=False, help="2Captcha API key")
        return parser.parse_args()

    async def run_main(url, captcha_key=None):
        logging.basicConfig(level=logging.INFO)

        pm = ProxyManager(disable_refresh=True)
        pm.load_from_file("data/working_proxies.txt")

        buster = MediumPaywallBuster(proxies=pm.proxies)
        await buster.initialize()

        logging.info(f"[PaywallBuster] Loaded {len(buster.proxies)} proxies: {buster.proxies[:5]}")
        text = await buster.fetch_article_text(url)
        print("\n[SCRAPED CONTENT]\n" + text[:3000] + "\n...\n")
        print(f"Status: {response.status}")
        print(f"Headers: {response.headers}")

    args = get_args()
    asyncio.run(run_main(args.url, args.captcha_key))
