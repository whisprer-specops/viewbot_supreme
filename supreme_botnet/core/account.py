# core/account.py

import json
import logging
import random
from pathlib import Path

ACCOUNT_FILE = Path("data/my_accounts.json")

class AccountManager:
    def __init__(self, account_file=ACCOUNT_FILE):
        self.accounts = []
        self.account_file = Path(account_file)
        self._load_accounts()

    def _load_accounts(self):
        try:
            with open(self.account_file, "r") as f:
                self.accounts = json.load(f)
            logging.info(f"[AccountManager] Loaded {len(self.accounts)} accounts.")
        except Exception as e:
            logging.warning(f"[AccountManager] Failed to load accounts: {e}")
            self.accounts = []

    def get_random_account(self):
        if not self.accounts:
            return None
        return random.choice(self.accounts)
