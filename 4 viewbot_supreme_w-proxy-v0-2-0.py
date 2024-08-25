import requests
import threading
import time

# Configuration
URL = "http://example.com"  # Replace with the target URL
NUM_THREADS = 10  # Number of concurrent threads
REQUESTS_PER_THREAD = 100  # Number of requests per thread
DELAY_BETWEEN_REQUESTS = 0.1  # Delay between requests in seconds

# Proxy Configuration
PROXY = "http://proxy-server.com:port"  # Replace with your proxy server URL

def send_request():
    proxies = {
        "http": PROXY,
        "https": PROXY,
    }
    
    for _ in range(REQUESTS_PER_THREAD):
        try:
            response = requests.get(URL, proxies=proxies)
            print(f"Request sent, status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
        time.sleep(DELAY_BETWEEN_REQUESTS)

def main():
    threads = []
    for _ in range(NUM_THREADS):
        thread = threading.Thread(target=send_request)
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()