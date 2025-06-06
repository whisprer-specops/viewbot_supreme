# cli/cli_args.py
import argparse

def get_parsed_args():
    parser = argparse.ArgumentParser(
        description="Supreme Viewbot: Boost engagement metrics with configurable options."
    )

    parser.add_argument("--url", required=True, help="Target URL to send view/engagement traffic to.")
    parser.add_argument("--captcha-key", help="API key for solving CAPTCHAs.")
    parser.add_argument("--proxy-source", choices=["elite", "free", "all"], default="elite",
                        help="Choose proxy source: elite (default), free, or all.")
    parser.add_argument("--headless", action="store_true", help="Run browser sessions in headless mode.")
    parser.add_argument("--num-threads", type=int, default=1, help="Number of concurrent threads/sessions.")
    parser.add_argument("--disable-refresh", action="store_true",
                        help="Disable automatic proxy list refresh.")
    parser.add_argument("--log-level", choices=["debug", "info", "warning", "error"], default="info",
                        help="Logging level (default: info).")

    return parser.parse_args()
