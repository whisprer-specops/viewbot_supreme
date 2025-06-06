#!/usr/bin/env python3
"""
Supreme Botnet Framework with Enhanced Security
Main entry point with integrated proxy management and view/vote boosting
"""

import os
import argparse
import asyncio
import logging
import json
from pathlib import Path
from core.proxy_manager import ProxyManager
from core.vote_booster import VoteBooster
from core.account import AccountManager
from core.browser import BrowserManager
from core.captcha import CaptchaSolver
from core.email import TempEmailService
from core.user_agent import UserAgentManager
from core.secure_encryption import PersistentKeyManager
from core.secure_webhook import SecureWebhookManager
from platforms.medium.interactor import MediumInteractor
from platforms.medium.viewbot import MediumViewBot, run_view_only_mode
from utils.logging import setup_logging
from config import get_config

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='Supreme Bot Framework')
    parser.add_argument('--platform', type=str, choices=['medium', 'vote'], default='medium', help='Platform to target (medium or vote)')
    parser.add_argument('--mode', type=str, choices=['full', 'view-only'], default='full', help='Operation mode (full or view-only)')
    parser.add_argument('--url', type=str, help='Target URL (Medium article or voting endpoint)')
    parser.add_argument('--vote-endpoint', type=str, help='Vote API endpoint')
    parser.add_argument('--vote-payload', type=json.loads, help='JSON vote payload')
    parser.add_argument('--webhook', type=str, help='Discord webhook URL')
    parser.add_argument('--discord-token', type=str, help='Discord bot token')
    parser.add_argument('--discord-channel', type=str, help='Discord channel ID')
    parser.add_argument('--account-file', type=str, default='my_accounts.json', help='Account credentials file')
    parser.add_argument('--threads', type=int, help='Number of concurrent workers')
    parser.add_argument('--requests', type=int, help='Number of requests per worker')
    parser.add_argument('--delay', type=float, help='Delay between requests (seconds)')
    parser.add_argument('--verify-ssl', type=lambda x: x.lower() == 'true', default=True, help='Verify SSL certificates')
    parser.add_argument('--log-level', type=str, default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], help='Logging level')
    parser.add_argument('--stats-interval', type=int, help='Interval for stats reporting (seconds)')
    parser.add_argument('--max-duration', type=int, help='Maximum runtime duration (seconds)')
    parser.add_argument('--create-env', action='store_true', help='Create environment configuration')
    parser.add_argument('--config-dir', type=str, help='Directory for config and keys')
    return parser.parse_args()

async def run_vote_bot(config):
    """Run the VoteBooster bot."""
    proxy_manager = ProxyManager(config)
    account_manager = AccountManager(config)
    user_agent_manager = UserAgentManager()
    await proxy_manager.initialize()
    await account_manager.initialize()
    vote_booster = VoteBooster(config, proxy_manager, account_manager, user_agent_manager)
    await vote_booster.initialize()
    try:
        await vote_booster.process_votes(config["vote_endpoint"])
    finally:
        await vote_booster.cleanup()
        await account_manager.cleanup()
        await proxy_manager.cleanup()

async def run_medium_bot(config, mode):
    """Run the Medium ViewBot."""
    proxy_manager = ProxyManager(config)
    account_manager = AccountManager(config)
    browser_manager = BrowserManager(config)
    captcha_solver = CaptchaSolver(config) if config.get("captcha_enabled") else None
    temp_email_service = TempEmailService(config) if config.get("temp_email_api") else None
    user_agent_manager = UserAgentManager()
    webhook_key_manager = PersistentKeyManager(service_name="webhook", config_dir=config.get("config_dir"))
    webhook_manager = SecureWebhookManager(config.get("webhook_url"), webhook_key_manager)
    
    await proxy_manager.initialize()
    await account_manager.initialize()
    await browser_manager.initialize()
    
    medium_interactor = MediumInteractor(
        browser_manager=browser_manager,
        captcha_solver=captcha_solver,
        temp_email_service=temp_email_service,
        user_agent_manager=user_agent_manager,
        config=config
    )
    
    view_bot = MediumViewBot(
        config=config,
        medium_interactor=medium_interactor,
        browser_manager=browser_manager,
        proxy_manager=proxy_manager,
        account_manager=account_manager,
        webhook_manager=webhook_manager,
        captcha_solver=captcha_solver,
        temp_email_service=temp_email_service,
        user_agent_manager=user_agent_manager
    )
    
    try:
        if mode == "view-only":
            success, failed = await run_view_only_mode(
                config=config,
                proxy_manager=proxy_manager,
                user_agent_manager=user_agent_manager,
                webhook_manager=webhook_manager
            )
            logging.info(f"View-only mode results: {success} successful, {failed} failed")
        else:
            await view_bot.run()
    finally:
        await browser_manager.cleanup()
        await account_manager.cleanup()
        await proxy_manager.cleanup()

async def main():
    """Main entry point."""
    args = parse_arguments()
    config = get_config(args)
    setup_logging(config["log_level"], config["log_file"])
    
    if args.create_env:
        os.makedirs(config["config_dir"], exist_ok=True)
        logging.info(f"Environment created at {config['config_dir']}")
        return
    
    if args.platform == "vote":
        await run_vote_bot(config)
    elif args.platform == "medium":
        await run_medium_bot(config, args.mode)

if __name__ == "__main__":
    asyncio.run(main())