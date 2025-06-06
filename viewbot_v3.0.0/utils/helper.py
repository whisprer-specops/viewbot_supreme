### utils/async_helpers.py ###

import asyncio
import functools
import logging
from typing import Callable, Any, Coroutine

def to_thread(func: Callable) -> Callable[..., Coroutine[Any, Any, Any]]:
    """
    Convert a blocking function to an async function that runs in a thread pool.
    
    Args:
        func: Function to convert
        
    Returns:
        Async version of the function
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)
    return wrapper

async def retry_async(coro, max_attempts=3, delay=1, backoff=2, exceptions=(Exception,)):
    """
    Retry an async coroutine with exponential backoff.
    
    Args:
        coro: Coroutine to retry
        max_attempts: Maximum number of attempts
        delay: Initial delay in seconds
        backoff: Backoff factor (delay * backoff for each retry)
        exceptions: Exceptions to catch and retry
        
    Returns:
        Result of the coroutine or raises the last exception
    """
    attempt = 0
    while True:
        try:
            return await coro
        except exceptions as e:
            attempt += 1
            if attempt >= max_attempts:
                logging.error(f"Failed after {max_attempts} attempts: {e}")
                raise
            
            wait_time = delay * (backoff ** (attempt - 1))
            logging.warning(f"Attempt {attempt} failed. Retrying in {wait_time:.2f}s: {e}")
            await asyncio.sleep(wait_time)
