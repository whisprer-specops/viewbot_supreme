import os
import random
import logging

"""
Supreme Botnet Configuration

This module contains all the configuration settings for the Supreme Botnet.
Settings can be overridden via command-line arguments or environment variables.
"""

# Default configuration with reasonable values
DEFAULT_CONFIG = {
    # Target URLs
    "target_url": "https://medium.com/@cgpt/is-vibe-coding-cheating-or-the-future-of-programming-in-the-workplace-216fe9d5084d",
    "webhook_url": "https://discord.com/api/webhooks/1368210146949464214/QqgJoJOeI2qzfQjqlMCVWKgHpYqCZFGlVQ9EnugixWmwaP567xQw1w7l7DEm-pqOpP93",
    "captcha_api_key": os.getenv('2CAPTCHA_APIKEY', ''),
    
    # Threading and performance settings
    "max_concurrent_threads": 4,  
    "requests_per_thread": lambda: random.randint(20, 40),
    "delay_between_requests": lambda: random.uniform(30.0, 60.0),
    
    # Network settings
    "use_tor": False,
    "use_freedium": False,
    "prefer_email_login": True,
    "verify_ssl": False,  # Disable SSL verification for problematic proxies
    
    # Browser settings
    "browser_timeout": 90,
    "headless": True,
    
    # Interaction settings
    "read_time_min": 45,
    "read_time_max": 180,
    "clap_probability": 0.6,
    "comment_probability": 0.2,
    "follow_probability": 0.3,
    
    # Retry settings
    "max_retries": 3,
    "retry_delay": 5,
    
    # Logging
    "log_level": logging.INFO,
    "log_file": "botnet.log",
    
    # File paths
    "proxy_file": "proxies.txt",
    "account_file": "accounts.json",
    
    # Platform-specific settings
    "starting_articles": [
        "https://medium.com/the-narrative-arc/if-you-want-to-be-a-writer-maybe-read-this-first-okay-54a341d293e6"
    ],
    
    # YouTube specific
    "comment_text": "Great video! Really enjoyed this content. Keep it up!",
    "youtube_max_video_length": 600,  # in seconds
}

# Load environment variables that match config keys
def load_from_env():
    config = DEFAULT_CONFIG.copy()
    for key in config:
        env_key = f"BOTNET_{key.upper()}"
        if env_key in os.environ:
            env_value = os.environ[env_key]
            
            # Try to convert to the appropriate type
            if isinstance(config[key], bool):
                config[key] = env_value.lower() in ('true', 'yes', '1', 'y')
            elif isinstance(config[key], int):
                config[key] = int(env_value)
            elif isinstance(config[key], float):
                config[key] = float(env_value)
            else:
                config[key] = env_value
                
    return config

# Update config from command line arguments
def update_from_args(config, args):
    if args.url:
        config["target_url"] = args.url
    if args.threads:
        config["max_concurrent_threads"] = args.threads
    if args.requests:
        config["requests_per_thread"] = lambda: args.requests
    if args.delay:
        config["delay_between_requests"] = lambda: args.delay
    if args.tor:
        config["use_tor"] = True
    if args.no_freedium:
        config["use_freedium"] = False
    if args.captcha_key:
        config["captcha_api_key"] = args.captcha_key
    if args.webhook:
        config["webhook_url"] = args.webhook
    if args.log_level:
        config["log_level"] = getattr(logging, args.log_level)
    if args.proxy_file:
        config["proxy_file"] = args.proxy_file
    if args.account_file:
        config["account_file"] = args.account_file
    if args.headless is not None:
        config["headless"] = args.headless
        
    return config

# Get the complete configuration
def get_config(args=None):
    config = load_from_env()
    
    if args:
        config = update_from_args(config, args)
        
    return config