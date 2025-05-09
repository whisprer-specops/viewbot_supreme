import os
import queue
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
CAPTCHA_API_KEY = os.getenv('2CAPTCHA_APIKEY')  # Load from env var
NUM_THREADS = 7
REQUESTS_PER_THREAD = random.randint(50, 100)  # Randomized requests
DELAY_BETWEEN_REQUESTS = random.uniform(30.0, 45.0)  # Randomized delays
USE_TOR = False  # Toggle Tor routing
ACCOUNTS = [
    {'username': 'geoffrey.le@proton.me', 'password': 'pass1'},
    {'username': 'user2@example.com', 'password': 'pass2'},
    # Add more accounts here
]
# Temp email service API (using Temp-Mail as an example)
TEMP_EMAIL_API = "https://api.proton-mail.org/request"
TEMP_EMAIL_DOMAIN = "proton.me"

# Starting article (replace with a real free Medium article)
starting_articles = ['https://medium.com/the-narrative-arc/if-you-want-to-be-a-writer-maybe-read-this-first-okay-54a341d293e6']
for article in starting_articles:
    article_queue.put(article)

# Article queue
article_queue = queue.Queue()

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
            {"proxy": "http://9.223.187.19:3128", "weight": 1.0, "failures": 0},
            {"proxy": "http://34.102.48.89:8080", "weight": 1.0, "failures": 0},
            {"proxy": "http://37.140.51.159:80", "weight": 1.0, "failures": 0},
            {"proxy": "http://38.49.129.205:999", "weight": 1.0, "failures": 0},
            {"proxy": "http://38.65.172.81:999", "weight": 1.0, "failures": 0},
            {"proxy": "http://39.100.88.89:9080", "weight": 1.0, "failures": 0},
            {"proxy": "http://39.102.211.162:8081", "weight": 1.0, "failures": 0},
            {"proxy": "http://39.102.213.3:1111", "weight": 1.0, "failures": 0},
            {"proxy": "http://39.102.214.152:8080", "weight": 1.0, "failures": 0},
            {"proxy": "http://39.102.214.208:8080", "weight": 1.0, "failures": 0},
            {"proxy": "http://39.104.69.76:3128", "weight": 1.0, "failures": 0},
            {"proxy": "http://41.59.90.175:80", "weight": 1.0, "failures": 0},
            {"proxy": "http://47.91.115.179:8080", "weight": 1.0, "failures": 0},
            {"proxy": "http://47.91.120.190:8089", "weight": 1.0, "failures": 0},
            {"proxy": "http://47.104.28.135:80", "weight": 1.0, "failures": 0},
            {"proxy": "http://47.104.160.169:443", "weight": 1.0, "failures": 0},
            {"proxy": "http://47.108.159.113:8443", "weight": 1.0, "failures": 0},
            {"proxy": "http://47.109.83.196:8081", "weight": 1.0, "failures": 0},
            {"proxy": "http://47.119.22.156:80", "weight": 1.0, "failures": 0},
            {"proxy": "http://47.121.129.129:8443", "weight": 1.0, "failures": 0},
            {"proxy": "http://47.121.182.36:3128", "weight": 1.0, "failures": 0},
            {"proxy": "http://47.121.183.107:8080", "weight": 1.0, "failures": 0},
            {"proxy": "http://47.122.60.73:8080", "weight": 1.0, "failures": 0},
            {"proxy": "http://47.122.64.36:8080", "weight": 1.0, "failures": 0},
            {"proxy": "http://47.122.65.32:8081", "weight": 1.0, "failures": 0},
            {"proxy": "http://47.238.128.246:3128", "weight": 1.0, "failures": 0},
            {"proxy": "http://50.114.33.143:8080", "weight": 1.0, "failures": 0},
            {"proxy": "http://89.58.8.250:80", "weight": 1.0, "failures": 0},
            {"proxy": "http://89.58.28.110:80", "weight": 1.0, "failures": 0},
            {"proxy": "http://89.58.55.193:80", "weight": 1.0, "failures": 0},
            {"proxy": "http://92.255.193.113:8080", "weight": 1.0, "failures": 0},
            {"proxy": "http://101.200.158.109:8008", "weight": 1.0, "failures": 0},
            {"proxy": "http://103.86.109.38:80", "weight": 1.0, "failures": 0},
            {"proxy": "http://103.189.254.28:2222", "weight": 1.0, "failures": 0},
            {"proxy": "http://118.113.246.192:2324", "weight": 1.0, "failures": 0},
            {"proxy": "http://121.43.43.217:10007", "weight": 1.0, "failures": 0},
            {"proxy": "http://143.0.243.75:8080", "weight": 1.0, "failures": 0},
            {"proxy": "http://144.126.216.57:80", "weight": 1.0, "failures": 0},
            {"proxy": "http://149.129.226.9:1080", "weight": 1.0, "failures": 0},
            {"proxy": "http://159.65.245.255:80", "weight": 1.0, "failures": 0},
            {"proxy": "http://162.223.90.150:80", "weight": 1.0, "failures": 0},
            {"proxy": "http://178.63.237.156:80", "weight": 1.0, "failures": 0},
            {"proxy": "http://182.44.9.76:8072", "weight": 1.0, "failures": 0},
            {"proxy": "http://183.240.46.42:80", "weight": 1.0, "failures": 0},
            {"proxy": "http://203.95.198.154:8080", "weight": 1.0, "failures": 0},
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
    comment = text_model.make_short_sentence(280, tries=100) or "agreed!"
    return comment

def setup_browser(proxy):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    if proxy:
        chrome_options.add_argument(f"--proxy-server={proxy}")
    return webdriver.Chrome(options=chrome_options)

def get_freedium_url(medium_url):
    """Convert Medium URL to Freedium URL to bypass paywall."""
    return f"https://freedium.cfd/{medium_url}"

def get_temp_email():
    """Fetch a temporary email address."""
    try:
        response = requests.get(f"{TEMP_EMAIL_API}/email/format/json")
        email = response.json()['email']
        logging.info(f"Got temp email: {email}")
        return email
    except Exception as e:
        logging.error(f"Error getting temp email: {e}")
        return None

def get_signin_url(email, driver):
    """Fetch Medium sign-in URL from temp email."""
    try:
        time.sleep(5)  # Wait for email to arrive
        response = requests.get(f"{TEMP_EMAIL_API}/mail/id/{email}/format/json")
        emails = response.json()
        for email_data in emails:
            if "Medium" in email_data['subject']:
                soup = BeautifulSoup(email_data['body'], 'html.parser')
                links = soup.find_all('a')
                for link in links:
                    if "signin" in link['href']:
                        return link['href']
        logging.error("No sign-in email found")
        return None
    except Exception as e:
        logging.error(f"Error fetching sign-in email: {e}")
        return None

def login_with_email(driver, medium_url):
    """Attempt Medium login using temp email."""
    email = get_temp_email()
    if not email:
        return False
    try:
        driver.get(medium_url)
        time.sleep(2)
        signin_button = driver.find_element(By.XPATH, '//a[contains(text(), "Sign in")]')
        signin_button.click()
        time.sleep(2)
        email_input = driver.find_element(By.NAME, 'email')
        email_input.send_keys(email)
        driver.find_element(By.XPATH, '//button[contains(text(), "Continue")]').click()
        time.sleep(2)
        signin_url = get_signin_url(email, driver)
        if signin_url:
            driver.get(signin_url)
            time.sleep(5)
            logging.info("Logged in via email link")
            return True
        return False
    except Exception as e:
        logging.error(f"Email login failed: {e}")
        return False

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

def setup_browser(proxy, extension_path):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    if proxy:
        chrome_options.add_argument(f"--proxy-server={proxy}")
    chrome_options.add_extension(extension_path)  # Path to Bypass Paywalls .crx
    return webdriver.Chrome(options=chrome_options)

def login(driver, account):
    driver.get('https://medium.com/m/signin')
    time.sleep(2)
    driver.find_element(By.NAME, 'email').send_keys(account['username'])
    driver.find_element(By.XPATH, '//button[contains(text(), "Next")]').click()
    time.sleep(2)
    driver.find_element(By.NAME, 'password').send_keys(account['password'])
    driver.find_element(By.XPATH, '//button[contains(text(), "Sign in")]').click()
    time.sleep(5)  # Wait for login to complete

        # Handle CAPTCHA if present
        try:
            captcha_element = driver.find_element(By.CLASS_NAME, 'g-recaptcha')
            site_key = driver.execute_script("return document.querySelector('.g-recaptcha').dataset.sitekey;")
            if not solve_captcha(driver, site_key, STORY_URL):
                driver.quit()
                return
        except:
            logging.info("No CAPTCHA detected")

def generate_comment(text):
    """Generate a Markov chain-based comment."""
    try:
        text_model = markovify.Text(text, state_size=2)
        comment = text_model.make_short_sentence(280, tries=100) or "Great article!"
        return comment
    except:
        return "Insightful read!"

def interact_with_article(driver, article_url, use_freedium=True):
    """Interact with a Medium article."""
    url = get_freedium_url(article_url) if use_freedium else article_url
    driver.get(url)
    time.sleep(random.uniform(3, 7))

    # Fallback to email login if Freedium fails
    if not use_freedium or "paywall" in driver.page_source.lower():
        logging.info("Freedium failed, attempting email login")
        if not login_with_email(driver, article_url):
            logging.error("Could not access article")
            return

    # Simulate full read (50%) or glance (50%)
    if random.random() < 0.5:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(120, 300))  # 2-5 min
    else:
        time.sleep(random.uniform(5, 10))  # 5-10 sec

    # Clap (70% chance)
    if random.random() < 0.7:
        try:
            clap_button = driver.find_element(By.XPATH, '//button[contains(@aria-label, "clap")]')
            num_claps = random.randint(1, 50)
            for _ in range(num_claps):
                clap_button.click()
                time.sleep(0.1)
            logging.info(f"Clapped {num_claps} times on {article_url}")
        except Exception as e:
            logging.error(f"Error clapping: {e}")

    # Comment (30% chance)
    if random.random() < 0.3:
        try:
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            article_text = soup.get_text()
            comment = generate_comment(article_text)
            comment_box = driver.find_element(By.TAG_NAME, 'textarea')
            comment_box.click()
            comment_box.send_keys(comment)
            comment_box.send_keys(Keys.CONTROL, Keys.ENTER)
            logging.info(f"Commented: {comment} on {article_url}")
        except Exception as e:
            logging.error(f"Error commenting: {e}")

    # Follow next article in series (50% chance)
    try:
        next_link = driver.find_element(By.XPATH, '//a[contains(text(), "Next") or contains(text(), "Part")]')
        next_url = next_link.get_attribute('href')
        if random.random() < 0.5:
            article_queue.put(next_url)
            logging.info(f"Enqueued next article: {next_url}")
    except:
        pass # No next link found

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
        "Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
    # Add more as needed
]



def worker():
    while True:
        try:
            article_url = article_queue.get(timeout=1)
            account = random.choice(ACCOUNTS)
            proxy = random.choice(PROXY_POOL) if PROXY_POOL else None
            driver = setup_browser(proxy, '/path/to/bypass_paywalls.crx')
            try:
                login(driver, account)
                interact_with_article(driver, article_url)
            finally:
                driver.quit()
            article_queue.task_done()
        except queue.Empty:
            break
        except Exception as e:
            logging.error(f"Worker error: {e}")

# Start threads
NUM_THREADS = 3
threads = []
for _ in range(NUM_THREADS):
    t = threading.Thread(target=worker)
    t.start()
    threads.append(t)

# Wait for all threads to finish
for t in threads:
    t.join()

logging.info("Bot finished processing all articles.")

# Run bot
if __name__ == "__main__":
    NUM_THREADS = 3
    threads = []
    for _ in range(NUM_THREADS):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    logging.info("Bot finished processing all articles.")
    