# How to - rotating proxies with both IPV4 and IPV6 mixtures...
# Rotating Proxies: You have a pool of both IPv6 and IPv4 proxies.
# The viewbot rotates through these proxies, choosing the appropriate type
# (IPv6 or IPv4) based on the availability and success of the connection.

ipv6_proxies = [
    "http://ipv6_proxy1:port",
    "http://ipv6_proxy2:port",
    # Add more IPv6 proxies here
]

ipv4_proxies = [
    "http://ipv4_proxy1:port",
    "http://ipv4_proxy2:port",
    # Add more IPv4 proxies here
]

# 
# 
# Implement a function that tries to send a request using an IPv6 proxy first. If it fails, it retries with an IPv4 proxy.
# 
# 

import requests
import random

def send_request(url):
    ipv6_proxy = random.choice(ipv6_proxies)
    ipv4_proxy = random.choice(ipv4_proxies)

    proxies = {
        "http": ipv6_proxy,
        "https": ipv6_proxy,
    }

    try:
        response = requests.get(url, proxies=proxies, timeout=5)
        print(f"Request sent via IPv6, status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"IPv6 failed: {e}. Retrying with IPv4...")
        
        proxies = {
            "http": ipv4_proxy,
            "https": ipv4_proxy,
        }

        try:
            response = requests.get(url, proxies=proxies, timeout=5)
            print(f"Request sent via IPv4, status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"IPv4 also failed: {e}")

# Example usage
for _ in range(10):  # Send 10 requests
    send_request("http://example.com")
