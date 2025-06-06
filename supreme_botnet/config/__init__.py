### supreme_botnet/__init__.py ###
"""
Supreme Botnet Framework
Advanced automation toolkit for web platforms.
"""

__version__ = "4.0.0"
__author__ = "whispr.dev"

PROXY_SOURCES = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://www.proxy-list.download/api/v1/get?type=http",
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=1000&country=all"
]

CHECK_INTERVAL = 300  # seconds between proxy refresh


