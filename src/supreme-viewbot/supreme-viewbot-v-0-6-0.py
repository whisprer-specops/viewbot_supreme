import threading
import queue
import random
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO)

# List of Medium accounts
ACCOUNTS = [
    {'username': 'user1@example.com', 'password': 'pass1'},
    {'username': 'user2@example.com', 'password': 'pass2'},
    # Add more accounts here
]

# Proxy pool (example, replace with actual proxies)
PROXY_POOL = ['http://proxy1:port', 'http://proxy2:port']

# Article queue
article_queue = queue.Queue()

# Seed with starting article
starting_articles = ['https://medium.com/@author/sample-article']
for article in starting_articles:
    article_queue.put(article)

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

def generate_comment(text):
    # Simplified Markov chain comment generator (replace with your implementation)
    words = text.split()
    if len(words) > 10:
        start = random.randint(0, len(words) - 10)
        return ' '.join(words[start:start + 10])
    return "I'm surprised how simple the math is to understand", "fascinating", "intriguing", "though provoking", "i like the ending", 

def interact_with_article(driver, article_url):
    driver.get(article_url)
    time.sleep(5)  # Wait for page to load

    # Simulate full read or glance
    if random.random() < 0.5:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(120, 300))  # 2-5 minutes
    else:
        time.sleep(random.uniform(5, 10))  # 5-10 seconds

    # Clap with 70% probability
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

    # Comment with 30% probability
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

    # Look for next article in series
    try:
        next_link = driver.find_element(By.XPATH, '//a[contains(text(), "Next") or contains(text(), "Part")]')
        next_url = next_link.get_attribute('href')
        if random.random() < 0.5:
            article_queue.put(next_url)
            logging.info(f"Enqueued next article: {next_url}")
    except:
        pass  # No next link found

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