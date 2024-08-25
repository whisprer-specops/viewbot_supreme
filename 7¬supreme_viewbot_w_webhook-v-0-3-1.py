import requests
import threading
import time
import random
import aiohttp
import asyncio
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# Configuration
VIDEO_URL = "https://www.youtube.com/watch?v=your_video_id"
WEBHOOK_URL = "https://discord.com/api/webhooks/your_webhook_id/your_webhook_token"
CAPTCHA_API_KEY = 'your_2captcha_api_key'
NUM_THREADS = 10  # Number of concurrent threads

# Rotating proxy class with IPv4 and IPv6 proxies
class ProxyPool:
    def __init__(self):
        self.ipv6_proxies = [
            {"proxy": "http://ipv6_proxy1:port", "weight": 5, "failures": 0},
            {"proxy": "http://ipv6_proxy2:port", "weight": 2, "failures": 0},
            {"proxy": "http://ipv6_proxy3:port", "weight": 1, "failures": 0},
        ]
        self.ipv4_proxies = [
            {"proxy": "http://ipv4_proxy1:port", "weight": 5, "failures": 0},
            {"proxy": "http://ipv4_proxy2:port", "weight": 3, "failures": 0},
            {"proxy": "http://ipv4_proxy3:port", "weight": 1, "failures": 0},
        ]
        self.max_failures = 3

    def get_proxy(self, ipv6=True):
        proxies = self.ipv6_proxies if ipv6 else self.ipv4_proxies
        total_weight = sum(proxy["weight"] for proxy in proxies)
        random_choice = random.uniform(0, total_weight)
        cumulative_weight = 0
        for proxy in proxies:
            cumulative_weight += proxy["weight"]
            if random_choice <= cumulative_weight:
                return proxy["proxy"]
        return None

    def report_failure(self, proxy_url):
        for proxies in [self.ipv6_proxies, self.ipv4_proxies]:
            for proxy in proxies:
                if proxy["proxy"] == proxy_url:
                    proxy["failures"] += 1
                    if proxy["failures"] >= self.max_failures:
                        print(f"Removing {proxy_url} due to repeated failures")
                        proxies.remove(proxy)
                    break

    def report_success(self, proxy_url):
        for proxies in [self.ipv6_proxies, self.ipv4_proxies]:
            for proxy in proxies:
                if proxy["proxy"] == proxy_url:
                    proxy["failures"] = 0
                    break

# Webhook notification function
def send_webhook_notification(video_url):
    payload = {
        "content": f"The bot has navigated to the next video: {video_url}"
    }
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(WEBHOOK_URL, json=payload, headers=headers)
        if response.status_code == 204:
            print("Webhook sent successfully.")
        else:
            print(f"Failed to send webhook: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Error sending webhook: {e}")

# CAPTCHA solving function
def solve_captcha(driver, site_key, url):
    payload = {
        'key': CAPTCHA_API_KEY,
        'method': 'userrecaptcha',
        'googlekey': site_key,
        'pageurl': url,
        'json': 1
    }
    response = requests.post('http://2captcha.com/in.php', data=payload)
    captcha_id = response.json().get('request')

    result_payload = {
        'key': CAPTCHA_API_KEY,
        'action': 'get',
        'id': captcha_id,
        'json': 1
    }

    for _ in range(30):  # Retry every 5 seconds for up to 150 seconds
        time.sleep(5)
        result = requests.get('http://2captcha.com/res.php', params=result_payload)
        if result.json().get('status') == 1:
            captcha_solution = result.json().get('request')
            logging.info(f"CAPTCHA solved: {captcha_solution}")
            driver.execute_script(f'document.getElementById("g-recaptcha-response").innerHTML="{captcha_solution}";')
            return True
        logging.info("Waiting for CAPTCHA solution...")
    
    logging.error("Failed to solve CAPTCHA.")
    return False

# Asynchronous fetch with proxy support
async def fetch(session, url, proxy_pool, ipv6=True):
    proxy = proxy_pool.get_proxy(ipv6=ipv6)
    headers = {"User-Agent": random.choice(user_agents)}
    try:
        async with session.get(url, proxy=proxy, headers=headers) as response:
            print(f"Request sent via {proxy}, status code: {response.status}")
            proxy_pool.report_success(proxy)
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}. Retrying with a different proxy...")
        proxy_pool.report_failure(proxy)

# Main async function to run the requests
async def main():
    proxy_pool = ProxyPool()
    async with aiohttp.ClientSession() as session:
        tasks = []
        for _ in range(NUM_THREADS):
            tasks.append(fetch(session, VIDEO_URL, proxy_pool))
        await asyncio.gather(*tasks)

# User-Agent randomization setup
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/89.0",
]

# Main bot function
def run_bot():
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run headless for performance
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")

    # Initialize the WebDriver
    driver = webdriver.Chrome(options=chrome_options)

    # Visit the YouTube video URL
    driver.get(VIDEO_URL)
    time.sleep(5)  # Wait for the page to load

    # Check for CAPTCHA (assuming reCAPTCHA)
    try:
        captcha_element = driver.find_element(By.CLASS_NAME, 'g-recaptcha')
        if captcha_element:
            site_key = driver.execute_script("return document.querySelector('.g-recaptcha').dataset.sitekey;")
            if solve_captcha(driver, site_key, VIDEO_URL):
                print("CAPTCHA solved successfully.")
            else:
                print("Failed to solve CAPTCHA.")
                driver.quit()
                return
    except Exception as e:
        print("No CAPTCHA detected.")

    # Find the 'Next' button and navigate to the next video
    try:
        next_button = driver.find_element(By.CSS_SELECTOR, 'a.ytp-next-button.ytp-button')
        next_button.click()
        time.sleep(5)  # Wait for the next video to load

        # Get the new video URL after navigation
        new_video_url = driver.current_url
        print(f"Navigated to the next video: {new_video_url}")

        # Send webhook notification
        send_webhook_notification(new_video_url)

    except Exception as e:
        print(f"Could not find or click the 'Next' button: {e}")

    # Close the browser
    driver.quit()

# Start the bot
if __name__ == "__main__":
    # Run the proxy-supported main function asynchronously
    asyncio.run(main())

    # Run the YouTube navigation bot
    run_bot()
