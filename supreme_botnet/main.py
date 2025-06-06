import asyncio
import logging
import argparse
from urllib.parse import urlparse
from datetime import datetime
from colorama import Fore, Style, init
from cli.cli_args import get_parsed_args

# Initialize colorama for colored console output
init(autoreset=True)

#  from utils.paywall_buster import MediumPaywallBuster, fetch_proxies, setup_logging

async def main():
    args = get_parsed_args()

def setup_logging(level=logging.INFO):
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    parser = argparse.ArgumentParser(description="Mass-Read Bot - Content Extraction")
    parser.add_argument("--url", required=True, help="Target article URL")
    parser.add_argument("--captcha-key", required=True, help="2CAPTCHA API key")
    parser.add_argument("--webhook", help="Discord webhook URL")
    parser.add_argument("--discord-token", help="Discord bot token")
    parser.add_argument("--discord-channel", type=int, help="Discord channel ID")
    args = parser.parse_args()

    # Configuration for the bot
    config = {
        "log_level": logging.INFO,
        "log_file": "botnet.log",  # log general events to this file
        "webhook_url": args.webhook,
        "discord_bot_token": args.discord_token,
        "discord_channel_id": args.discord_channel,
        "captcha_api_key": args.captcha_key,
        "account_file": "my_accounts.json",
        "clap_probability": 0.6,
        "comment_probability": 0.2,
        "user_agents": [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/91.0.4472.114 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/91.0.4472.101 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
        ]
    }

    # Set up logging to file for general logging (no console handler to keep console output clean)
    setup_logging(config)

    logging.info("Fetching proxies...")
    proxies = fetch_proxies()
    if not proxies:
        logging.error("No valid proxies found. Exiting...")
        print(f"{Fore.RED}[!] No valid proxies found. Exiting.{Style.RESET_ALL}")
        return

    # Load optional decryption key for Discord webhook (if provided)

    try:
        with open("bot_key.txt", "r") as f:
            decryption_key = f.read().strip()
    except FileNotFoundError:
        logging.warning("[!] No decryption key found. Proceeding without.")
        decryption_key = None

    # Initialize the Medium paywall buster and begin processing
    # buster = MediumPaywallBuster(config, proxies, decryption_key)
    await buster.initialize()
    print(f"{Fore.YELLOW}[*] Initiating scraping for {args.url} with rotating proxies...{Style.RESET_ALL}")
    try:
        await buster.process_article(args.url)
    finally:
        await buster.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
