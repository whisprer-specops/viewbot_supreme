# utils/async_helpers.py

import asyncio
import functools
import logging

def to_thread(func):
    """Decorator to run sync code in a thread from async context."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, functools.partial(func, *args, **kwargs))
    return wrapper

async def retry_async(coro_func, retries=3, delay=2, jitter=1):
    for attempt in range(retries):
        try:
            return await coro_func()
        except Exception as e:
            logging.warning(f"[retry_async] Attempt {attempt+1} failed: {e}")
            await asyncio.sleep(delay + random.uniform(0, jitter))
    raise RuntimeError("Max retries exceeded.")
