import asyncio
import sys
import os
from rapidproxyscan import run_scanner, get_args, run_speed_test, clean_old_files, analyze_proxy_stats, setup_auto_update

# =============================================================================
# GENERAL SETTINGS
# =============================================================================

# How often to check for new proxies (in seconds)
CHECK_INTERVAL = 30

# Maximum concurrent connections for proxy testing
CONNECTION_LIMIT = 1250

# Number of validation tests per proxy
VALIDATION_ROUNDS = 3

# Validation mode: 'any', 'majority', or 'all'
# - 'any': Consider proxy valid if any test passes
# - 'majority': Consider proxy valid if most tests pass
# - 'all': Consider proxy valid only if all tests pass
VALIDATION_MODE = 'majority'

# Connection timeout in seconds
TIMEOUT = 5.0

# Enable verbose logging
VERBOSE = True

# Check proxy anonymity level
CHECK_ANONYMITY = True

# Force fetch proxy lists on each cycle
FORCE_FETCH = False

# Run once and exit (useful for cron jobs)
SINGLE_RUN = False

# =============================================================================
# PROXY SOURCES
# =============================================================================

# List of proxy sources to check
# You can add or remove sources as needed
PROXY_SOURCES = [
    # Free proxy lists
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

# =============================================================================
# OPTIMIZER SETTINGS
# =============================================================================

# Number of concurrent workers for testing proxies
PROXY_TEST_WORKERS = CONNECTION_LIMIT # Sensible default to match connection limit

# Interval in seconds to fetch new proxy lists
PROXY_FETCH_INTERVAL = CHECK_INTERVAL * 2 # Fetch less frequently than checking

# Timeout for individual proxy tests
PROXY_TEST_TIMEOUT = TIMEOUT

# Number of retries for a failed proxy test
PROXY_TEST_RETRIES = VALIDATION_ROUNDS # Use validation rounds as a sensible default

# Maximum number of proxies to store in memory
MAX_PROXIES_TO_KEEP = 10000

# Minimum interval before re-testing a proxy
PROXY_REFRESH_MIN_INTERVAL = 300 # 5 minutes

# URL to test proxy connectivity and anonymity
TEST_URL = "http://ip-api.com/json" # A simple API that returns IP info

# Interval in seconds to export verified proxies
EXPORT_INTERVAL = 300 # 5 minutes

# Max attempts to fetch a proxy list
MAX_FETCH_ATTEMPTS = 5

# Delay between fetch retries
FETCH_RETRY_DELAY = 5

# =============================================================================
# MAIN EXECUTION BLOCK
# =============================================================================

if __name__ == "__main__":
    # This block allows config.py to be run standalone for utility functions
    # or to directly start the scanner with its configured settings.

    # Handle utility functions directly from command line
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
    
    # Otherwise, prepare to run the scanner
    print("Loading configuration...")
    
    # Import the actual scanner here to avoid circular imports
    try:
        # If running as standalone config
        # Get configuration (this will parse CLI args and use config.py defaults)
        args = get_args()
        
        # Run the scanner with config
        print("Starting RapidProxyScan with configuration from config.py")
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
            # Pass all additional arguments required by run_scanner
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
    except ImportError:
        print("Error: rapidproxyscan.py not found. Make sure it's in the same directory.")
    except Exception as e:
        print(f"An error occurred: {e}")