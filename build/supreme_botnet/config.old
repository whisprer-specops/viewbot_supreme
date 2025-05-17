"""
RapidProxyScan - Configuration File
==================================

This file lets you customize RapidProxyScan without editing the main code.
Simply change the settings below to match your preferences.
"""

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
    'https://free-proxy-list.net/',
    'https://www.sslproxies.org/',
    'https://www.us-proxy.org/',
    'https://free-proxy-list.net/uk-proxy.html',
    'https://www.proxy-list.download/api/v1/get',
    'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all',
    'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
    'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt',
    'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list.txt',
    'https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies.txt',
    'https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt'
]

# Add any custom proxy sources here
CUSTOM_PROXY_SOURCES = [
    # Add your own sources here
    # 'https://example.com/proxies.txt',
]

# Combine all sources
ALL_PROXY_SOURCES = PROXY_SOURCES + CUSTOM_PROXY_SOURCES

# =============================================================================
# TEST ENDPOINTS
# =============================================================================

# URLs to use for testing proxies
# These should be lightweight and fast-responding endpoints
TEST_ENDPOINTS = [
    'http://httpbin.org/ip',
    'https://api.ipify.org/?format=json',
    'http://ip-api.com/json/',
    'https://www.cloudflare.com/cdn-cgi/trace'
]

# =============================================================================
# OUTPUT SETTINGS
# =============================================================================

# Directory for output files (leave empty for current directory)
OUTPUT_DIR = ''

# Prefix for output filenames
OUTPUT_PREFIX = 'proxies'

# Export formats (set to True to enable)
EXPORT_TXT = True
EXPORT_CSV = True
EXPORT_JSON = True

# =============================================================================
# ELITE PROXY SWITCHER INTEGRATION
# =============================================================================

# Path to Elite Proxy Switcher executable
EPS_PATH = r"C:\Elite Proxy Switcher\EPS.exe"

# Enable automatic import to Elite Proxy Switcher
AUTO_IMPORT_TO_EPS = False

# =============================================================================
# ADVANCED SETTINGS
# =============================================================================

# Timeout ranges for different proxy speeds (in seconds)
TIMEOUT_RANGES = {
    'fast': {'connect': 1.0, 'read': 3.0},
    'medium': {'connect': 2.0, 'read': 5.0},
    'slow': {'connect': 3.0, 'read': 8.0}
}

# DNS cache TTL in seconds
DNS_CACHE_TTL = 300

# User agents for requests
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
]

# =============================================================================
# LOAD CONFIG AND CONVERT TO COMMAND LINE ARGS
# =============================================================================

def get_args():
    """Convert config settings to command line args"""
    import argparse
    
    parser = argparse.ArgumentParser(description='RapidProxyScan - High Performance Proxy Scanner')
    
    # Add all arguments
    parser.add_argument('--interval', dest='check_interval', type=int, default=CHECK_INTERVAL,
                        help=f'Interval between scan cycles in seconds (default: {CHECK_INTERVAL})')
    
    parser.add_argument('--connections', dest='connection_limit', type=int, default=CONNECTION_LIMIT,
                        help=f'Maximum number of concurrent connections (default: {CONNECTION_LIMIT})')
    
    parser.add_argument('--validation-rounds', dest='validation_rounds', type=int, default=VALIDATION_ROUNDS,
                        help=f'Number of validation rounds for each proxy (default: {VALIDATION_ROUNDS})')
    
    parser.add_argument('--validation-mode', dest='validation_mode', 
                        choices=['any', 'majority', 'all'], default=VALIDATION_MODE,
                        help=f'Validation success criteria (default: {VALIDATION_MODE})')
    
    parser.add_argument('--timeout', dest='timeout', type=float, default=TIMEOUT,
                        help=f'Timeout for proxy connections in seconds (default: {TIMEOUT})')
    
    parser.add_argument('--anonymity', dest='check_anonymity', action='store_true', default=CHECK_ANONYMITY,
                        help='Enable proxy anonymity checking')
    
    parser.add_argument('--force-fetch', dest='force_fetch', action='store_true', default=FORCE_FETCH,
                        help='Force fetch proxy lists on each cycle')
    
    parser.add_argument('--verbose', dest='verbose', action='store_true', default=VERBOSE,
                        help='Enable verbose output')
    
    parser.add_argument('--single-run', dest='single_run', action='store_true', default=SINGLE_RUN,
                        help='Run once and exit')
    
    parser.add_argument('--output-dir', dest='output_dir', type=str, default=OUTPUT_DIR,
                        help='Directory for output files')
    
    parser.add_argument('--output-prefix', dest='output_prefix', type=str, default=OUTPUT_PREFIX,
                        help='Prefix for output filenames')
    
    parser.add_argument('--export-txt', dest='export_txt', action='store_true', default=EXPORT_TXT,
                        help='Export results as text file')
    
    parser.add_argument('--export-csv', dest='export_csv', action='store_true', default=EXPORT_CSV,
                        help='Export results as CSV file')
    
    parser.add_argument('--export-json', dest='export_json', action='store_true', default=EXPORT_JSON,
                        help='Export results as JSON file')
    
    parser.add_argument('--eps-import', dest='eps_import', action='store_true', default=AUTO_IMPORT_TO_EPS,
                        help='Import results to Elite Proxy Switcher')
    
    parser.add_argument('--eps-path', dest='eps_path', type=str, default=EPS_PATH,
                        help='Path to Elite Proxy Switcher executable')
    
    # Parse args from command line (these will override config file settings)
    args = parser.parse_args()
    
    # Set additional attributes not directly exposed as command line args
    args.proxy_sources = ALL_PROXY_SOURCES
    args.test_endpoints = TEST_ENDPOINTS
    args.timeout_ranges = TIMEOUT_RANGES
    args.dns_cache_ttl = DNS_CACHE_TTL
    args.user_agents = USER_AGENTS
    
    return args

# =============================================================================
# CUSTOM PROXY SOURCES PARSER
# =============================================================================

def parse_elite_proxy_switcher_file(file_path):
    """Parse proxies from an Elite Proxy Switcher export file"""
    import re
    
    proxies = []
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
            # Extract proxies using regex pattern
            # EPS format may vary, adjust pattern as needed
            pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d+)'
            matches = re.findall(pattern, content)
            
            for host, port in matches:
                try:
                    port = int(port)
                    if 1 <= port <= 65535:
                        proxies.append(f"{host}:{port}")
                except ValueError:
                    continue
    except Exception as e:
        print(f"Error parsing Elite Proxy Switcher file: {e}")
    
    return proxies

# =============================================================================
# ELITE PROXY SWITCHER INTEGRATION
# =============================================================================

def import_to_elite_proxy_switcher(proxy_file):
    """Import proxies to Elite Proxy Switcher"""
    import subprocess
    import os
    
    if not os.path.exists(EPS_PATH):
        print(f"Elite Proxy Switcher not found at: {EPS_PATH}")
        return False
    
    try:
        # Run EPS with import parameter
        # Adjust command line options based on EPS documentation
        subprocess.run([EPS_PATH, f"/import:{os.path.abspath(proxy_file)}"])
        return True
    except Exception as e:
        print(f"Failed to import to Elite Proxy Switcher: {e}")
        return False

# =============================================================================
# AUTO-UPDATE FUNCTIONALITY
# =============================================================================

def setup_auto_update():
    """Setup automatic updates using Windows Task Scheduler"""
    import subprocess
    import sys
    import os
    
    print("Setting up automatic updates...")
    
    # Get the full path to the Python script
    script_path = os.path.abspath(sys.argv[0])
    python_exe = sys.executable
    
    try:
        # Create a scheduled task (Windows example)
        task_name = "RapidProxyScan_Hourly"
        
        # Build the command to run the script with --single-run
        command = f'"{python_exe}" "{script_path}" --single-run'
        
        # Schedule the task to run hourly
        subprocess.run([
            "schtasks", "/create", "/tn", task_name, 
            "/tr", command,
            "/sc", "hourly",  # Schedule: hourly
            "/mo", "1",       # Every 1 hour
            "/f"              # Force (overwrite if exists)
        ])
        
        print(f"Automatic updates scheduled as task: {task_name}")
        return True
    
    except Exception as e:
        print(f"Failed to setup automatic updates: {e}")
        print("You may need administrator privileges.")
        return False

# =============================================================================
# PROXY SPEED TEST UTILITY
# =============================================================================

def run_speed_test(proxy_list_file):
    """Run speed tests on a list of proxies"""
    import time
    import asyncio
    import aiohttp
    import json
    from datetime import datetime
    
    async def test_proxy_speed(session, proxy_url):
        start_time = time.time()
        try:
            async with session.get(
                'http://httpbin.org/ip',
                proxy=proxy_url,
                timeout=aiohttp.ClientTimeout(total=10),
                ssl=False
            ) as response:
                if response.status != 200:
                    return proxy_url, None
                
                body = await response.text()
                response_time = (time.time() - start_time) * 1000  # ms
                return proxy_url, response_time
        except:
            return proxy_url, None
    
    async def run_tests(proxies):
        connector = aiohttp.TCPConnector(limit=50, ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            for proxy in proxies:
                # Add http:// prefix if not present
                if not proxy.startswith('http'):
                    proxy = f"http://{proxy}"
                
                tasks.append(test_proxy_speed(session, proxy))
            
            results = await asyncio.gather(*tasks)
            return {proxy: time for proxy, time in results if time is not None}
    
    # Load proxies from file
    try:
        with open(proxy_list_file, 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error loading proxy list: {e}")
        return
    
    print(f"Running speed test on {len(proxies)} proxies...")
    
    # Run the speed tests
    speed_results = asyncio.run(run_tests(proxies))
    
    # Sort by speed
    sorted_results = sorted(speed_results.items(), key=lambda x: x[1])
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    result_file = f"speed_test_{timestamp}.json"
    
    with open(result_file, 'w') as f:
        result_data = {
            'timestamp': timestamp,
            'total_proxies': len(proxies),
            'working_proxies': len(speed_results),
            'results': [
                {'proxy': proxy, 'response_time_ms': time}
                for proxy, time in sorted_results
            ]
        }
        json.dump(result_data, f, indent=2)
    
    # Print summary
    print(f"\nSpeed Test Results:")
    print(f"Total proxies tested: {len(proxies)}")
    print(f"Working proxies: {len(speed_results)} ({len(speed_results)/len(proxies)*100:.1f}%)")
    
    if sorted_results:
        print("\nTop 5 fastest proxies:")
        for proxy, time in sorted_results[:5]:
            print(f"  {proxy}: {time:.2f}ms")
    
    print(f"\nDetailed results saved to: {result_file}")

# =============================================================================
# ADDITIONAL UTILITIES
# =============================================================================

def clean_old_files(max_age_days=7):
    """Clean up old proxy files"""
    import os
    import time
    from datetime import datetime
    
    print("Cleaning up old proxy files...")
    
    # Calculate cutoff time
    cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
    
    # Find and delete old files
    count = 0
    for file in os.listdir('.'):
        if any(file.startswith(prefix) for prefix in [
            'working_proxies_', 'proxies_detailed_', 'speed_test_'
        ]):
            if os.path.getmtime(file) < cutoff_time:
                try:
                    os.remove(file)
                    count += 1
                except:
                    pass
    
    print(f"Removed {count} old files")

def analyze_proxy_stats():
    """Analyze proxy statistics over time"""
    import os
    import json
    import matplotlib.pyplot as plt
    from datetime import datetime
    
    # Find all JSON result files
    result_files = [f for f in os.listdir('.') if f.startswith('proxies_detailed_') and f.endswith('.json')]
    
    if not result_files:
        print("No result files found for analysis")
        return
    
    # Extract data
    data_points = []
    for file in result_files:
        try:
            # Extract timestamp from filename
            timestamp_str = file.replace('proxies_detailed_', '').replace('.json', '')
            timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
            
            # Load data
            with open(file, 'r') as f:
                proxies = json.load(f)
            
            # Calculate stats
            total = len(proxies)
            avg_speed = sum(p.get('avg_response_time', 0) for p in proxies) / total if total else 0
            
            # Count by country
            countries = {}
            for proxy in proxies:
                country = proxy.get('country', 'Unknown')
                countries[country] = countries.get(country, 0) + 1
            
            data_points.append({
                'timestamp': timestamp,
                'total': total,
                'avg_speed': avg_speed,
                'countries': countries
            })
        except:
            continue
    
    if not data_points:
        print("No valid data found for analysis")
        return
    
    # Sort by timestamp
    data_points.sort(key=lambda x: x['timestamp'])
    
    # Create plots (requires matplotlib)
    try:
        # Plot total proxies over time
        plt.figure(figsize=(10, 6))
        plt.plot([d['timestamp'] for d in data_points], [d['total'] for d in data_points], 'b-')
        plt.title('Working Proxies Over Time')
        plt.xlabel('Date')
        plt.ylabel('Number of Working Proxies')
        plt.grid(True)
        plt.savefig('proxy_trend.png')
        
        # Plot average speed over time
        plt.figure(figsize=(10, 6))
        plt.plot([d['timestamp'] for d in data_points], [d['avg_speed'] for d in data_points], 'r-')
        plt.title('Average Proxy Response Time Over Time')
        plt.xlabel('Date')
        plt.ylabel('Response Time (ms)')
        plt.grid(True)
        plt.savefig('speed_trend.png')
        
        print("Analysis complete. Graphs saved as proxy_trend.png and speed_trend.png")
    except Exception as e:
        print(f"Error creating analysis plots: {e}")
        print("Make sure matplotlib is installed: pip install matplotlib")

# =============================================================================
# COMMAND LINE INTERFACE UTILITY
# =============================================================================

def show_help():
    """Show help information"""
    print("""
RapidProxyScan - High Performance Proxy Scanner
==============================================

Usage:
  python rapidproxyscan.py [options]

Options:
  --interval SECONDS       Interval between scan cycles (default: 30)
  --connections LIMIT      Maximum concurrent connections (default: 200)
  --validation-rounds N    Number of validation tests per proxy (default: 3)
  --validation-mode MODE   Success criteria: any, majority, all (default: majority)
  --timeout SECONDS        Connection timeout (default: 5.0)
  --anonymity              Enable proxy anonymity checking
  --force-fetch            Force fetch proxy lists on each cycle
  --verbose                Show detailed logs
  --single-run             Run once and exit
  --output-dir DIR         Directory for output files
  --output-prefix PREFIX   Prefix for output filenames
  --export-txt             Export results as text file
  --export-csv             Export results as CSV file
  --export-json            Export results as JSON file
  --eps-import             Import results to Elite Proxy Switcher
  --eps-path PATH          Path to Elite Proxy Switcher executable

Additional utilities:
  --speed-test FILE        Run speed test on proxies in FILE
  --clean-old              Clean up old proxy files
  --analyze                Analyze proxy statistics over time
  --setup-auto-update      Setup automatic updates using task scheduler
  --help                   Show this help message

Examples:
  python rapidproxyscan.py --interval 60 --connections 300 --validation-rounds 2
  python rapidproxyscan.py --single-run --export-txt --export-json
  python rapidproxyscan.py --speed-test working_proxies.txt
""")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    import sys
    
    # Check for utility commands
    if len(sys.argv) > 1:
        if "--help" in sys.argv or "-h" in sys.argv:
            show_help()
            sys.exit(0)
        
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
        from rapidproxyscan import run_scanner
        
        # Get configuration
        args = get_args()
        
        # Run the scanner with config
        print("Starting RapidProxyScan with configuration from config.py")
        run_scanner(
            check_interval=args.check_interval,
            connection_limit=args.connection_limit,
            validation_rounds=args.validation_rounds,
            validation_mode=args.validation_mode,
            timeout=args.timeout,
            check_anonymity=args.check_anonymity,
            force_fetch=args.force_fetch,
            verbose=args.verbose,
            single_run=args.single_run
        )
    except ImportError:
        # If config is being imported by the scanner
        print("Configuration loaded successfully.")