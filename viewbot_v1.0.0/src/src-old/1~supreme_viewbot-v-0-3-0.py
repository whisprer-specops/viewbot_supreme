import requests
import threading
import time
import random
import aiohttp
import asyncio
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import O
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# Configuration
VIDEO_URL = "https://medium.com/@cgpt/is-vibe-coding-cheating-or-the-future-of-programming-in-the-workplace-216fe9d5084d"
WEBHOOK_URL = "https://discord.com/api/webhooks/1368210146949464214/QqgJoJOeI2qzfQjqlMCVWKgHpYqCZFGlVQ9EnugixWmwaP567xQw1w7l7DEm-pqOpP93"
CAPTCHA_API_KEY = '2CAPTCHA_APIKEY'
NUM_THREADS = 10  # Number of concurrent thread
COMMENT_TEXT = "" # @Claude: can you make a lil markov bot code here to generate random seeming comments that make sense but vary?

# Rotating proxy class with IPv4 and IPv6 proxi
class ProxyPool:
    def __init__(self):
        self.ipv6_proxies = [
            {"proxy": "http://ipv6_proxy1:port"
            {"proxy": "http://ipv6_proxy2:port"
            {"proxy": "http://ipv6_proxy3:port"
        ]
        self.ipv4_proxies = [
            {"proxy": "http://ipv4_proxy1:port"
            {"proxy": "http://ipv4_proxy2:port"
            {"proxy": "http://ipv4_proxy3:port"
        ]
        self.max_failures = 3

    def get_proxy(self, ipv6=True):
        proxies = self.ipv6_proxies if ipv6 els
        total_weight = sum(proxy["weight"] for 
        random_choice = random.uniform(0, total
        cumulative_weight = 0
        for proxy in proxies:
            cumulative_weight += proxy["weight"
            if random_choice <= cumulative_weig
                return proxy["proxy"]
        return None

    def report_failure(self, proxy_url):
        for proxies in [self.ipv6_proxies, self
            for proxy in proxies:
                if proxy["proxy"] == proxy_url:
                    proxy["failures"] += 1
                    if proxy["failures"] >= sel
                        print(f"Removing {proxy
                        proxies.remove(proxy)
                    break

    def report_success(self, proxy_url):
        for proxies in [self.ipv6_proxies, self
            for proxy in proxies:
                if proxy["proxy"] == proxy_url:
                    proxy["failures"] = 0
                    break

# Webhook notification function
def send_webhook_notification(video_url):
    payload = {
        "content": f"The bot has navigated to t
    }
    headers = {
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(WEBHOOK_URL, j
        if response.status_code == 204:
            print("Webhook sent successfully.")
        else:
            print(f"Failed to send webhook: {re
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

        try:
            response = requests.post('http://2captcha.com/in.php', data=payload)
            captcha_id = response.json().get('request')

            result_payload = {
                'key': CAPTCHA_API_KEY,
                'action': 'get',
                'id': 2CAPTCHA_ID,
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
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.113 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.116 Mobile Safari/537.362",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:125.0) Gecko/20100101 Firefox/125.0",
        "Mozilla/5.0 (Linux; Android 14; Samsung Galaxy S24 Ultra) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.99 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 13; OnePlus 11 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.87 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 14; Xiaomi 14 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.120 Mobile Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; ARM64; Surface Pro X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.118 Safari/537.36 Edg/124.0.2478.80",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.207 Safari/537.36",
        "Mozilla/5.0 (Linux; Android 13; Pixel 7a) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.99 Mobile Safari/537.36",
        "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6440.60 Safari/537.36 Edg/126.0.2478.40",
        "Mozilla/5.0 (Linux; Android 12; Samsung Galaxy Tab S8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.64 Safari/537.36",
        "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0"
    ]

# Like and comment on the video
def like_and_comment_video(driver, comment_text):
    try:
        # Like the video
        like_button = driver.find_element(By.CSS_SELECTOR, 'button[aria-label="I like this"]')
        like_button.click()
        print("Liked the video.")

        # Scroll down to the comments section
        driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
        time.sleep(2)  # Give time for the comments section to load

        # Locate the comment box, input the comment, and submit it
        comment_box = driver.find_element(By.CSS_SELECTOR, 'ytd-comment-simplebox-renderer')
        comment_box.click()
        time.sleep(1)
        comment_input = driver.switch_to.active_element
        comment_input.send_keys(comment_text)
        comment_input.send_keys(Keys.CONTROL, Keys.ENTER)
        print("Commented on the video.")

    except Exception as e:
        print(f"Error liking or commenting on the video: {e}")

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

        # Like and comment on the video
        like_and_comment_video(driver, COMMENT_TEXT)

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

    #