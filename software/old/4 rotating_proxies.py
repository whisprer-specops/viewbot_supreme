import requests

# Configuration
URL = "http://example.com"
PROXY = "http://user:password@rotating.smartproxy.com:10000"  # Replace with your rotating proxy details

def send_request():
    proxies = {
        "http": PROXY,
        "https": PROXY,
    }
    
    response = requests.get(URL, proxies=proxies)
    print(f"Request sent, status code: {response.status_code}")

for _ in range(10):  # Sending 10 requests as an example
    send_request()

# these aare two ways of implementing a bot to operate using a rotating proxy
# top one assumes the rotation management etc. is auto done by proxy
# bottom one actually lets the bot itself do rotation from a list
# i have instructions how to do top w/ digital ocean
# top is preferred

import requests
import random

# Configuration
URL = "http://example.com"
PROXIES = [
    "http://proxy1.com:port",
    "http://proxy2.com:port",
    "http://proxy3.com:port",
    # Add more proxies to the list
]

def send_request():
    proxy = random.choice(PROXIES)
    proxies = {
        "http": proxy,
        "https": proxy,
    }
    
    response = requests.get(URL, proxies=proxies)
    print(f"Request sent through {proxy}, status code: {response.status_code}")

for _ in range(10):  # Sending 10 requests as an example
    send_request()