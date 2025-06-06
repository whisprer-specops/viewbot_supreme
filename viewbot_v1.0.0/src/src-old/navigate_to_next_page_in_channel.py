from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

# Setup Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run headless for performance
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920x1080")

# Initialize the WebDriver
driver = webdriver.Chrome(options=chrome_options)

# Visit the YouTube video URL
video_url = "https://www.youtube.com/watch?v=your_video_id"
driver.get(video_url)

# Wait for the page to load
time.sleep(5)

# Find the 'Next' button
try:
    next_button = driver.find_element(By.CSS_SELECTOR, 'a.ytp-next-button.ytp-button')

    # Click the 'Next' button to go to the next video
    next_button.click()

    print("Navigated to the next video.")
except Exception as e:
    print(f"Could not find or click the 'Next' button: {e}")

# Optional: Wait for the next video to load fully
time.sleep(5)
# You can now interact with the next video or close the driver
# For example, print the current URL of the next video
print(f"Current URL: {driver.current_url}")
# Close the browser
driver.quit()