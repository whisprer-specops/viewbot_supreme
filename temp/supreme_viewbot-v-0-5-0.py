import os
import random
import time
import threading
import asyncio
import aiohttp
import logging
import requests
import markovify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from stem import Signal
from stem.control import Controller
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Configuration
STORY_URL = "https://medium.com/@cgpt/is-vibe-coding-cheating-or-the-future-of-programming-in-the-workplace-216fe9d5084d"
WEBHOOK_URL = "https://discord.com/api/webhooks/1368210146949464214/QqgJoJOeI2qzfQjqlMCVWKgHpYqCZFGlVQ9EnugixWmwaP567xQw1w7l7DEm-pqOpP93"
CAPTCHA_API_KEY = os.getenv('CAPTCHA_API_KEY', '2CAPTCHA_APIKEY')  # Load from env var
NUM_THREADS = 7
REQUESTS_PER_THREAD = random.randint(50, 100)  # Randomized requests
DELAY_BETWEEN_REQUESTS = random.uniform(30.0, 45.0)  # Randomized delays
USE_TOR = False  # Toggle Tor routing

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Encryption for webhook payloads
def generate_encryption_key():
    salt = os.urandom(16)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
    key = base64.urlsafe_b64encode(kdf.derive(b"super_secret_password"))
    return Fernet(key)

cipher = generate_encryption_key()

# Proxy pool with weighted rotation
class ProxyPool:
    def __init__(self):
        self.proxies = [
            {"proxy": "http://8.130.34.237:5555", "weight": 1.0, "failures": 0},
            {"proxy": "http://8.130.36.245:80", "weight": 1.0, "failures": 0},
            {"proxy": "http://8.130.37.235:9080", "weight": 1.0, "failures": 0},
            {"proxy": "http://8.130.39.117:8001", "weight": 1.0, "failures": 0},
            {"proxy": "http://8.146.200.53:8080", "weight": 1.0, "failures": 0},
            {"proxy": "http://8.148.24.225:9080", "weight": 1.0, "failures": 0},
            {"proxy": "http://8.212.165.164:1000", "weight": 1.0, "failures": 0},
            {"proxy": "http://8.213.129.15:50001", "weight": 1.0, "failures": 0},
            {"proxy": "http://8.213.222.157:3128", "weight": 1.0, "failures": 0},
            {"proxy": "http://8.219.97.248:80", "weight": 1.0, "failures": 0},
            # Add more proxies as needed
        ]
        self.max_failures = 3
        self.is_ipv6 = False  # All proxies are IPv4 based on inspection

    def get_proxy(self):
        proxies = [p for p in self.proxies if p["failures"] < self.max_failures]
        if not proxies:
            return None
        total_weight = sum(p["weight"] for p in proxies)
        choice = random.uniform(0, total_weight)
        cumulative = 0
        for proxy in proxies:
            cumulative += proxy["weight"]
            if choice <= cumulative:
                return proxy["proxy"]
        return proxies[-1]["proxy"]

    def report_failure(self, proxy_url):
        for proxy in self.proxies:
            if proxy["proxy"] == proxy_url:
                proxy["failures"] += 1
                proxy["weight"] *= 0.5  # Reduce weight on failure
                if proxy["failures"] >= self.max_failures:
                    logging.info(f"Removing proxy {proxy_url} due to excessive failures")
                    self.proxies.remove(proxy)
                break

    def report_success(self, proxy_url):
        for proxy in self.proxies:
            if proxy["proxy"] == proxy_url:
                proxy["failures"] = 0
                proxy["weight"] = min(proxy["weight"] * 1.2, 2.0)  # Increase weight on success
                break

# Tor setup
def renew_tor_ip():
    with Controller.from_port(port=9051) as controller:
        controller.authenticate()
        controller.signal(Signal.NEWNYM)
        logging.info("Renewed Tor IP")

# Webhook notification with encryption
def send_webhook_notification(message):
    encrypted_message = cipher.encrypt(message.encode()).decode()
    payload = {"content": f"Encrypted: {encrypted_message}"}
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(WEBHOOK_URL, json=payload, headers=headers)
        if response.status_code == 204:
            logging.info("Webhook sent successfully")
        else:
            logging.error(f"Failed to send webhook: {response.status_code}")
    except Exception as e:
        logging.error(f"Error sending webhook: {e}")

# CAPTCHA solving
def solve_captcha(driver, site_key, url):
    payload = {
        'key': CAPTCHA_API_KEY,
        'method': 'userrecaptcha',
        'googlekey': site_key,
        'pageurl': url,
        'json': 1
    }
    try:
        response = requests.post('http://2captcha.com/in.php', data=payload)
        captcha_id = response.json().get('request')
        result_payload = {'key': CAPTCHA_API_KEY, 'action': 'get', 'id': captcha_id, 'json': 1}
        for _ in range(30):
            time.sleep(5)
            result = requests.get('http://2captcha.com/res.php', params=result_payload)
            if result.json().get('status') == 1:
                captcha_solution = result.json().get('request')
                logging.info("CAPTCHA solved successfully")
                driver.execute_script(f'document.getElementById("g-recaptcha-response").innerHTML="{captcha_solution}";')
                return True
            logging.info("Waiting for CAPTCHA solution...")
        logging.error("Failed to solve CAPTCHA")
        return False
    except Exception as e:
        logging.error(f"CAPTCHA solving error: {e}")
        return False

# Markov chain comment generator
def generate_comment(article_text):
    text_model = markovify.Text(article_text, state_size=2)
    comment = text_model.make_short_sentence(280, tries=100) or "Great article, very insightful!"
    return comment

# Medium interaction
def interact_with_medium(driver, proxy_pool, comment_text):
    try:
        proxy = proxy_pool.get_proxy()
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920x1080")
        if USE_TOR:
            chrome_options.add_argument("--proxy-server=socks5://127.0.0.1:9050")
        elif proxy:
            chrome_options.add_argument(f"--proxy-server={proxy}")

        driver = webdriver.Chrome(options=chrome_options)
        driver.get(STORY_URL)
        time.sleep(random.uniform(3, 7))  # Random page load wait

        # Handle CAPTCHA if present
        try:
            captcha_element = driver.find_element(By.CLASS_NAME, 'g-recaptcha')
            site_key = driver.execute_script("return document.querySelector('.g-recaptcha').dataset.sitekey;")
            if not solve_captcha(driver, site_key, STORY_URL):
                driver.quit()
                return
        except:
            logging.info("No CAPTCHA detected")

        # Clap the article
        try:
            clap_button = driver.find_element(By.CSS_SELECTOR, 'button[data-testid="clap-button"]')
            clap_button.click()
            logging.info("Clapped the article")
        except Exception as e:
            logging.error(f"Error clapping: {e}")

        # Follow the author
        try:
            follow_button = driver.find_element(By.CSS_SELECTOR, 'button[data-testid="follow-button"]')
            follow_button.click()
            logging.info("Followed the author")
        except Exception as e:
            logging.error(f"Error following: {e}")

        # Add comment
        try:
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            article_text = soup.get_text()
            comment = generate_comment(article_text)
            comment_box = driver.find_element(By.CSS_SELECTOR, 'textarea[data-testid="comment-input"]')
            comment_box.click()
            comment_box.send_keys(comment)
            comment_box.send_keys(Keys.CONTROL, Keys.ENTER)
            logging.info(f"Commented: {comment}")
        except Exception as e:
            logging.error(f"Error commenting: {e}")

        # Send webhook notification
        send_webhook_notification(f"Interacted with {STORY_URL}: clapped, followed, commented")
        proxy_pool.report_success(proxy)

    except Exception as e:
        logging.error(f"Interaction error: {e}")
        if proxy:
            proxy_pool.report_failure(proxy)
    finally:
        driver.quit()

# Async fetch for view boosting
async def fetch(session, url, proxy_pool):
    proxy = proxy_pool.get_proxy() if not USE_TOR else "socks5://127.0.0.1:9050"
    headers = {"User-Agent": random.choice(user_agents)}
    try:
        async with session.get(url, proxy=proxy, headers=headers) as response:
            logging.info(f"View sent via {proxy}, status: {response.status}")
            proxy_pool.report_success(proxy)
    except Exception as e:
        logging.error(f"View failed: {e}")
        proxy_pool.report_failure(proxy)

# Main async function
async def main():
    proxy_pool = ProxyPool()
    async with aiohttp.ClientSession() as session:
        tasks = []
        for _ in range(NUM_THREADS):
            for _ in range(REQUESTS_PER_THREAD):
                tasks.append(fetch(session, STORY_URL, proxy_pool))
                await asyncio.sleep(DELAY_BETWEEN_REQUESTS)
        await asyncio.gather(*tasks)

# User agents
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.113 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    # Add more as needed
]

# Run bot
if __name__ == "__main__":
    proxy_pool = ProxyPool()
    threads = []
    for _ in range(NUM_THREADS):
        thread = threading.Thread(target=interact_with_medium, args=(webdriver, proxy_pool, ""))
        threads.append(thread)
        thread.start()
        time.sleep(random.uniform(1, 3))
    asyncio.run(main())
    for thread in threads:
        thread.join()