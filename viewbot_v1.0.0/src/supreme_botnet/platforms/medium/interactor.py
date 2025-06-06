import time
import random
import logging
import asyncio
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import markovify

class MediumInteractor:
    """
    Handles Medium-specific page interactions including reading, clapping,
    commenting, and author following.
    """
    
    def __init__(self, browser_manager, captcha_solver=None, temp_email_service=None, config=None):
        """
        Initialize the Medium interactor.
        
        Args:
            browser_manager: BrowserManager instance for creating browser sessions
            captcha_solver: Optional CaptchaSolver instance
            temp_email_service: Optional TempEmailService instance
            config: Optional configuration dictionary
        """
        self.browser_manager = browser_manager
        self.captcha_solver = captcha_solver
        self.temp_email_service = temp_email_service
        self.config = config or {}
        
    def get_freedium_url(self, medium_url):
        """
        Convert Medium URL to Freedium URL to bypass paywall.
        
        Args:
            medium_url: Original Medium article URL
            
        Returns:
            Freedium URL for the article
        """
        # Make sure URL is properly formatted
        if not medium_url.startswith("http"):
            medium_url = f"https://{medium_url}"
        return f"https://freedium.cfd/{medium_url}"
        
    def _detect_and_solve_captcha(self, driver, url):
        """
        Detect and solve CAPTCHA if present.
        
        Args:
            driver: WebDriver instance
            url: Current page URL
            
        Returns:
            bool: True if CAPTCHA was solved or not present, False otherwise
        """
        if not self.captcha_solver:
            return False
            
        try:
            # Check for reCAPTCHA presence
            captcha_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'g-recaptcha'))
            )
            
            # Extract site key
            site_key = driver.execute_script(
                "return document.querySelector('.g-recaptcha').dataset.sitekey;"
            )
            
            if not site_key:
                logging.error("CAPTCHA detected but couldn't extract site key")
                return False
                
            # Solve CAPTCHA
            solution = self.captcha_solver.solve_recaptcha(site_key, url)
            if not solution:
                return False
                
            # Apply solution
            return self.captcha_solver.apply_solution(driver, solution)
            
        except TimeoutException:
            # No CAPTCHA found
            return True
        except Exception as e:
            logging.error(f"Error in CAPTCHA handling: {e}")
            return False
    
    async def login_with_email(self, driver, medium_url):
        """
        Login to Medium using temporary email.
        
        Args:
            driver: WebDriver instance
            medium_url: Medium article URL
            
        Returns:
            bool: True if login successful, False otherwise
        """
        if not self.temp_email_service:
            return False
            
        email = self.temp_email_service.get_email()
        if not email:
            return False
            
        try:
            # Navigate to Medium
            driver.get(medium_url)
            
            # Find and click sign in button
            try:
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//a[contains(text(), "Sign in")]'))
                ).click()
            except:
                logging.warning("Could not find Sign in button, looking for alternative")
                # Try alternative sign-in buttons
                alternatives = [
                    '//button[contains(text(), "Sign in")]',
                    '//a[contains(@href, "signin")]',
                    '//a[contains(@class, "signin")]'
                ]
                for xpath in alternatives:
                    try:
                        element = WebDriverWait(driver, 3).until(
                            EC.element_to_be_clickable((By.XPATH, xpath))
                        )
                        element.click()
                        break
                    except:
                        continue
            
            # Enter email
            try:
                email_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, 'email'))
                )
                email_input.send_keys(email)
                
                # Find and click continue button
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Continue")]'))
                ).click()
                
                # Wait for sign-in email
                logging.info("Waiting for sign-in email...")
                signin_url = await asyncio.to_thread(
                    self.temp_email_service.check_inbox, 
                    timeout=180,  # 3 minutes to wait for email
                    interval=5    # Check every 5 seconds
                )
                
                if signin_url:
                    driver.get(signin_url)
                    # Wait for login to complete
                    time.sleep(5)
                    logging.info("Successfully logged in via email link")
                    return True
                else:
                    logging.error("No sign-in email received")
                    return False
            except Exception as e:
                logging.error(f"Error during email login flow: {e}")
                return False
                
        except Exception as e:
            logging.error(f"Email login failed: {e}")
            return False
        
    def login_with_credentials(self, driver, username, password):
        """
        Login to Medium using stored credentials.
        
        Args:
            driver: WebDriver instance
            username: Medium account email
            password: Medium account password
            
        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            # Navigate to sign-in page
            driver.get('https://medium.com/m/signin')
            
            # Enter email
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'email'))
            ).send_keys(username)
            
            # Click next
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Next") or contains(text(), "Continue")]'))
            ).click()
            
            # If redirected to password page
            try:
                password_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, 'password'))
                )
                password_field.send_keys(password)
                
                # Click sign in
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Sign in")]'))
                ).click()
                
                # Wait for login to complete
                time.sleep(5)
                
                # Check for successful login
                if "Sign in" in driver.title or "/signin" in driver.current_url:
                    logging.error("Login unsuccessful - still on login page")
                    return False
                    
                logging.info(f"Successfully logged in as {username}")
                return True
                
            except TimeoutException:
                # May already be logged in or email-only login
                logging.warning("Could not find password field, checking login status")
                
                # Check if we're already logged in
                if "Sign in" not in driver.title and "/signin" not in driver.current_url:
                    logging.info(f"Login seems successful for {username}")
                    return True
                    
                return False
                
        except Exception as e:
            logging.error(f"Login with credentials failed: {e}")
            return False
    
    def simulate_human_reading(self, driver, article_length=None):
        """
        Simulate realistic human reading patterns.
        
        Args:
            driver: WebDriver instance
            article_length: Optional pre-determined article length
            
        Returns:
            bool: True if simulation successful, False otherwise
        """
        try:
            # Get scroll height
            scroll_height = driver.execute_script("return document.body.scrollHeight")
            
            if not article_length:
                # Estimate article length by text content
                article_text = driver.find_element(By.TAG_NAME, "body").text
                article_length = len(article_text)
            
            # Calculate read time based on article length (approx 200-300 WPM)
            words = article_length // 5  # Approx 5 chars per word
            base_read_time = words / random.uniform(200, 300)  # Random WPM between 200-300
            
            # Add some randomness (±20%)
            read_time = base_read_time * random.uniform(0.8, 1.2)
            
            # Cap read time between config min and max
            read_time_min = self.config.get("read_time_min", 45)
            read_time_max = self.config.get("read_time_max", 180)
            read_time = max(read_time_min, min(read_time_max, read_time))
            
            # Divide scroll height into random segments
            segments = random.randint(5, 15)
            segment_height = scroll_height / segments
            
            logging.info(f"Reading article for ~{read_time:.1f}s with {segments} scroll segments")
            
            # Initial pause to simulate page load review
            time.sleep(random.uniform(1, 3))
            
            # Scroll through article with random pauses
            for i in range(segments):
                # Scroll to next segment with some randomness
                target_scroll = int((i + 1) * segment_height * random.uniform(0.9, 1.1))
                driver.execute_script(f"window.scrollTo(0, {min(target_scroll, scroll_height)});")
                
                # Pause for reading with some randomness
                segment_time = read_time / segments * random.uniform(0.7, 1.3)
                time.sleep(segment_time)
                
                # 10% chance to scroll back up a bit (like re-reading)
                if random.random() < 0.1:
                    scroll_back = max(0, target_scroll - segment_height * random.uniform(0.3, 0.7))
                    driver.execute_script(f"window.scrollTo(0, {scroll_back});")
                    time.sleep(random.uniform(1, 3))
                    
                    # Then continue where we left off
                    driver.execute_script(f"window.scrollTo(0, {target_scroll});")
                    time.sleep(random.uniform(1, 2))
                    
                # 5% chance to pause a little longer (like being distracted)
                if random.random() < 0.05:
                    time.sleep(random.uniform(3, 8))
                    
            # 70% chance to scroll back up randomly at the end
            if random.random() < 0.7:
                random_position = random.uniform(0, scroll_height * 0.8)
                driver.execute_script(f"window.scrollTo(0, {random_position});")
                time.sleep(random.uniform(1, 3))
            
            return True
        except Exception as e:
            logging.error(f"Error during reading simulation: {e}")
            return False
            
    def clap_for_article(self, driver, min_claps=1, max_claps=50):
        """
        Clap for an article with a random number of claps.
        
        Args:
            driver: WebDriver instance
            min_claps: Minimum number of claps
            max_claps: Maximum number of claps
            
        Returns:
            bool: True if clapping successful, False otherwise
        """
        try:
            # Find the clap button
            clap_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//button[contains(@aria-label, "clap") or contains(@class, "clap")]'))
            )
            
            # Random number of claps
            num_claps = random.randint(min_claps, max_claps)
            logging.info(f"Clapping {num_claps} times")
            
            # Click the button multiple times
            for _ in range(num_claps):
                clap_button.click()
                time.sleep(random.uniform(0.05, 0.2))  # Random delay between claps
                
            return True
        except Exception as e:
            logging.error(f"Error while clapping: {e}")
            return False
            
    def generate_comment(self, article_text):
        """
        Generate a Markov chain-based comment from article text.
        
        Args:
            article_text: Text content of the article
            
        Returns:
            str: Generated comment text
        """
        try:
            # Clean up article text
            clean_text = ' '.join(article_text.split())
            
            # Create Markov model
            text_model = markovify.Text(clean_text, state_size=2)
            
            # Try to generate a sensible comment
            for _ in range(10):  # Try up to 10 times
                comment = text_model.make_short_sentence(
                    max_chars=280, 
                    min_chars=50,
                    tries=100
                )
                if comment and len(comment) >= 50:
                    break
                    
            # Fallback comments if generation fails
            fallback_comments = [
                "Great article! Really enjoyed the insights.",
                "Thanks for sharing these thoughts, very enlightening!",
                "This was an interesting read. Looking forward to more.",
                "I appreciate the perspective shared here.",
                "This resonates with my own experiences. Well written!",
                "Thoughtful analysis. I'll be reflecting on these points.",
                "You've articulated something I've been thinking about too."
            ]
            
            if not comment:
                comment = random.choice(fallback_comments)
                
            return comment
        except Exception as e:
            logging.error(f"Error generating comment: {e}")
            return random.choice([
                "Interesting perspective!",
                "Great read!",
                "Thanks for sharing this!"
            ])
            
    def post_comment(self, driver, comment=None):
        """
        Post a comment on the article.
        
        Args:
            driver: WebDriver instance
            comment: Optional comment text (generated if None)
            
        Returns:
            bool: True if comment posted successfully, False otherwise
        """
        try:
            if not comment:
                # Get article text
                article_text = driver.find_element(By.TAG_NAME, "body").text
                comment = self.generate_comment(article_text)
                
            # Look for comment box
            comment_selectors = [
                '//textarea[contains(@placeholder, "comment") or contains(@placeholder, "response")]',
                '//div[contains(@aria-label, "comment") or contains(@aria-label, "response")]',
                '//textarea',  # Fallback to any textarea
            ]
            
            comment_box = None
            for selector in comment_selectors:
                try:
                    comment_box = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                    break
                except:
                    continue
                    
            if not comment_box:
                logging.error("Could not find comment box")
                return False
                
            # Click on comment box
            comment_box.click()
            time.sleep(random.uniform(0.5, 1.5))
            
            # Type comment with human-like timing
            for char in comment:
                comment_box.send_keys(char)
                time.sleep(random.uniform(0.01, 0.10))  # Random typing delay
                
            time.sleep(random.uniform(0.5, 2))  # Pause before publishing
            
            # Try to find publish button
            publish_selectors = [
                '//button[contains(text(), "Publish") or contains(text(), "Comment") or contains(text(), "Respond")]',
                '//button[@type="submit"]',
                '//button[contains(@class, "publish") or contains(@class, "submit")]'
            ]
            
            for selector in publish_selectors:
                try:
                    publish_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    publish_button.click()
                    logging.info(f"Posted comment: {comment[:50]}...")
                    time.sleep(random.uniform(1, 3))  # Wait for submission
                    return True
                except:
                    continue
                    
            # Fallback: try Enter key
            comment_box.send_keys(Keys.CONTROL, Keys.ENTER)
            logging.info(f"Posted comment using Ctrl+Enter: {comment[:50]}...")
            time.sleep(random.uniform(1, 3))
            
            return True
        except Exception as e:
            logging.error(f"Error posting comment: {e}")
            return False
            
    def follow_author(self, driver):
        """
        Find and click the follow button to follow the author.
        
        Args:
            driver: WebDriver instance
            
        Returns:
            bool: True if author followed successfully, False otherwise
        """
        try:
            follow_selectors = [
                '//button[contains(text(), "Follow")]',
                '//a[contains(text(), "Follow")]',
                '//button[contains(@aria-label, "Follow")]'
            ]
            
            for selector in follow_selectors:
                try:
                    follow_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    follow_button.click()
                    logging.info("Followed author")
                    time.sleep(random.uniform(1, 3))
                    return True
                except:
                    continue
                    
            logging.warning("Could not find follow button")
            return False
        except Exception as e:
            logging.error(f"Error following author: {e}")
            return False
            
    def find_next_article(self, driver):
        """
        Find and return URL of a next or related article.
        
        Args:
            driver: WebDriver instance
            
        Returns:
            str: URL of next article or None if not found
        """
        try:
            # Try to find "Next" or "Part" links first
            next_selectors = [
                '//a[contains(text(), "Next")]',
                '//a[contains(text(), "Part")]',
                '//a[contains(@class, "next")]'
            ]
            
            for selector in next_selectors:
                try:
                    next_link = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    next_url = next_link.get_attribute('href')
                    if next_url and "medium.com" in next_url:
                        logging.info(f"Found next article: {next_url}")
                        return next_url
                except:
                    continue
                    
            # If no next article, try to find related/recommended articles
            related_selectors = [
                '//h2[contains(text(), "More from")]/following::a',
                '//h3[contains(text(), "Recommended")]/following::a',
                '//div[contains(@class, "recommended")]/descendant::a',
                '//article//a[contains(@href, "medium.com")]'
            ]
            
            for selector in related_selectors:
                try:
                    related_links = driver.find_elements(By.XPATH, selector)
                    if related_links:
                        # Get random related article
                        related_link = random.choice(related_links)
                        related_url = related_link.get_attribute('href')
                        if related_url and "medium.com" in related_url:
                            logging.info(f"Found related article: {related_url}")
                            return related_url
                except:
                    continue
                    
            logging.warning("Could not find next or related article")
            return None
        except Exception as e:
            logging.error(f"Error finding next article: {e}")
            return None
            
    def extract_medium_stats(self, driver):
        """
        Extract and return article metadata and stats.
        
        Args:
            driver: WebDriver instance
            
        Returns:
            dict: Article metadata and stats
        """
        try:
            stats = {
                "title": None,
                "author": None,
                "publish_date": None,
                "read_time": None,
                "clap_count": None,
                "comment_count": None
            }
            
            # Extract title
            try:
                stats["title"] = driver.find_element(By.TAG_NAME, "h1").text
            except:
                pass
                
            # Extract author
            try:
                stats["author"] = driver.find_element(By.XPATH, '//a[contains(@href, "/@")]').text
            except:
                pass
                
            # Extract publish date
            try:
                date_element = driver.find_element(By.XPATH, '//time')
                stats["publish_date"] = date_element.get_attribute("datetime") or date_element.text
            except:
                pass
                
            # Extract read time
            try:
                read_time_text = driver.find_element(By.XPATH, '//*[contains(text(), "min read")]').text
                stats["read_time"] = read_time_text
            except:
                pass
                
            # Extract clap count
            try:
                clap_text = driver.find_element(By.XPATH, '//*[contains(@aria-label, "clap") or contains(@class, "clap")]//following-sibling::*').text
                stats["clap_count"] = clap_text
            except:
                pass
                
            # Extract comment count
            try:
                comment_text = driver.find_element(By.XPATH, '//*[contains(text(), "response") or contains(text(), "comment")]').text
                stats["comment_count"] = comment_text
            except:
                pass
                
            return {k: v for k, v in stats.items() if v}  # Only return non-None values
        except Exception as e:
            logging.error(f"Error extracting article stats: {e}")
            return {}
