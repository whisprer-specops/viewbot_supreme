### utils/stats.py ###

import time
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class StatCounter:
    """Simple counter for tracking statistics."""
    count: int = 0
    start_time: float = None
    
    def increment(self, amount=1):
        """Increment the counter."""
        self.count += amount
        
    def reset(self):
        """Reset the counter."""
        self.count = 0
        
    def get_rate(self, now=None):
        """Get rate per second."""
        if self.start_time is None:
            return 0
        now = now or time.time()
        elapsed = now - self.start_time
        if elapsed <= 0:
            return 0
        return self.count / elapsed


class StatsTracker:
    """
    Tracks and reports statistics for bot runs.
    """
    
    def __init__(self):
        """Initialize stats tracker."""
        self._counters = {}
        self.start_time = time.time()
        
    def create_counter(self, name):
        """
        Create a new counter.
        
        Args:
            name: Name of the counter
        """
        self._counters[name] = StatCounter(0, self.start_time)
        
    def increment(self, name, amount=1):
        """
        Increment a counter.
        
        Args:
            name: Name of the counter
            amount: Amount to increment by
        """
        if name not in self._counters:
            self.create_counter(name)
        self._counters[name].increment(amount)
        
    def get_stats(self) -> Dict[str, Any]:
        """
        Get current statistics.
        
        Returns:
            dict: Dictionary of statistics
        """
        now = time.time()
        elapsed = now - self.start_time
        
        # Format elapsed time
        hours, remainder = divmod(elapsed, 3600)
        minutes, seconds = divmod(remainder, 60)
        elapsed_str = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
        
        # Build stats dict
        stats = {
            "runtime": elapsed_str,
            "runtime_seconds": elapsed
        }
        
        # Add counter stats
        for name, counter in self._counters.items():
            stats[name] = counter.count
            stats[f"{name}_per_hour"] = round((counter.count / elapsed) * 3600, 2)
            
        return stats
    