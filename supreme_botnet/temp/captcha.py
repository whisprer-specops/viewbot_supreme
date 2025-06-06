# core/captcha.py

import logging
import requests

class CaptchaSolver:
    """
    Pluggable CAPTCHA solver using 2Captcha-like services.
    """

    def __init__(self, api_key):
        self.api_key = api_key

    def solve_recaptcha_v2(self, sitekey, url):
        logging.info("[CaptchaSolver] Solving reCAPTCHA v2...")
        try:
            resp = requests.post("http://2captcha.com/in.php", data={
                "key": self.api_key,
                "method": "userrecaptcha",
                "googlekey": sitekey,
                "pageurl": url,
                "json": 1
            })
            req_id = resp.json()["request"]
            logging.info("[CaptchaSolver] Sent for solving, waiting...")

            while True:
                time.sleep(5)
                poll = requests.get("http://2captcha.com/res.php", params={
                    "key": self.api_key,
                    "action": "get",
                    "id": req_id,
                    "json": 1
                }).json()
                if poll["status"] == 1:
                    return poll["request"]
                elif poll["request"] != "CAPCHA_NOT_READY":
                    raise Exception(f"Captcha solve failed: {poll}")
        except Exception as e:
            logging.warning(f"[CaptchaSolver] Failed: {e}")
            return None
