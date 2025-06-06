#!/usr/bin/env python3
"""
Supreme Botnet Framework with Enhanced Security
Main entry point with improved key management
"""

import os
import argparse
import asyncio
import logging
import json
from pathlib import Path

# Config imports
from config.settings import get_config

# Core components
from core.proxy import ProxyPool, TorController
from core.user_agent import UserAgentManager
from core.browser import BrowserManager
from core.captcha import CaptchaSolver
from core.email import TempEmailService

# Enhanced security with persistent key management
from core.secure_encryption import PersistentKeyManager
from core.secure_webhook import SecureWebhookManager

# Utils
from utils.logging import setup_logging


def parse_arguments():
    """Parse command-line arguments with security enhancements."""
    parser = argparse.ArgumentParser(description='Supreme Botnet Framework')

    # General options
    parser.add_argument('--platform', type=str, choices=['medium', 'youtube'], default='medium',
                       help='Platform to target (default: medium)')
    parser.add_argument('--mode', type=str, choices=['full', 'view-only'], default='full',
                        help='Operation mode (default: full)')

    # Target and credentials
    parser.add_argument('--url', type=str, help='Target URL to boost')
    parser.add_argument('--captcha-key', type=str, help='2CAPTCHA API key')
    parser.add_argument('--webhook', type=str, help='Discord webhook URL (will be encrypted)')
    parser.add_argument('--proxy-file', type=str, help='Path to proxy list file')
    parser.add_argument('--account-file', type=str, help='Path to account credentials file')

    # Performance settings
    parser.add_argument('--threads', type=int, help='Number of concurrent worker threads')
    parser.add_argument('--requests', type=int, help='Number of requests per thread')
    parser.add_argument('--delay', type=float, help='Delay between requests in seconds')

    # Network settings
    parser.add_argument('--tor', action='store_true', help='Use Tor for routing all traffic')
    parser.add_argument('--no-freedium', action='store_true', help='Disable Freedium for Medium articles')
    parser.add_argument('--verify-proxies', action='store_true', help='Verify proxies before use')
    parser.add_argument('--verify-ssl', type=lambda x: x.lower() == 'true', default=True,
                        help='Enable/disable SSL verification (default: true)')

    # Browser settings
    parser.add_argument('--headless', action='store_true', help='Run browsers in headless mode')
    parser.add_argument('--browser-timeout', type=int, help='Browser operation timeout in seconds')

    # Logging and reporting
    parser.add_argument('--log-level', type=str, default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Logging level (default: INFO)')
    parser.add_argument('--stats-interval', type=int, help='Interval for printing stats in seconds')
    parser.add_argument('--max-duration', type=int, help='Maximum runtime duration in seconds')
    
    # Security options
    parser.add_argument('--create-env-script', action='store_true', 
                        help='Create a script to set up environment variables with encryption keys')
    parser.add_argument('--config-dir', type=str, 
                        help='Directory to store configuration and encryption keys')

    return parser.parse_args()


async def run_medium_bot(config, mode):
    """
    Run the Medium ViewBot with enhanced security.

    Args:
        config: Configuration dictionary
        mode: 'full' or 'view-only'
    """
    # Import platform-specific modules
    from platforms.medium.interactor import MediumInteractor
    from platforms.medium.viewbot import MediumViewBot, run_view_only_mode

    # Initialize key managers
    webhook_key_manager = PersistentKeyManager(
        service_name="webhook",
        config_dir=config.get("config_dir")
    )
    
    credentials_key_manager = PersistentKeyManager(
        service_name="credentials",
        config_dir=config.get("config_dir") 
    )
    
    # If requested, create environment setup script
    if config.get("create_env_script"):
        webhook_key_manager.create_env_var_script("setup_webhook_key")
        credentials_key_manager.create_env_var_script("setup_credentials_key")
        logging.info("Created environment variable setup scripts")

    # Initialize core components
    proxy_pool = ProxyPool(proxy_file=config.get("proxy_file"), config=config)
    user_agent_manager = UserAgentManager()
    webhook_manager = SecureWebhookManager(
        webhook_url=config.get("webhook_url"),
        key_manager=webhook_key_manager
    )
    browser_manager = BrowserManager(
        headless=config.get("headless"), 
        user_agent_manager=user_agent_manager, 
        config=config
    )
    captcha_solver = CaptchaSolver(api_key=config.get("captcha_api_key"))
    temp_email_service = TempEmailService()

    if mode == 'view-only':
        logging.info("Starting Medium bot in view-only mode...")
        await run_view_only_mode(
            config, 
            proxy_pool, 
            user_agent_manager,
            tor_controller=None if not config.get("use_tor") else TorController(),
            webhook_manager=webhook_manager
        )
    else:
        logging.info("Starting Medium bot in full engagement mode...")
        medium_interactor = MediumInteractor(
        browser_manager=browser_manager,
        captcha_solver=captcha_solver,
        temp_email_service=temp_email_service,
        config=config
    )
    viewbot = MediumViewBot(
        config=config,
        medium_interactor=medium_interactor,
        browser_manager=browser_manager,
        proxy_pool=proxy_pool,
        account_manager=None,  # We'll implement secure account storage in a future update
        tor_controller=None if not config.get("use_tor") else TorController(),
        webhook_manager=webhook_manager,
        captcha_solver=captcha_solver,
  
        temp_email_service=temp_email_service,
        user_agent_manager=user_agent_manager
    )

    # Run the viewbot
    await viewbot.run()

    print(f"MODE: {mode}, freedium: {config.get('use_freedium')}, account: {config.get('account_file')}")


async def run_youtube_bot(config, mode):
    """
    Run the YouTube ViewBot with enhanced security.

    Args:
        config: Configuration dictionary
        mode: 'full' or 'view-only'
    """
    logging.info("YouTube bot not yet implemented")
    return


async def main():
    """Main entry point with enhanced security."""
    # Parse command-line arguments
    args = parse_arguments()

    # Get configuration with command-line overrides
    config = get_config(args)
    
    # Add security-related config options
    if args.create_env_script:
        config["create_env_script"] = True
    if args.config_dir:
        config["config_dir"] = args.config_dir
    else:
        config["config_dir"] = str(Path.home() / ".supremebot")
        
    # Ensure config directory exists
    Path(config["config_dir"]).mkdir(parents=True, exist_ok=True)

    # Setup logging
    setup_logging(config)

    # Save the webhook URL securely if provided
    if args.webhook:
        webhook_key_manager = PersistentKeyManager(
            service_name="webhook",
            config_dir=config.get("config_dir")
        )
        webhook_manager = SecureWebhookManager(
            webhook_url=args.webhook,
            key_manager=webhook_key_manager
        )
        logging.info("Webhook URL encrypted and stored securely")

    # Run the appropriate bot based on platform selection
    if args.platform == 'medium':
        await run_medium_bot(config, args.mode)
    elif args.platform == 'youtube':
        await run_youtube_bot(config, args.mode)
    else:
        logging.error(f"Unsupported platform: {args.platform}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Botnet stopped by user.")
    except Exception as e:
        logging.critical(f"An unhandled error occurred: {e}", exc_info=True)