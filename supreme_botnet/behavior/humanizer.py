import asyncio
import random

async def simulate_human_scroll(driver):
    scroll_height = driver.execute_script("return document.body.scrollHeight")
    current_scroll = 0
    while current_scroll < scroll_height:
        increment = random.randint(100, 400)
        driver.execute_script(f"window.scrollBy(0, {increment});")
        await asyncio.sleep(random.uniform(1, 3))
        current_scroll += increment

    # Simulate reading pause
    await asyncio.sleep(random.uniform(5, 10))
def human_emulation(driver):
    import random
    import time

    try:
        time.sleep(random.uniform(1.0, 2.5))
        driver.execute_script("window.scrollTo(0, window.innerHeight / 2);")
        time.sleep(random.uniform(0.5, 1.5))
        driver.execute_script("window.scrollTo(0, 0);")
        print("[*] Human emulation behavior completed.")
    except Exception as e:
        print(f"[!] Human emulation error: {e}")

async def simulate_mouse_jitter(driver):
    script = """
    const evt = new MouseEvent('mousemove', {
        bubbles: true,
        clientX: Math.floor(Math.random() * window.innerWidth),
        clientY: Math.floor(Math.random() * window.innerHeight)
    });
    document.dispatchEvent(evt);
    """
    for _ in range(random.randint(5, 10)):
        driver.execute_script(script)
        await asyncio.sleep(random.uniform(0.5, 1.5))