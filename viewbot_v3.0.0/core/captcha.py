### core/captcha.py ###

import time
import logging
import requests

class CaptchaSolver:
    """
    Integrates with CAPTCHA solving services (e.g., 2CAPTCHA).
    """
    
    def __init__(self, api_key):
        """
        Initialize CAPTCHA solver.
        
        Args:
            api_key: API key for the CAPTCHA solving service
        """
        self.api_key = api_key
        
    def solve_recaptcha(self, site_key, page_url, timeout=300):
        """
        Solve a reCAPTCHA challenge.
        
        Args:
            site_key: Site key for the reCAPTCHA
            page_url: URL of the page with the CAPTCHA
            timeout: Maximum time to wait for a solution
            
        Returns:
            str: CAPTCHA solution or None if failed
        """
        if not self.api_key:
            logging.error("No 2CAPTCHA API key provided")
            return None
            
        payload = {
            'key': self.api_key,
            'method': 'userrecaptcha',
            'googlekey': site_key,
            'pageurl': page_url,
            'json': 1
        }
        try:
            # Submit CAPTCHA
            response = requests.post('http://2captcha.com/in.php', data=payload)
            response_data = response.json()
            
            if response_data.get('status') != 1:
                logging.error(f"CAPTCHA submission failed: {response_data.get('error_text')}")
                return None
                
            captcha_id = response_data.get('request')
            logging.info(f"CAPTCHA submitted, ID: {captcha_id}")
            
            # Wait for solution
            result_payload = {'key': self.api_key, 'action': 'get', 'id': captcha_id, 'json': 1}
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                time.sleep(5)
                result = requests.get('http://2captcha.com/res.php', params=result_payload)
                result_data = result.json()
                
                if result_data.get('status') == 1:
                    captcha_solution = result_data.get('request')
                    logging.info("CAPTCHA solved successfully")
                    return captcha_solution
                    
                logging.debug(f"Waiting for CAPTCHA solution... ({int(time.time() - start_time)}s)")
                
            logging.error(f"CAPTCHA solving timed out after {timeout}s")
            return None
        except Exception as e:
            logging.error(f"CAPTCHA solving error: {e}")
            return None
    
    def apply_solution(self, driver, solution):
        """
        Apply a CAPTCHA solution to a browser.
        
        Args:
            driver: WebDriver instance
            solution: CAPTCHA solution
            
        Returns:
            bool: True if applied successfully, False otherwise
        """
        try:
            driver.execute_script(f'document.getElementById("g-recaptcha-response").innerHTML="{solution}";')
            driver.execute_script("___grecaptcha_cfg.clients[0].Y.Y.callback('" + solution + "')")
            return True
        except Exception as e:
            logging.error(f"Error applying CAPTCHA solution: {e}")
            return False
