"""
Shared memory monitor to cache system resource statistics and reduce syscall overhead.
"""

import asyncio
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass

from src.utils.logging import get_logger


logger = get_logger("shared_memory_monitor")


@dataclass
class MemoryStats:
    """Cached memory statistics."""
    total_mb: float
    available_mb: float
    used_mb: float
    percentage: float
    timestamp: datetime
    
    @property
    def is_expired(self) -> bool:
        """Check if stats are expired (older than 250ms)."""
        return datetime.utcnow() - self.timestamp > timedelta(milliseconds=250)


@dataclass
class CPUStats:
    """Cached CPU statistics."""
    percentage: float
    load_average: tuple
    timestamp: datetime
    
    @property
    def is_expired(self) -> bool:
        """Check if stats are expired (older than 250ms)."""
        return datetime.utcnow() - self.timestamp > timedelta(milliseconds=250)


@dataclass
class DiskStats:
    """Cached disk statistics."""
    usage_percentage: float
    free_gb: float
    total_gb: float
    timestamp: datetime
    
    @property
    def is_expired(self) -> bool:
        """Check if stats are expired (older than 250ms)."""
        return datetime.utcnow() - self.timestamp > timedelta(milliseconds=250)


class SharedMemoryMonitor:
    """
    Shared memory monitor that caches system resource statistics to reduce syscall overhead.
    
    This monitor caches memory, CPU, and disk statistics for 250ms to prevent excessive
    psutil calls during alert storms when multiple agents check system resources.
    """
    
    def __init__(self, cache_duration_ms: int = 250):
        """
        Initialize shared memory monitor.
        
        Args:
            cache_duration_ms: Cache duration in milliseconds
        """
        self.cache_duration = timedelta(milliseconds=cache_duration_ms)
        
        # Cached statistics
        self._memory_stats: Optional[MemoryStats] = None
        self._cpu_stats: Optional[CPUStats] = None
        self._disk_stats: Optional[DiskStats] = None
        
        # Lock for thread-safe access
        self._lock = asyncio.Lock()
        
        # Statistics tracking
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_requests = 0
        
        logger.info(f"Initialized shared memory monitor with {cache_duration_ms}ms cache duration")
    
    async def get_memory_stats(self) -> MemoryStats:
        """
        Get cached memory statistics.
        
        Returns:
            Current memory statistics (cached or fresh)
        """
        async with self._lock:
            self.total_requests += 1
            
            # Check if cached stats are still valid
            if self._memory_stats and not self._memory_stats.is_expired:
                self.cache_hits += 1
                return self._memory_stats
            
            # Fetch fresh stats
            self.cache_misses += 1
            memory_info = psutil.virtual_memory()
            
            self._memory_stats = MemoryStats(
                total_mb=memory_info.total / (1024 * 1024),
                available_mb=memory_info.available / (1024 * 1024),
                used_mb=memory_info.used / (1024 * 1024),
                percentage=memory_info.percent,
                timestamp=datetime.utcnow()
            )
            
            return self._memory_stats
    
    async def get_cpu_stats(self) -> CPUStats:
        """
        Get cached CPU statistics.
        
        Returns:
            Current CPU statistics (cached or fresh)
        """
        async with self._lock:
            self.total_requests += 1
            
            # Check if cached stats are still valid
            if self._cpu_stats and not self._cpu_stats.is_expired:
                self.cache_hits += 1
                return self._cpu_stats
            
            # Fetch fresh stats
            self.cache_misses += 1
            cpu_percent = psutil.cpu_percent(interval=None)  # Non-blocking
            
            try:
                load_avg = psutil.getloadavg()
            except AttributeError:
                # Windows doesn't have getloadavg
                load_avg = (0.0, 0.0, 0.0)
            
            self._cpu_stats = CPUStats(
                percentage=cpu_percent,
                load_average=load_avg,
                timestamp=datetime.utcnow()
            )
            
            return self._cpu_stats
    
    async def get_disk_stats(self, path: str = "/") -> DiskStats:
        """
        Get cached disk statistics.
        
        Args:
            path: Path to check disk usage for
            
        Returns:
            Current disk statistics (cached or fresh)
        """
        async with self._lock:
            self.total_requests += 1
            
            # Check if cached stats are still valid
            if self._disk_stats and not self._disk_stats.is_expired:
                self.cache_hits += 1
                return self._disk_stats
            
            # Fetch fresh stats
            self.cache_misses += 1
            disk_usage = psutil.disk_usage(path)
            
            self._disk_stats = DiskStats(
                usage_percentage=(disk_usage.used / disk_usage.total) * 100,
                free_gb=disk_usage.free / (1024 * 1024 * 1024),
                total_gb=disk_usage.total / (1024 * 1024 * 1024),
                timestamp=datetime.utcnow()
            )
            
            return self._disk_stats
    
    async def get_memory_percentage(self) -> float:
        """
        Get memory usage percentage (convenience method).
        
        Returns:
            Memory usage percentage (0.0 to 100.0)
        """
        stats = await self.get_memory_stats()
        return stats.percentage
    
    async def get_memory_pressure(self) -> float:
        """
        Get memory pressure as a ratio (convenience method).
        
        Returns:
            Memory pressure ratio (0.0 to 1.0)
        """
        stats = await self.get_memory_stats()
        return stats.percentage / 100.0
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """
        Get cache performance statistics.
        
        Returns:
            Dictionary with cache hit/miss statistics
        """
        hit_rate = self.cache_hits / max(1, self.total_requests)
        
        return {
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": hit_rate,
            "cache_duration_ms": self.cache_duration.total_seconds() * 1000,
            "memory_stats_cached": self._memory_stats is not None and not self._memory_stats.is_expired,
            "cpu_stats_cached": self._cpu_stats is not None and not self._cpu_stats.is_expired,
            "disk_stats_cached": self._disk_stats is not None and not self._disk_stats.is_expired
        }
    
    async def invalidate_cache(self) -> None:
        """Invalidate all cached statistics."""
        async with self._lock:
            self._memory_stats = None
            self._cpu_stats = None
            self._disk_stats = None
            logger.info("Invalidated all cached statistics")
    
    async def health_check(self) -> bool:
        """
        Perform health check on the memory monitor.
        
        Returns:
            True if monitor is healthy
        """
        try:
            # Test memory stats retrieval
            await self.get_memory_stats()
            
            # Check cache hit rate (should be reasonable if system is working)
            stats = self.get_cache_statistics()
            if stats["total_requests"] > 10 and stats["hit_rate"] < 0.1:
                logger.warning(f"Low cache hit rate: {stats['hit_rate']:.2%}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Memory monitor health check failed: {e}")
            return False


# Global shared memory monitor instance
_shared_memory_monitor: Optional[SharedMemoryMonitor] = None


def get_shared_memory_monitor() -> SharedMemoryMonitor:
    """
    Get or create the global shared memory monitor instance.
    
    Returns:
        Shared memory monitor instance
    """
    global _shared_memory_monitor
    if _shared_memory_monitor is None:
        _shared_memory_monitor = SharedMemoryMonitor()
    return _shared_memory_monitor


async def get_cached_memory_percentage() -> float:
    """
    Convenience function to get cached memory percentage.
    
    Returns:
        Memory usage percentage (0.0 to 100.0)
    """
    monitor = get_shared_memory_monitor()
    return await monitor.get_memory_percentage()


async def get_cached_memory_pressure() -> float:
    """
    Convenience function to get cached memory pressure ratio.
    
    Returns:
        Memory pressure ratio (0.0 to 1.0)
    """
    monitor = get_shared_memory_monitor()
    return await monitor.get_memory_pressure()