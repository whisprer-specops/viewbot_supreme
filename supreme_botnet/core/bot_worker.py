import threading
import logging
from time import sleep
import random

from core.browser import BrowserController
from core.account import AccountManager
from core.secure_webhook import SecureWebhookManager
from core.captcha import CaptchaSolver

class BotWorker(threading.Thread):
    def __init__(self, mode, target, count, proxy, account_mgr: AccountManager,
                 webhook_mgr: SecureWebhookManager = None, captcha_solver: CaptchaSolver = None):
        super().__init__()
        self.mode = mode
        self.target = target
        self.count = count
        self.proxy = proxy
        self.account_mgr = account_mgr
        self.webhook_mgr = webhook_mgr
        self.captcha_solver = captcha_solver
        self.browser = BrowserController()
        self._stop_event = threading.Event()

    def run(self):
        logging.info(f"[BotWorker] Mode: {self.mode}, Target: {self.target}, Count: {self.count}")
        successes = 0
        failures = 0

        for i in range(self.count):
            if self._stop_event.is_set():
                logging.info("[BotWorker] Stopping on external request.")
                break

            logging.info(f"[BotWorker] Attempt {i + 1}/{self.count}")
            account = self.account_mgr.get_random_account()
            if not account:
                logging.warning("[BotWorker] No account available.")
                break

            try:
                with self.browser.launch(account=account, proxy=self.proxy) as session:
                    if self.mode == "medium":
                        success = session.clap_article(self.target)
                    elif self.mode == "youtube":
                        success = session.watch_video(self.target)
                    else:
                        logging.warning(f"[BotWorker] Unknown mode: {self.mode}")
                        success = False

                    if success:
                        successes += 1
                        logging.info(f"[BotWorker] Success #{successes}")
                    else:
                        failures += 1
                        logging.warning(f"[BotWorker] Failure #{failures}")

            except Exception as e:
                failures += 1
                logging.error(f"[BotWorker] Exception: {e}")

            sleep(random.randint(3, 8))

        logging.info(f"[BotWorker] Finished: {successes} success, {failures} failures.")

    "✅ BotWorker now sends webhook summary at task end!"

    def stop(self):
        self._stop_event.set()