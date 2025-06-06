# core/browser.py

import logging
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from core.user_agent import UserAgentManager
from core.proxy_manager import ProxyManager
from pathlib import Path
import undetected_chromedriver as uc


import asyncio
from utils.paywall_buster import PaywallBuster
from behavior.humanizer import simulate_mouse_jitter, simulate_human_scroll
from urllib.parse import urlparse

def is_known_paywalled_site(url):
    return any(domain in url.lower() for domain in ["medium.com", "substack.com", "wsj.com"])

async def simulate_human_activity(driver):
    await simulate_mouse_jitter(driver)
    await simulate_human_scroll(driver)

def maybe_bust_paywall(driver, url):
    if is_known_paywalled_site(url):
        print("[*] Paywalled site detected. Extracting readable content and simulating human activity...")
        try:
            pb = PaywallBuster()
            readable = pb.extract_readable_text(url)
            print("\n--- Extracted Article Content (preview) ---\n")
            print(readable[:1200], "...\n")
        except Exception as e:
            print("[!] Paywall bypass failed:", e)

        try:
            asyncio.run(simulate_human_activity(driver))
        except Exception as e:
            print("[!] Human behavior simulation failed:", e)

class BrowserSession:
    def __init__(self, driver, account):
        self.driver = driver
        self.account = account

    def clap_article(self, url):
        try:
            self.driver.get(url)
            maybe_bust_paywall(self.driver, url)
            maybe_bust_paywall(self.driver, url)
            maybe_bust_paywall(self.driver, url)
            time.sleep(random.uniform(3, 5))
            clap_btns = self.driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'clap')]")
            if not clap_btns:
                raise Exception("No clap buttons found.")
            for btn in clap_btns:
                self.driver.execute_script("arguments[0].click();", btn)
                time.sleep(0.5)
            return True
        except Exception as e:
            logging.warning(f"[BrowserSession] Failed to clap: {e}")
            return False

    def watch_video(self, url):
        try:
            self.driver.get(url)
            maybe_bust_paywall(self.driver, url)
            maybe_bust_paywall(self.driver, url)
            maybe_bust_paywall(self.driver, url)
            time.sleep(5)
            # Optional: press play manually
            return True
        except Exception as e:
            logging.warning(f"[BrowserSession] Failed to watch video: {e}")
            return False

    def cast_vote(self, url):
        try:
            self.driver.get(url)
            maybe_bust_paywall(self.driver, url)
            maybe_bust_paywall(self.driver, url)
            maybe_bust_paywall(self.driver, url)
            time.sleep(2)
            vote_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Vote')]")
            vote_btn.click()
            time.sleep(2)
            return True
        except Exception as e:
            logging.warning(f"[BrowserSession] Failed to vote: {e}")
            return False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.driver.quit()
        except Exception:
            pass


class BrowserController:
    def __init__(self, headless=True, user_agent_mgr: UserAgentManager = None, proxy_mgr: ProxyManager = None):
        self.headless = headless
        self.ua_mgr = user_agent_mgr
        self.proxy_mgr = proxy_mgr
        self.dead_proxies = set()

    def get_proxy(self):
        if self.proxy_mgr:
            return self.proxy_mgr.get_random_proxy()
        return None

    def mark_proxy_dead(self, proxy):
        if self.proxy_mgr and proxy:
            self.proxy_mgr.mark_dead(proxy)

    def launch(self, account=None, proxy=None):
        try:
            options = uc.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            if self.headless:
                options.add_argument("--headless=new")

            user_agent = self.ua_mgr.get_random_user_agent()
            options.add_argument(f"user-agent={user_agent}")

            if proxy:
                options.add_argument(f'--proxy-server={proxy}')

            driver = uc.Chrome(options=options)
            logging.info("[BrowserController] Chrome launched.")
            return BrowserSession(driver, account)

        except Exception as e:
            logging.error(f"[BrowserController] Failed to launch browser: {e}")
            if proxy:
                self.mark_proxy_dead(proxy)
            raise
