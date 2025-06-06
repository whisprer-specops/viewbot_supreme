### core/user_agent.py ###

import random

class UserAgentManager:
    """
    Manages and provides diverse user agent strings for browser fingerprinting.
    """
    
    def __init__(self):
        """Initialize with a diverse set of modern user agents."""
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.113 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
            "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.116 Mobile Safari/537.362",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:125.0) Gecko/20100101 Firefox/125.0",
            "Mozilla/5.0 (Linux; Android 14; Samsung Galaxy S24 Ultra) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.99 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; OnePlus 11 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.87 Mobile Safari/537.36"
        ]
        
    def get_random(self):
        """
        Get a random user agent string.
        
        Returns:
            str: Random user agent string
        """
        return random.choice(self.user_agents)
        
    def get_desktop(self):
        """
        Get a random desktop user agent.
        
        Returns:
            str: Random desktop user agent string
        """
        desktop_agents = [ua for ua in self.user_agents if "Android" not in ua and "iPhone" not in ua and "iPad" not in ua]
        return random.choice(desktop_agents) if desktop_agents else self.get_random()
        
    def get_mobile(self):
        """
        Get a random mobile user agent.
        
        Returns:
            str: Random mobile user agent string
        """
        mobile_agents = [ua for ua in self.user_agents if "Android" in ua or "iPhone" in ua or "iPad" in ua]
        return random.choice(mobile_agents) if mobile_agents else self.get_random()
