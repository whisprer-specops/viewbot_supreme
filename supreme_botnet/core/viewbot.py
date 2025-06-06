from utils.paywall_buster import PaywallBuster
from behavior.humanizer import simulate_human_scroll, simulate_mouse_jitter
import asyncio
from urllib.parse import urlparse

def is_known_paywalled_site(url):
    return any(domain in url.lower() for domain in ["medium.com", "substack.com", "wsj.com"])

async def emulate_human_behavior(driver):
    await simulate_mouse_jitter(driver)
    await simulate_human_scroll(driver)

def process_paywall_if_needed(url, driver):
    if is_known_paywalled_site(url):
        print("[*] Target paywalled site detected. Attempting paywall bypass...")
        pb = PaywallBuster()
        readable = pb.extract_readable_text(url)
        print("\\n[Paywall Buster Output]\\n", readable[:1000], "...\\n")

        print("[*] Simulating human behavior during visit...")
        asyncio.run(emulate_human_behavior(driver))