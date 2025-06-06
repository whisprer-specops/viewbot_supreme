#!/usr/bin/env python3
"""
Proxy Updater Script
Replaces auto_update_and_check.bat, fetching and validating proxies using rapidproxyscan
"""

import asyncio
import logging
import os
from pathlib import Path
from rapidproxyscan import ProxyScanManager
from config import get_config, parse_arguments
from utils.logging import setup_logging

async def update_proxies(config):
    """Fetch and validate proxies, exporting to proxies.txt."""
    proxy_manager = ProxyScanManager(
        check_interval=config["check_interval"],
        connection_limit=config["connection_limit"],
        validation_rounds=config["validation_rounds"],
        validation_mode=config["validation_mode"],
        timeout=config["timeout"],
        check_anonymity=config["check_anonymity"],
        force_fetch=True,  # Force fetch for single run
        verbose=config["verbose"],
        single_run=True,
        proxy_sources=config["proxy_sources"],
        proxy_test_workers=config["proxy_test_workers"],
        proxy_fetch_interval=config["proxy_fetch_interval"],
        proxy_test_timeout=config["proxy_test_timeout"],
        proxy_test_retries=config["proxy_test_retries"],
        max_proxies_to_keep=config["max_proxies_to_keep"],
        proxy_refresh_min_interval=config["proxy_refresh_min_interval"],
        test_url=config["test_url"],
        export_interval=config["export_interval"],
        max_fetch_attempts=config["max_fetch_attempts"],
        fetch_retry_delay=config["fetch_retry_delay"]
    )
    
    await proxy_manager.initialize()
    try:
        await proxy_manager.start_scanning_loop()
        # Export to proxies.txt in the format expected by proxy_checker.py
        output_file = Path("proxies.txt")
        with outp
ut_file.open("w") as f:
            for proxy_address in sorted(proxy_manager.verified_proxies):
                f.write(f"{proxy_address}\n")
        logging.info(f"Exported {len(proxy_manager.verified_proxies)} proxies to {output_file}")
    finally:
        await proxy_manager.cleanup()

async def main():
    """Main entry point."""
    args = parse_arguments()
    config = get_config(args)
    setup_logging(config["log_level"], config["log_file"])
    await update_proxies(config)

if __name__ == "__main__":
    asyncio.run(main())