### core/email.py ###

import time
import logging
import requests
import re
from bs4 import BeautifulSoup

class TempEmailService:
    """
    Provides temporary email addresses for registration and verification.
    """
    
    def __init__(self, api_base="https://api.temp-mail.org"):
        """
        Initialize temporary email service.
        
        Args:
            api_base: Base URL for the temp email API
        """
        self.api_base = api_base
        self.email = None
        self.email_id = None
        
        # Alternative services if primary fails
        self.alt_services = [
            "https://www.1secmail.com/api/v1/",
            "https://www.emailnator.com/api/v1/"
        ]
        self.current_service = 0
        
    def get_email(self):
        """
        Get a temporary email address.
        
        Returns:
            str: Email address or None if failed
        """
        # Try primary service
        email = self._try_get_email(self.api_base)
        if email:
            return email
            
        # Try alternative services
        for i, service in enumerate(self.alt_services):
            logging.info(f"Primary email service failed. Trying alternative service {i+1}...")
            email = self._try_get_email(service)
            if email:
                self.current_service = i + 1
                return email
                
        # If all fail, generate a random email (might not work for verification)
        logging.warning("All email services failed. Generating random email...")
        import random
        import string
        random_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.email = f"{random_name}@example.com"
        return self.email
    
    def _try_get_email(self, service_url):
        """
        Try to get an email from a specific service.
        
        Args:
            service_url: URL of the email service
            
        Returns:
            str: Email address or None if failed
        """
        try:
            response = requests.get(f"{service_url}/request/email/format/json", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.email = data.get('email')
                self.email_id = data.get('email_id')
                logging.info(f"Got temp email: {self.email}")
                return self.email
        except Exception as e:
            logging.error(f"Error getting temp email from {service_url}: {e}")
        return None
            
    def check_inbox(self, timeout=180, interval=5):
        """
        Check inbox for sign-in emails.
        
        Args:
            timeout: Maximum time to wait
            interval: Time between inbox checks
            
        Returns:
            str: Sign-in URL or None if not found
        """
        if not self.email_id:
            logging.error("No email ID available")
            return None
            
        start_time = time.time()
        service_url = self.alt_services[self.current_service - 1] if self.current_service > 0 else self.api_base
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{service_url}/request/mail/id/{self.email_id}/format/json", timeout=10)
                if response.status_code == 200:
                    emails = response.json()
                    
                    # Look for sign-in emails
                    for email_data in emails:
                        subject = email_data.get('subject', '')
                        if "sign" in subject.lower() or "verify" in subject.lower() or "confirm" in subject.lower():
                            body = email_data.get('body', '')
                            
                            # Try to find sign-in link in HTML content
                            soup = BeautifulSoup(body, 'html.parser')
                            for link in soup.find_all('a'):
                                href = link.get('href', '')
                                if any(keyword in href.lower() for keyword in ["signin", "sign-in", "verify", "confirm"]):
                                    logging.info(f"Found sign-in link: {href[:50]}...")
                                    return href
                                    
                            # If HTML parsing fails, try regex
                            urls = re.findall(r'https?://\S+?(?=[\s\'"]|$)', body)
                            for url in urls:
                                if any(keyword in url.lower() for keyword in ["signin", "sign-in", "verify", "confirm"]):
                                    logging.info(f"Found sign-in link via regex: {url[:50]}...")
                                    return url
            except Exception as e:
                logging.error(f"Error checking inbox: {e}")
                
            # Progress logging
            elapsed = int(time.time() - start_time)
            if elapsed % 30 == 0:  # Log every 30 seconds
                logging.info(f"Waiting for sign-in email... ({elapsed}s elapsed)")
                
            time.sleep(interval)
            
        logging.error(f"No sign-in email found after {timeout}s")
        return None
