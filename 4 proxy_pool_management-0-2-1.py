###############################
managing a pool of proxies 
# 
############################### 
1. Round-Robin Selection
# 
# proxies = ["http://proxy1:port", "http://proxy2:port", "http://proxy3:port"]
# proxy_index = 0
# 
# def get_next_proxy():
#     global proxy_index
#     proxy = proxies[proxy_index]
#     proxy_index = (proxy_index + 1) % len(proxies)
#     return proxy
# 
# def send_request(url):
#     proxy = get_next_proxy()
#     proxies_dict = {"http": proxy, "https": proxy}
#    
#    try:
#        response = requests.get(url, proxies=proxies_dict)
#        print(f"Request sent via {proxy}, status code: {response.status_code}")
#    except requests.exceptions.RequestException as e:
#        print(f"Request failed: {e}")
#
# # Example usage
# for _ in range(10):
#      send_request("http://example.com")
# 
################################
2. Weighted Selection

import random

# Proxies with their associated weights
proxies = [
    {"proxy": "http://proxy1:port", "weight": 5},
    {"proxy": "http://proxy2:port", "weight": 3},
    {"proxy": "http://proxy3:port", "weight": 2},
]

def get_weighted_proxy():
    total_weight = sum(proxy["weight"] for proxy in proxies)
    random_choice = random.uniform(0, total_weight)
    cumulative_weight = 0
    for proxy in proxies:
        cumulative_weight += proxy["weight"]
        if random_choice <= cumulative_weight:
            return proxy["proxy"]

def send_request(url):
    proxy = get_weighted_proxy()
    proxies_dict = {"http": proxy, "https": proxy}
    
    try:
        response = requests.get(url, proxies=proxies_dict)
        print(f"Request sent via {proxy}, status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

# Example usage
for _ in range(10):
    send_request("http://example.com")


#################################################
3. Proxy Pool Management System

import random

class ProxyPool:
    def __init__(self):
        self.proxies = [
            {"proxy": "http://proxy1:port", "weight": 5, "failures": 0},
            {"proxy": "http://proxy2:port", "weight": 3, "failures": 0},
            {"proxy": "http://proxy3:port", "weight": 2, "failures": 0},
        ]
        self.max_failures = 3
    
    def get_proxy(self):
        # Perform a weighted random selection
        total_weight = sum(proxy["weight"] for proxy in self.proxies)
        random_choice = random.uniform(0, total_weight)
        cumulative_weight = 0
        for proxy in self.proxies:
            cumulative_weight += proxy["weight"]
            if random_choice <= cumulative_weight:
                return proxy["proxy"]

    def report_failure(self, proxy_url):
        for proxy in self.proxies:
            if proxy["proxy"] == proxy_url:
                proxy["failures"] += 1
                if proxy["failures"] >= self.max_failures:
                    print(f"Removing {proxy_url} due to repeated failures")
                    self.proxies.remove(proxy)
                break

    def report_success(self, proxy_url):
        for proxy in self.proxies:
            if proxy["proxy"] == proxy_url:
                proxy["failures"] = 0  # Reset failure count on success
                break

def send_request(url, proxy_pool):
    proxy = proxy_pool.get_proxy()
    proxies_dict = {"http": proxy, "https": proxy}
    
    try:
        response = requests.get(url, proxies=proxies_dict)
        print(f"Request sent via {proxy}, status code: {response.status_code}")
        proxy_pool.report_success(proxy)
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        proxy_pool.report_failure(proxy)

# Example usage
proxy_pool = ProxyPool()

for _ in range(10):
    send_request("http://example.com", proxy_pool)

# 
# Summary
# Round-Robin Selection: Simple, sequential proxy rotation. Easy to implement but doesn't account for differences in proxy performance.
# Weighted Selection: Allows for more sophisticated proxy rotation based on the relative quality of proxies. Useful when some proxies are more reliable or faster than others.
# Proxy Pool Management System: A more comprehensive and dynamic approach to managing proxies, including health checks, dynamic weighting, failover, and scaling. This is suitable for larger, more complex projects where proxy reliability and performance are critical.
# Each method has its advantages and is suitable for different scenarios, depending on the complexity of your needs and the scale of your operations.
# 