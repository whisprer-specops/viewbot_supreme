### core/account.py ###

import os
import json
import logging
import threading
import time

class AccountManager:
    """
    Manages accounts for platform login.
    """
    
    def __init__(self, account_file=None):
        """
        Initialize account manager.
        
        Args:
            account_file: Optional path to JSON file with accounts
        """
        self.accounts = []
        self.in_use = set()
        self.lock = threading.Lock()
        
        if account_file and os.path.exists(account_file):
            self.load_from_file(account_file)
            
    def load_from_file(self, filename):
        """
        Load accounts from a JSON file.
        
        Args:
            filename: Path to the JSON file
        """
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
                for account in data:
                    self.add_account(account['username'], account['password'])
            logging.info(f"Loaded {len(self.accounts)} accounts from {filename}")
        except Exception as e:
            logging.error(f"Failed to load accounts from file: {e}")
            # Add default accounts if loading fails
            self.add_account("example@example.com", "password123")
            
    def add_account(self, username, password):
        """
        Add an account.
        
        Args:
            username: Account username/email
            password: Account password
        """
        with self.lock:
            account = {
                'username': username, 
                'password': password, 
                'last_used': 0, 
                'failures': 0
            }
            self.accounts.append(account)
            
    def get_account(self):
        """
        Get an available account.
        
        Returns:
            dict: Account information or None if none available
        """
        with self.lock:
            now = time.time()
            available = [a for a in self.accounts 
                         if a['username'] not in self.in_use 
                         and a['failures'] < 3 
                         and now - a['last_used'] > 3600]  # 1 hour cooldown
            
            if not available:
                return None
                
            # Sort by last_used (oldest first)
            available.sort(key=lambda a: a['last_used'])
            account = available[0]
            account['last_used'] = now
            self.in_use.add(account['username'])
            return account.copy()
            
    def release_account(self, username, success=True):
        """
        Release an account back to the pool.
        
        Args:
            username: Account username/email
            success: Whether the account use was successful
        """
        with self.lock:
            if username in self.in_use:
                self.in_use.remove(username)
                
            for account in self.accounts:
                if account['username'] == username:
                    if not success:
                        account['failures'] += 1
                    else:
                        account['failures'] = 0
                    break
