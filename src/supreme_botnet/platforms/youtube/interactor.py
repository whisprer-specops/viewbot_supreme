import time
import random
import logging
import asyncio
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

class YouTubeInteractor:
    """
    Handles YouTube-specific page interactions including video viewing,
    liking, commenting, and related video discovery.
    """
    
    def __init__(self, browser_manager, captcha_solver=None, config=None):
        """
        Initialize the YouTube interactor.
        
        Args:
            browser_manager: BrowserManager instance for creating browser sessions
            captcha_solver: Optional CaptchaSolver instance
            config: Optional configuration dictionary
        """
        self.browser_manager = browser_manager
        self.captcha_solver = captcha_solver
        self.config = config or {}
        
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
    
    def simulate_human_viewing(self, driver, video_length=None):
        """
        Simulate realistic human video viewing patterns.
        
        Args:
            driver: WebDriver instance
            video_length: Optional video length in seconds
            
        Returns:
            bool: True if simulation successful, False otherwise
        """
        try:
            # Determine video length if not provided
            if not video_length:
                try:
                    # Try to extract video length from YouTube player
                    time.sleep(3)  # Wait for player to load
                    duration_element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'ytp-time-duration'))
                    )
                    duration_text = duration_element.text  # Format: "MM:SS" or "HH:MM:SS"
                    
                    # Parse time
                    time_parts = duration_text.split(':')
                    if len(time_parts) == 2:  # MM:SS
                        minutes, seconds = map(int, time_parts)
                        video_length = minutes * 60 + seconds
                    elif len(time_parts) == 3:  # HH:MM:SS
                        hours, minutes, seconds = map(int, time_parts)
                        video_length = hours * 3600 + minutes * 60 + seconds
                    else:
                        # Default to 5 minutes if parsing fails
                        video_length = 300
                except Exception as e:
                    logging.warning(f"Could not determine video length: {e}")
                    # Default to 5 minutes if extraction fails
                    video_length = 300
            
            # Cap view time to reasonable limits
            max_video_length = self.config.get("youtube_max_video_length", 600)  # 10 minutes default max
            view_time = min(video_length, max_video_length)
            
            # Watch some portion of the video (40-80% for shorter videos, 20-40% for longer ones)
            if view_time < 180:  # Short video (< 3 minutes)
                percent_to_watch = random.uniform(0.4, 0.8)
            else:  # Longer video
                percent_to_watch = random.uniform(0.2, 0.4)
                
            watch_time = view_time * percent_to_watch
            
            # Add some randomness to watch time
            watch_time *= random.uniform(0.9, 1.1)
            
            logging.info(f"Watching video for ~{watch_time:.1f}s (out of {video_length}s)")
            
            # Initial pause to let video start playing
            time.sleep(random.uniform(2, 5))
            
            # Check if video is playing (auto-play may be disabled)
            try:
                play_button = driver.find_element(By.CSS_SELECTOR, '.ytp-play-button')
                if "Play" in play_button.get_attribute("aria-label"):
                    play_button.click()
                    logging.info("Started video playback")
                    time.sleep(1)
            except Exception as e:
                logging.warning(f"Could not check play button: {e}")
            
            # Simulate random interactions during viewing
            remaining_time = watch_time
            while remaining_time > 0:
                # Random sleep interval (5-15 seconds)
                interval = min(remaining_time, random.uniform(5, 15))
                time.sleep(interval)
                remaining_time -= interval
                
                # 15% chance to perform a random action
                if random.random() < 0.15:
                    action = random.choice([
                        'scroll_down', 'scroll_up', 'adjust_volume', 
                        'pause_play', 'check_time', 'do_nothing'
                    ])
                    
                    try:
                        if action == 'scroll_down':
                            driver.execute_script("window.scrollBy(0, 300);")
                            time.sleep(random.uniform(1, 3))
                            
                        elif action == 'scroll_up':
                            driver.execute_script("window.scrollBy(0, -200);")
                            time.sleep(random.uniform(1, 2))
                            
                        elif action == 'adjust_volume':
                            # Simulate volume adjustment (doesn't actually change volume)
                            # Just moves mouse to volume area
                            volume_area = driver.find_element(By.CLASS_NAME, 'ytp-volume-area')
                            webdriver.ActionChains(driver).move_to_element(volume_area).perform()
                            time.sleep(random.uniform(0.5, 1.5))
                            
                        elif action == 'pause_play':
                            # 50% chance to actually pause (others just hover)
                            if random.random() < 0.5:
                                play_button = driver.find_element(By.CSS_SELECTOR, '.ytp-play-button')
                                play_button.click()
                                time.sleep(random.uniform(0.5, 2))
                                play_button.click()  # Resume playing
                            else:
                                play_area = driver.find_element(By.CLASS_NAME, 'ytp-chrome-bottom')
                                webdriver.ActionChains(driver).move_to_element(play_area).perform()
                                
                        elif action == 'check_time':
                            # Just hover over the time display
                            time_display = driver.find_element(By.CLASS_NAME, 'ytp-time-display')
                            webdriver.ActionChains(driver).move_to_element(time_display).perform()
                    
                    except Exception as e:
                        logging.debug(f"Action '{action}' failed: {e}")
            
            logging.info("Finished watching video")
            return True
            
        except Exception as e:
            logging.error(f"Error simulating video viewing: {e}")
            return False
    
    def like_video(self, driver):
        """
        Like the current video.
        
        Args:
            driver: WebDriver instance
            
        Returns:
            bool: True if like successful, False otherwise
        """
        try:
            # Look for the like button using various selectors
            like_selectors = [
                'button[aria-label="I like this"]',
                'button[aria-label^="Like"]',
                'ytd-toggle-button-renderer:not([is-subscribed])',
                'yt-icon-button.ytd-toggle-button-renderer'
            ]
            
            # Try each selector
            like_button = None
            for selector in like_selectors:
                try:
                    like_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except:
                    continue
            
            if not like_button:
                logging.warning("Could not find like button")
                return False
            
            # Click the like button
            # First scroll to it to ensure visibility
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", like_button)
            time.sleep(random.uniform(0.5, 1.5))
            
            try:
                like_button.click()
                logging.info("Liked the video")
                time.sleep(random.uniform(0.5, 1.5))
                return True
            except ElementClickInterceptedException:
                # Try JavaScript click if normal click is intercepted
                driver.execute_script("arguments[0].click();", like_button)
                logging.info("Liked the video (via JavaScript)")
                time.sleep(random.uniform(0.5, 1.5))
                return True
                
        except Exception as e:
            logging.error(f"Error liking video: {e}")
            return False
    
    def post_comment(self, driver, comment_text=None):
        """
        Post a comment on the current video.
        
        Args:
            driver: WebDriver instance
            comment_text: Optional comment text
            
        Returns:
            bool: True if comment posted successfully, False otherwise
        """
        if not comment_text:
            comment_text = self.config.get("comment_text", "Great video! Really enjoyed this.")
        
        try:
            # Scroll down to the comments section
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight / 2);")
            time.sleep(random.uniform(1, 3))
            
            # Look for comment box using various methods
            try:
                # First, try to find and click the comment box
                comment_box = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'ytd-comment-simplebox-renderer'))
                )
                comment_box.click()
                time.sleep(random.uniform(1, 2))
                
                # Then find and click the actual input area that appears
                try:
                    comment_input = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, '#contenteditable-root'))
                    )
                except:
                    # Fallback to active element
                    comment_input = driver.switch_to.active_element
                
                # Type comment with human-like timing
                for char in comment_text:
                    comment_input.send_keys(char)
                    time.sleep(random.uniform(0.01, 0.08))  # Random typing delay
                
                time.sleep(random.uniform(0.5, 1.5))  # Pause before submitting
                
                # Look for submit button
                submit_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, '#submit-button'))
                )
                submit_button.click()
                
                logging.info(f"Posted comment: {comment_text[:50]}...")
                time.sleep(random.uniform(1, 3))  # Wait for submission
                return True
                
            except Exception as e:
                logging.warning(f"Standard comment method failed: {e}")
                
                # Try alternative commenting method
                try:
                    # Some YouTube versions use a different comment approach
                    driver.execute_script("window.scrollBy(0, 500);")  # Scroll to expose comments
                    time.sleep(1)
                    
                    # Try to find any textarea
                    comment_area = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea'))
                    )
                    comment_area.click()
                    time.sleep(1)
                    
                    comment_area.send_keys(comment_text)
                    time.sleep(1)
                    
                    # Try submitting via Ctrl+Enter
                    comment_area.send_keys(Keys.CONTROL, Keys.ENTER)
                    logging.info(f"Posted comment using alternative method: {comment_text[:50]}...")
                    return True
                    
                except Exception as e2:
                    logging.error(f"Alternative comment method also failed: {e2}")
                    return False
                
        except Exception as e:
            logging.error(f"Error posting comment: {e}")
            return False
    
    def subscribe_to_channel(self, driver):
        """
        Subscribe to the channel of the current video.
        
        Args:
            driver: WebDriver instance
            
        Returns:
            bool: True if subscription successful, False otherwise
        """
        try:
            # Look for subscribe button using various selectors
            subscribe_selectors = [
                '#subscribe-button button',
                'ytd-subscribe-button-renderer button',
                'button[aria-label^="Subscribe"]',
                'paper-button.ytd-subscribe-button-renderer'
            ]
            
            # Try each selector
            subscribe_button = None
            for selector in subscribe_selectors:
                try:
                    subscribe_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    
                    # Check if already subscribed
                    if "SUBSCRIBED" in subscribe_button.text.upper() or "UNSUBSCRIBE" in subscribe_button.text.upper():
                        logging.info("Already subscribed to channel")
                        return False
                        
                    break
                except:
                    continue
            
            if not subscribe_button:
                logging.warning("Could not find subscribe button")
                return False
            
            # Click the subscribe button
            try:
                subscribe_button.click()
                logging.info("Subscribed to channel")
                time.sleep(random.uniform(0.5, 1.5))
                return True
            except ElementClickInterceptedException:
                # Try JavaScript click if normal click is intercepted
                driver.execute_script("arguments[0].click();", subscribe_button)
                logging.info("Subscribed to channel (via JavaScript)")
                time.sleep(random.uniform(0.5, 1.5))
                return True
                
        except Exception as e:
            logging.error(f"Error subscribing to channel: {e}")
            return False
    
    def find_next_video(self, driver):
        """
        Find and return URL of next or related video.
        
        Args:
            driver: WebDriver instance
            
        Returns:
            str: URL of next video or None if not found
        """
        try:
            # First try the "Next" button in the player
            try:
                next_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.ytp-next-button.ytp-button'))
                )
                # Just get the link without clicking
                next_video_url = next_button.get_attribute('href')
                if next_video_url:
                    logging.info(f"Found next video from player button: {next_video_url}")
                    return next_video_url
            except:
                logging.debug("No next button in player, checking recommendations")
            
            # Try to find recommended videos
            recommended_selectors = [
                '#related ytd-compact-video-renderer a#thumbnail',
                '#related a.yt-simple-endpoint',
                'ytd-watch-next-secondary-results-renderer a#thumbnail',
                '#secondary a.yt-simple-endpoint[href*="watch"]'
            ]
            
            for selector in recommended_selectors:
                try:
                    recommended_videos = driver.find_elements(By.CSS_SELECTOR, selector)
                    if recommended_videos:
                        # Get a random recommended video
                        next_video = random.choice(recommended_videos)
                        next_video_url = next_video.get_attribute('href')
                        if next_video_url and 'watch?' in next_video_url:
                            logging.info(f"Found recommended video: {next_video_url}")
                            return next_video_url
                except:
                    continue
            
            logging.warning("Could not find any next or recommended videos")
            return None
            
        except Exception as e:
            logging.error(f"Error finding next video: {e}")
            return None
    
    def navigate_to_next_video(self, driver):
        """
        Navigate to the next video using the "Next" button.
        
        Args:
            driver: WebDriver instance
            
        Returns:
            str: URL of the new video or None if navigation failed
        """
        try:
            # Find and click the "Next" button
            next_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.ytp-next-button.ytp-button'))
            )
            next_button.click()
            
            # Wait for the new video to load
            time.sleep(5)
            
            # Get the new URL
            new_url = driver.current_url
            logging.info(f"Navigated to next video: {new_url}")
            return new_url
            
        except Exception as e:
            logging.error(f"Failed to navigate to next video: {e}")
            
            # Fallback: find a recommended video and navigate manually
            try:
                next_url = self.find_next_video(driver)
                if next_url:
                    driver.get(next_url)
                    time.sleep(3)
                    new_url = driver.current_url
                    logging.info(f"Navigated to recommended video: {new_url}")
                    return new_url
            except Exception as e:
                logging.error(f"Failed to navigate to recommended video: {e}")
                
            return None
    
    def extract_video_info(self, driver):
        """
        Extract metadata from the current video.
        
        Args:
            driver: WebDriver instance
            
        Returns:
            dict: Video metadata
        """
        info = {
            "title": None,
            "channel": None,
            "view_count": None,
            "like_count": None,
            "publish_date": None,
            "duration": None,
            "description": None
        }
        
        try:
            # Extract title
            try:
                info["title"] = driver.find_element(By.CSS_SELECTOR, 'h1.ytd-video-primary-info-renderer').text
            except:
                try:
                    info["title"] = driver.find_element(By.CSS_SELECTOR, '#title h1').text
                except:
                    pass
            
            # Extract channel name
            try:
                info["channel"] = driver.find_element(By.CSS_SELECTOR, '#channel-name').text
            except:
                pass
            
            # Extract view count
            try:
                view_element = driver.find_element(By.CSS_SELECTOR, '.view-count')
                info["view_count"] = view_element.text
            except:
                pass
            
            # Extract like count
            try:
                like_element = driver.find_element(By.CSS_SELECTOR, 'button[aria-label^="Like"] + yt-formatted-string')
                info["like_count"] = like_element.text
            except:
                pass
            
            # Extract publish date
            try:
                date_element = driver.find_element(By.CSS_SELECTOR, '#info-strings yt-formatted-string')
                info["publish_date"] = date_element.text
            except:
                pass
            
            # Extract duration
            try:
                duration_element = driver.find_element(By.CLASS_NAME, 'ytp-time-duration')
                info["duration"] = duration_element.text
            except:
                pass
            
            # Extract description
            try:
                description_element = driver.find_element(By.CSS_SELECTOR, '#description-text')
                info["description"] = description_element.text
            except:
                pass
            
            return {k: v for k, v in info.items() if v}  # Only return non-None values
            
        except Exception as e:
            logging.error(f"Error extracting video info: {e}")
            return info