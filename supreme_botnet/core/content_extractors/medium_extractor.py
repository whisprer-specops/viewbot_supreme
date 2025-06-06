import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

def extract_medium_article(driver):
    """Extract readable text from a Medium article, bypassing overlay junk."""
    # Scroll a bit to trigger JS lazy loads
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.2);")
    time.sleep(2)

    article_text = ""

    try:
        # Medium articles typically live in <article>
        article_element = driver.find_element(By.TAG_NAME, "article")
        paragraphs = article_element.find_elements(By.XPATH, ".//p")

        for p in paragraphs:
            text = p.text.strip()
            if text and "Sign up" not in text and "Member-only" not in text:
                article_text += text + "\n\n"

    except NoSuchElementException:
        return "[!] Failed to locate article body."

    return article_text.strip() if article_text else "[!] No readable content extracted."
