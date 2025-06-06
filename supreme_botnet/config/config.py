# config.py
import asyncio
import sys
import os
from rapidproxyscan import run_scanner, get_args, run_speed_test, clean_old_files, analyze_proxy_stats, setup_auto_update

# General Settings
CHECK_INTERVAL = 30
CONNECTION_LIMIT = 1250
VALIDATION_ROUNDS = 3
VALIDATION_MODE = 'majority'
TIMEOUT = 5.0
VERBOSE = True
CHECK_ANONYMITY = True
FORCE_FETCH = False
SINGLE_RUN = False

# Proxy Sources
PROXY_SOURCES = [
    'https://www.freeproxylists.net/',
    'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
    'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt',
    'https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt',
    'https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt',
    'https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt',
    'https://raw.githubusercontent.com/opsxcq/proxy-list/master/list.txt',
    'https://raw.githubusercontent.com/proxy4free/proxy-list/main/http.txt',
    'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all',
    'https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt'
]

# Optimizer Settings
PROXY_TEST_WORKERS = CONNECTION_LIMIT
PROXY_FETCH_INTERVAL = CHECK_INTERVAL * 2
PROXY_TEST_TIMEOUT = TIMEOUT
PROXY_TEST_RETRIES = VALIDATION_ROUNDS
MAX_PROXIES_TO_KEEP = 10000
PROXY_REFRESH_MIN_INTERVAL = 300
TEST_URL = "http://ip-api.com/json"
EXPORT_INTERVAL = 300
MAX_FETCH_ATTEMPTS = 5
FETCH_RETRY_DELAY = 5

# Vote Boosting Settings
VOTE_ENDPOINT = None  # e.g., "https://example.com/api/vote"
VOTE_PAYLOAD = {}  # e.g., {"vote_id": "123", "option": "A"}
VOTE_AUTH_REQUIRED = False
VOTE_DELAY_MIN = 1.0
VOTE_DELAY_MAX = 5.0
VOTE_PROBABILITY = 0.9
VOTE_MAX_PER_PROXY = 10
VOTE_MAX_PER_ACCOUNT = 5
VOTE_BROWSER_BASED = False  # Set to True for browser-based voting
VOTE_LOGIN_URL = None  # e.g., "https://example.com/login"
VOTE_CSRF_TOKEN_SELECTOR = None  # CSS selector for CSRF token if needed

# Account Settings
ACCOUNT_FILE = "my_accounts.json"
AUTO_CREATE_ACCOUNTS = False
SIGNUP_URL = None  # e.g., "https://example.com/signup"
SIGNUP_PAYLOAD = {}  # e.g., {"email": "{email}", "password": "hunter2"}

# CAPTCHA Settings
CAPTCHA_API_KEY = None  # 2CAPTCHA API key
CAPTCHA_ENABLED = False
CAPTCHA_SITE_KEY = None  # reCAPTCHA site key
CAPTCHA_PAGE_URL = None  # Page URL for CAPTCHA

# Email Settings
TEMP_EMAIL_API = "https://api.temp-mail.org"
EMAIL_TIMEOUT = 180
EMAIL_INTERVAL = 5

# Browser Settings
BROWSER_HEADLESS = True
BROWSER_TIMEOUT = 90
VERIFY_SSL = True
USE_TOR = False
USE_EXTENSION = False
EXTENSION_PATH = None

# Webhook Settings
DISCORD_BOT_TOKEN = None
DISCORD_CHANNEL_ID = None
WEBHOOK_URL = None

def get_config(args):
    """Convert CLI args to config dict, merging with defaults."""
    config = {
        "check_interval": CHECK_INTERVAL,
        "connection_limit": CONNECTION_LIMIT,
        "validation_rounds": VALIDATION_ROUNDS,
        "validation_mode": VALIDATION_MODE,
        "timeout": TIMEOUT,
        "verbose": VERBOSE,
        "check_anonymity": CHECK_ANONYMITY,
        "force_fetch": FORCE_FETCH,
        "single_run": SINGLE_RUN,
        "proxy_sources": PROXY_SOURCES,
        "proxy_test_workers": PROXY_TEST_WORKERS,
        "proxy_fetch_interval": PROXY_FETCH_INTERVAL,
        "proxy_test_timeout": PROXY_TEST_TIMEOUT,
        "proxy_test_retries": PROXY_TEST_RETRIES,
        "max_proxies_to_keep": MAX_PROXIES_TO_KEEP,
        "proxy_refresh_min_interval": PROXY_REFRESH_MIN_INTERVAL,
        "test_url": TEST_URL,
        "export_interval": EXPORT_INTERVAL,
        "max_fetch_attempts": MAX_FETCH_ATTEMPTS,
        "fetch_retry_delay": FETCH_RETRY_DELAY,
        "vote_endpoint": args.vote_endpoint or VOTE_ENDPOINT,
        "vote_payload": args.vote_payload or VOTE_PAYLOAD,
        "vote_auth_required": VOTE_AUTH_REQUIRED,
        "vote_delay_min": args.delay or VOTE_DELAY_MIN,
        "vote_delay_max": VOTE_DELAY_MAX,
        "vote_probability": VOTE_PROBABILITY,
        "vote_max_per_proxy": VOTE_MAX_PER_PROXY,
        "vote_max_per_account": VOTE_MAX_PER_ACCOUNT,
        "vote_browser_based": VOTE_BROWSER_BASED,
        "vote_login_url": VOTE_LOGIN_URL,
        "vote_csrf_token_selector": VOTE_CSRF_TOKEN_SELECTOR,
        "account_file": args.account_file or ACCOUNT_FILE,
        "auto_create_accounts": AUTO_CREATE_ACCOUNTS,
        "signup_url": SIGNUP_URL,
        "signup_payload": SIGNUP_PAYLOAD,
        "captcha_api_key": CAPTCHA_API_KEY,
        "captcha_enabled": CAPTCHA_ENABLED,
        "captcha_site_key": CAPTCHA_SITE_KEY,
        "captcha_page_url": CAPTCHA_PAGE_URL,
        "temp_email_api": TEMP_EMAIL_API,
        "email_timeout": EMAIL_TIMEOUT,
        "email_interval": EMAIL_INTERVAL,
        "browser_headless": BROWSER_HEADLESS,
        "browser_timeout": BROWSER_TIMEOUT,
        "verify_ssl": args.verify_ssl if args.verify_ssl is not None else VERIFY_SSL,
        "use_tor": USE_TOR,
        "use_extension": USE_EXTENSION,
        "extension_path": EXTENSION_PATH,
        "discord_bot_token": args.discord_token or DISCORD_BOT_TOKEN,
        "discord_channel_id": args.discord_channel or DISCORD_CHANNEL_ID,
        "webhook_url": args.webhook or WEBHOOK_URL,
        "log_level": args.log_level,
    }
    return config

if __name__ == "__main__":
    # Handle utility functions
    if len(sys.argv) > 1:
        if "--speed-test" in sys.argv:
            idx = sys.argv.index("--speed-test")
            if idx + 1 < len(sys.argv):
                run_speed_test(sys.argv[idx + 1])
            else:
                print("Error: --speed-test requires a file path")
            sys.exit(0)
        if "--clean-old" in sys.argv:
            clean_old_files()
            sys.exit(0)
        if "--analyze" in sys.argv:
            analyze_proxy_stats()
            sys.exit(0)
        if "--setup-auto-update" in sys.argv:
            setup_auto_update()
            sys.exit(0)

    # Run scanner with config
    print("Starting RapidProxyScan with configuration from config.py")
    args = get_args()
    asyncio.run(run_scanner(
        check_interval=args.check_interval,
        connection_limit=args.connection_limit,
        validation_rounds=args.validation_rounds,
        validation_mode=args.validation_mode,
        timeout=args.timeout,
        check_anonymity=args.check_anonymity,
        force_fetch=args.force_fetch,
        verbose=args.verbose,
        single_run=args.single_run,
        proxy_sources=args.proxy_sources,
        proxy_test_workers=args.proxy_test_workers,
        proxy_fetch_interval=args.proxy_fetch_interval,
        proxy_test_timeout=args.proxy_test_timeout,
        proxy_test_retries=args.proxy_test_retries,
        max_proxies_to_keep=args.max_proxies_to_keep,
        proxy_refresh_min_interval=args.proxy_refresh_min_interval,
        test_url=args.test_url,
        export_interval=args.export_interval,
        max_fetch_attempts=args.max_fetch_attempts,
        fetch_retry_delay=args.fetch_retry_delay
    ))

    config.TEST_ENDPOINTS = OPTIMIZED_TEST_ENDPOINTS