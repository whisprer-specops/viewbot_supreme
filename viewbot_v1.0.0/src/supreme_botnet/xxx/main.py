#!/usr/bin/env python3
"""
Supreme Botnet Framework
Main entry point for running various botnet modules.
"""

import os
import argparse
import asyncio
import logging

# Config imports
from config.settings import get_config

# Core components
from core.proxy import ProxyPool, TorController
from core.user_agent import UserAgentManager
from core.encryption import EncryptionManager
from core.webhook import WebhookManager
from core.browser import BrowserManager
from core.captcha import CaptchaSolver
from core.email import TempEmailService

# Utils
from utils.logging import setup_logging

# Platform-specific imports (lazy loaded based on command)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Supreme Botnet Framework')
    
    # General options
    parser.add_argument('--platform', type=str, choices=['medium', 'youtube'], default='medium',
                       help='Platform to target (default: medium)')
    parser.add_argument('--mode', type=str, choices=['full', 'view-only'], default='full',
                        help='Operation mode (default: full)')
    
    # Target and credentials
    parser.add_argument('--url', type=str, help='Target URL to boost')
    parser.add_argument('--captcha-key', type=str, help='2CAPTCHA API key')
    parser.add_argument('--webhook', type=str, help='Discord webhook URL')
    
    # Performance settings
    parser.add_argument('--threads', type=int, help='Number of concurrent threads')
    parser.add_argument('--requests', type=int, help='Requests per thread')
    parser.add_argument('--delay', type=float, help='Delay between requests (seconds)')
    
    # Network settings
    parser.add_argument('--tor', action='store_true', help='Use Tor for routing')
    parser.add_argument('--no-freedium', action='store_true', help='Disable Freedium for paywall bypass')
    parser.add_argument('--verify-ssl', action='store_true', help='Enable SSL verification')
    
    # Browser settings
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    
    # File paths
    parser.add_argument('--proxy-file', type=str, help='File containing proxy list')
    parser.add_argument('--account-file', type=str, help='File containing account credentials')
    
    # Logging
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                        default='INFO', help='Logging level')
    parser.add_argument('--log-file', type=str, help='Log file path')
    
    return parser.parse_args()


async def run_medium_bot(config, mode):
    """
    Run the Medium ViewBot.
    
    Args:
        config: Configuration dictionary
        mode: 'full' or 'view-only'
    """
    # Import platform-specific modules
    from platforms.medium.interactor import MediumInteractor
    from platforms.medium.viewbot import MediumViewBot, run_view_only_mode
    
    # Initialize core components
    proxy_pool = ProxyPool(proxy_file=config.get("proxy_file"), config=config)
    user_agent_manager = UserAgentManager()
    
    if mode == 'view-only':
        # Run simplified view-only mode
        tor_controller = TorController() if config.get("use_tor") else None
        await run_view_only_mode(config, proxy_pool, user_agent_manager, tor_controller)
    else:
        # Initialize additional components for full mode
        browser_manager = BrowserManager(
            headless=config.get("headless", True),
            user_agent_manager=user_agent_manager,
            config=config
        )
        
        # Optional components based on configuration
        encryption_manager = EncryptionManager()
        webhook_manager = WebhookManager(config["webhook_url"], encryption_manager) if config.get("webhook_url") else None
        captcha_solver = CaptchaSolver(config["captcha_api_key"]) if config.get("captcha_api_key") else None
        temp_email_service = TempEmailService()
        tor_controller = TorController() if config.get("use_tor") else None
        
        # Create account manager if account file provided
        if "account_file" in config and os.path.exists(config["account_file"]):
            from core.account import AccountManager
            account_manager = AccountManager(config["account_file"])
        else:
            from core.account import AccountManager
            account_manager = AccountManager()  # Empty account manager
        
        # Create Medium interactor
        medium_interactor = MediumInteractor(
            browser_manager=browser_manager,
            captcha_solver=captcha_solver,
            temp_email_service=temp_email_service,
            config=config
        )
        
        # Create and run Medium ViewBot
        viewbot = MediumViewBot(
            config=config,
            medium_interactor=medium_interactor,
            browser_manager=browser_manager,
            proxy_pool=proxy_pool,
            account_manager=account_manager,
            tor_controller=tor_controller,
            webhook_manager=webhook_manager,
            captcha_solver=captcha_solver,
            temp_email_service=temp_email_service,
            user_agent_manager=user_agent_manager
        )
        
        # Run the viewbot
        await viewbot.run()


async def run_youtube_bot(config, mode):
    """
    Run the YouTube ViewBot.
    
    Args:
        config: Configuration dictionary
        mode: 'full' or 'view-only'
    """
    # Import platform-specific modules
    from platforms.youtube.interactor import YouTubeInteractor
    from platforms.youtube.viewbot import YouTubeViewBot, run_view_only_mode
    
    # Initialize components
    # ...Similar to Medium but with YouTube-specific setup
    # This function would be implemented when adding YouTube support
    
    print("YouTube bot not yet implemented")


async def main():
    """Main entry point for the application."""
    # Parse command-line arguments
    args = parse_arguments()
    
    # Get configuration with command-line overrides
    config = get_config(args)
    
    # Setup logging
    setup_logging(config)
    
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
        print("\nBot stopped by user")
    except Exception as e:
        logging.exception(f"Unhandled exception: {e}")
        print(f"\nError: {e}")