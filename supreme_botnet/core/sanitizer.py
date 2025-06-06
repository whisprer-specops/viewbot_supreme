# core/sanitizer.py
from bs4 import BeautifulSoup

def sanitize_paywalled_content(html):
    soup = BeautifulSoup(html, 'html.parser')

    # Remove scripts and styles
    for script in soup(["script", "style", "noscript", "header", "footer", "svg", "img"]):
        script.decompose()

    # Remove any elements that are typical paywall overlays
    for div in soup.find_all(True):
        classes = div.get("class")
        if classes and any("paywall" in c.lower() or "overlay" in c.lower() or "blur" in c.lower() for c in classes):
            div.decompose()

    # Try to detect JS-only rendering and warn
    scripts = soup.find_all('script')
    if len(scripts) > 20 and not soup.body.find(True):
        print("[!] Content likely rendered via JS. Fallback body was nearly empty.")

    # Extract clean text
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines()]
    clean = "\n".join(line for line in lines if line)

    return clean
