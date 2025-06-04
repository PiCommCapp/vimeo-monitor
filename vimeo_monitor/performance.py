#!/usr/bin/env python3

"""Performance monitoring and optimization module for Vimeo stream monitoring."""

import gc
import hashlib
import json
import logging
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from threading import RLock
from typing import Any

import psutil

from vimeo_monitor.metrics import PrometheusMetrics


@dataclass
class CacheEntry:
    """Represents a cached API response entry."""

    data: Any
    timestamp: float
    ttl: float
    access_count: int = 0
    last_access: float = 0.0

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return time.time() > (self.timestamp + self.ttl)

    def mark_accessed(self) -> None:
        """Mark entry as accessed and update counters."""
        self.access_count += 1
        self.last_access = time.time()


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure."""

    timestamp: float
    cpu_percent: float
    memory_usage_mb: float
    memory_percent: float
    api_response_time: float = 0.0
    cache_hit_rate: float = 0.0
    active_threads: int = 0
    process_uptime: float = 0.0
    gc_collections: dict[int, int] = field(default_factory=dict)


class IntelligentCache:
    """Thread-safe intelligent cache with TTL, LRU eviction, and performance tracking."""

    def __init__(self, max_size: int = 100, default_ttl: float = 300.0, cleanup_interval: float = 300.0):
        """Initialize the cache.

        Args:
            max_size: Maximum number of entries to store
            default_ttl: Default time-to-live in seconds
            cleanup_interval: Interval between cache cleanups
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval
        self._cache: dict[str, CacheEntry] = {}
        self._access_order: deque[str] = deque()
        self._lock = RLock()
        self._stats = {"hits": 0, "misses": 0, "evictions": 0, "expired": 0}

        logging.debug(
            "Intelligent cache initialized: max_size=%d, default_ttl=%.1fs, cleanup_interval=%.1fs",
            max_size,
            default_ttl,
            cleanup_interval,
        )

    def _generate_key(self, key_data: Any) -> str:
        """Generate a consistent cache key from data."""
        if isinstance(key_data, str):
            return key_data

        # For complex objects, create hash
        serialized = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(serialized.encode()).hexdigest()

    def get(self, key: Any, default: Any = None) -> Any:
        """Get value from cache.

        Args:
            key: Cache key
            default: Default value if not found

        Returns:
            Cached value or default
        """
        cache_key = self._generate_key(key)

        with self._lock:
            entry = self._cache.get(cache_key)

            if entry is None:
                self._stats["misses"] += 1
                logging.debug("Cache miss for key: %s", cache_key[:16])
                return default

            if entry.is_expired():
                del self._cache[cache_key]
                if cache_key in self._access_order:
                    self._access_order.remove(cache_key)
                self._stats["expired"] += 1
                self._stats["misses"] += 1
                logging.debug("Cache expired for key: %s", cache_key[:16])
                return default

            # Update access tracking
            entry.mark_accessed()

            # Move to end (most recently used)
            if cache_key in self._access_order:
                self._access_order.remove(cache_key)
            self._access_order.append(cache_key)

            self._stats["hits"] += 1
            logging.debug("Cache hit for key: %s (access_count=%d)", cache_key[:16], entry.access_count)
            return entry.data

    def set(self, key: Any, value: Any, ttl: float | None = None) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        cache_key = self._generate_key(key)
        cache_ttl = ttl if ttl is not None else self.default_ttl

        with self._lock:
            # Check if we need to evict entries
            while len(self._cache) >= self.max_size:
                self._evict_lru()

            # Create new entry
            entry = CacheEntry(data=value, timestamp=time.time(), ttl=cache_ttl)

            # Store entry
            self._cache[cache_key] = entry

            # Update access order
            if cache_key in self._access_order:
                self._access_order.remove(cache_key)
            self._access_order.append(cache_key)

            logging.debug("Cache set for key: %s (ttl=%.1fs)", cache_key[:16], cache_ttl)

    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._access_order:
            return

        lru_key = self._access_order.popleft()
        if lru_key in self._cache:
            del self._cache[lru_key]
            self._stats["evictions"] += 1
            logging.debug("Evicted LRU entry: %s", lru_key[:16])

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()
            logging.debug("Cache cleared")

    def get_statistics(self) -> dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = (self._stats["hits"] / total_requests) if total_requests > 0 else 0.0

            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hit_rate": hit_rate,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "evictions": self._stats["evictions"],
                "expired": self._stats["expired"],
                "total_requests": total_requests,
            }

    def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed."""
        expired_count = 0
        current_time = time.time()

        with self._lock:
            expired_keys = [key for key, entry in self._cache.items() if current_time > (entry.timestamp + entry.ttl)]

            for key in expired_keys:
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                expired_count += 1

            self._stats["expired"] += expired_count

        if expired_count > 0:
            logging.debug("Cleaned up %d expired cache entries", expired_count)

        return expired_count


class PerformanceMonitor:
    """Performance monitoring system with metrics collection and resource tracking."""

    def __init__(self, collection_interval: float = 5.0, history_size: int = 1000):
        """Initialize performance monitor.

        Args:
            collection_interval: How often to collect metrics (seconds)
            history_size: Maximum number of metric entries to keep
        """
        self.collection_interval = collection_interval
        self.history_size = history_size
        self.metrics_history: deque[PerformanceMetrics] = deque(maxlen=history_size)
        self.start_time = time.time()

        # Process reference
        self.process = psutil.Process()

        # Monitoring state
        self._monitoring = False
        self._monitor_thread: threading.Thread | None = None
        self._lock = RLock()

        # Performance tracking
        self._api_response_times: deque[float] = deque(maxlen=100)
        self._last_gc_stats = {gen: gc.get_stats()[gen]["collections"] for gen in range(3)}

        logging.debug("Performance monitor initialized: interval=%.1fs, history=%d", collection_interval, history_size)

    def start_monitoring(self) -> None:
        """Start background performance monitoring."""
        with self._lock:
            if self._monitoring:
                logging.warning("Performance monitoring already running")
                return

            self._monitoring = True
            self._monitor_thread = threading.Thread(
                target=self._monitoring_loop, name="PerformanceMonitor", daemon=True
            )
            self._monitor_thread.start()
            logging.info("Performance monitoring started")

    def stop_monitoring(self) -> None:
        """Stop background performance monitoring."""
        with self._lock:
            if not self._monitoring:
                return

            self._monitoring = False

            if self._monitor_thread and self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=1.0)

            logging.info("Performance monitoring stopped")

    def _monitoring_loop(self) -> None:
        """Background monitoring loop."""
        while self._monitoring:
            try:
                self._collect_metrics()
                time.sleep(self.collection_interval)
            except Exception as e:
                logging.exception("Error in performance monitoring loop: %s", e)
                time.sleep(self.collection_interval)

    def _collect_metrics(self) -> None:
        """Collect current performance metrics."""
        try:
            # CPU and memory metrics
            cpu_percent = self.process.cpu_percent()
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()

            # Thread count
            active_threads = threading.active_count()

            # Process uptime
            uptime = time.time() - self.start_time

            # GC statistics
            current_gc_stats = {gen: gc.get_stats()[gen]["collections"] for gen in range(3)}
            gc_collections = {gen: current_gc_stats[gen] - self._last_gc_stats[gen] for gen in range(3)}
            self._last_gc_stats = current_gc_stats

            # API response time average
            with self._lock:
                avg_response_time = (
                    sum(self._api_response_times) / len(self._api_response_times) if self._api_response_times else 0.0
                )

            # Create metrics entry
            metrics = PerformanceMetrics(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_usage_mb=memory_info.rss / 1024 / 1024,  # Convert to MB
                memory_percent=memory_percent,
                api_response_time=avg_response_time,
                active_threads=active_threads,
                process_uptime=uptime,
                gc_collections=gc_collections,
            )

            self.metrics_history.append(metrics)

            # Log periodic summary
            if len(self.metrics_history) % 12 == 0:  # Every minute at 5s intervals
                self._log_performance_summary()

        except Exception as e:
            logging.exception("Error collecting performance metrics: %s", e)

    def record_api_response_time(self, response_time: float) -> None:
        """Record an API response time."""
        with self._lock:
            self._api_response_times.append(response_time)

    def get_current_metrics(self) -> PerformanceMetrics | None:
        """Get the most recent performance metrics."""
        return self.metrics_history[-1] if self.metrics_history else None

    def get_metrics_summary(self, duration_minutes: int = 5) -> dict[str, Any]:
        """Get performance metrics summary for the specified duration.

        Args:
            duration_minutes: Number of minutes to analyze

        Returns:
            Dictionary with performance summary
        """
        if not self.metrics_history:
            return {}

        cutoff_time = time.time() - (duration_minutes * 60)
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]

        if not recent_metrics:
            return {}

        # Calculate statistics
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_usage_mb for m in recent_metrics]
        response_times = [m.api_response_time for m in recent_metrics if m.api_response_time > 0]

        summary = {
            "duration_minutes": duration_minutes,
            "sample_count": len(recent_metrics),
            "cpu": {"avg": sum(cpu_values) / len(cpu_values), "max": max(cpu_values), "min": min(cpu_values)},
            "memory": {
                "current_mb": recent_metrics[-1].memory_usage_mb,
                "avg_mb": sum(memory_values) / len(memory_values),
                "max_mb": max(memory_values),
                "min_mb": min(memory_values),
            },
            "api_response_time": {
                "avg_ms": (sum(response_times) * 1000 / len(response_times)) if response_times else 0,
                "max_ms": (max(response_times) * 1000) if response_times else 0,
                "min_ms": (min(response_times) * 1000) if response_times else 0,
            },
            "threads": recent_metrics[-1].active_threads,
            "uptime_hours": recent_metrics[-1].process_uptime / 3600,
            "gc_collections": recent_metrics[-1].gc_collections,
        }

        return summary

    def _log_performance_summary(self) -> None:
        """Log performance summary."""
        summary = self.get_metrics_summary(5)
        if summary:
            logging.info(
                "Performance: CPU=%.1f%% Memory=%.1fMB Threads=%d API_Avg=%.0fms GC=%s",
                summary["cpu"]["avg"],
                summary["memory"]["current_mb"],
                summary["threads"],
                summary["api_response_time"]["avg_ms"],
                summary["gc_collections"],
            )

    def force_garbage_collection(self) -> dict[str, Any]:
        """Force garbage collection and return statistics."""
        before_mem = self.process.memory_info().rss / 1024 / 1024

        # Force GC for all generations
        collected = {"gen0": gc.collect(0), "gen1": gc.collect(1), "gen2": gc.collect(2)}

        after_mem = self.process.memory_info().rss / 1024 / 1024
        memory_freed = before_mem - after_mem

        result = {
            "collected_objects": collected,
            "memory_before_mb": before_mem,
            "memory_after_mb": after_mem,
            "memory_freed_mb": memory_freed,
        }

        logging.info("Forced GC: collected %s objects, freed %.2fMB memory", collected, memory_freed)

        return result


class PerformanceOptimizer:
    """Main performance optimization coordinator."""

    def __init__(self, config: Any) -> None:
        """Initialize performance optimizer with configuration.

        Args:
            config: Configuration object with performance settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Performance settings
        self.cache_enabled = getattr(config, "enable_api_caching", True)
        self.monitor_enabled = getattr(config, "enable_performance_optimization", True)
        self.auto_gc_threshold_mb = getattr(config, "auto_gc_memory_threshold_mb", 500)

        # Initialize cache
        cache_max_size = getattr(config, "cache_max_size", 100)
        cache_default_ttl = getattr(config, "cache_default_ttl", 300)
        cache_cleanup_interval = getattr(config, "cache_cleanup_interval", 300)

        self.cache = IntelligentCache(
            max_size=cache_max_size, default_ttl=cache_default_ttl, cleanup_interval=cache_cleanup_interval
        )

        # Initialize performance monitor
        monitor_interval = getattr(config, "performance_monitor_interval", 5.0)
        history_size = getattr(config, "performance_history_size", 1000)

        self.monitor = PerformanceMonitor(collection_interval=monitor_interval, history_size=history_size)

        # Performance tracking
        self.optimization_runs = 0
        self.last_optimization = time.time()
        self.start_time = time.time()

        # Threading
        self._lock = RLock()
        self.running = False

        # Initialize Prometheus metrics if enabled
        metrics_enabled = getattr(config, "enable_prometheus_metrics", True)
        metrics_port = getattr(config, "prometheus_metrics_port", 8000)
        self.prometheus_metrics = PrometheusMetrics(enable_metrics=metrics_enabled, metrics_port=metrics_port)

        self.logger.info(
            "Performance optimizer initialized with cache=%s, monitoring=%s, metrics=%s",
            self.cache_enabled,
            self.monitor_enabled,
            metrics_enabled,
        )

    def start(self) -> None:
        """Start performance monitoring and optimization services."""
        with self._lock:
            if self.running:
                self.logger.warning("Performance optimizer already running")
                return

            self.running = True

            # Start performance monitor
            if self.monitor_enabled:
                self.monitor.start_monitoring()
                self.logger.info("Performance monitoring started")

            # Start Prometheus metrics server
            self.prometheus_metrics.start_metrics_server()

            self.logger.info("Performance optimization services started")

    def stop(self) -> None:
        """Stop performance monitoring and optimization services."""
        with self._lock:
            if not self.running:
                self.logger.warning("Performance optimizer not running")
                return

            self.running = False

            # Stop performance monitor
            self.monitor.stop_monitoring()
            self.logger.info("Performance monitoring stopped")

            # Stop Prometheus metrics server
            self.prometheus_metrics.stop_metrics_server()

            self.logger.info("Performance optimization services stopped")

    def cached_api_call(
        self, cache_key: str, api_function: Callable[[], Any], ttl: float | None = None, endpoint: str = "api"
    ) -> Any:
        """Execute API call with intelligent caching and performance tracking.

        Args:
            cache_key: Unique key for caching the result
            api_function: Function to call if cache miss
            ttl: Time-to-live override for this specific call
            endpoint: API endpoint name for metrics

        Returns:
            Result from cache or API call
        """
        start_time = time.time()

        try:
            # Try cache first
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                response_time = time.time() - start_time
                self.prometheus_metrics.record_cache_hit()
                self.prometheus_metrics.record_api_request(endpoint, response_time, "cache_hit")
                logging.debug("Cache hit for key: %s (%.3fs)", cache_key, response_time)
                return cached_result

            # Cache miss - make API call
            self.prometheus_metrics.record_cache_miss()

            result = api_function()
            api_call_time = time.time() - start_time

            # Cache the result
            self.cache.set(cache_key, result, ttl)

            # Record metrics
            self.prometheus_metrics.record_api_request(endpoint, api_call_time, "success")

            # Record current performance metrics
            current_metrics = self.monitor.get_current_metrics()
            if current_metrics:
                self.monitor.record_api_response_time(api_call_time * 1000)  # Convert to ms

            logging.debug("API call completed and cached: %s (%.3fs)", cache_key, api_call_time)
            return result

        except Exception as e:
            error_time = time.time() - start_time
            error_type = type(e).__name__

            # Record failure metrics
            self.prometheus_metrics.record_api_failure(error_type)
            self.prometheus_metrics.record_api_request(endpoint, error_time, "error")

            logging.exception("API call failed for %s: %s (%.3fs)", cache_key, e, error_time)
            raise

    def periodic_optimization(self) -> None:
        """Run periodic optimization tasks."""
        if not self.running:
            return

        start_time = time.time()

        try:
            with self._lock:
                self.optimization_runs += 1

                # Update cache metrics in Prometheus
                cache_stats = self.cache.get_statistics()
                cache_hit_rate = cache_stats.get("hit_rate", 0.0)
                cache_size = len(self.cache._cache)

                self.prometheus_metrics.update_cache_metrics("api", cache_size, cache_hit_rate)

                # Cleanup expired cache entries
                if time.time() - self.last_optimization > self.cache.cleanup_interval:
                    expired_count = self.cache.cleanup_expired()
                    if expired_count > 0:
                        logging.debug("Cleaned up %d expired cache entries", expired_count)
                    self.last_optimization = time.time()

                # Memory pressure check
                current_metrics = self.monitor.get_current_metrics()
                if current_metrics and current_metrics.memory_usage_mb > self.auto_gc_threshold_mb:
                    logging.info(
                        "Memory usage %.1fMB exceeds threshold %.1fMB, forcing GC",
                        current_metrics.memory_usage_mb,
                        self.auto_gc_threshold_mb,
                    )
                    gc_start = time.time()
                    gc_result = self.monitor.force_garbage_collection()
                    gc_time = time.time() - gc_start

                    # Record GC metrics
                    self.prometheus_metrics.record_gc_collection(0, gc_time)  # Assuming generation 0

                    collected_objects = gc_result["collected_objects"]
                    logging.info(
                        "Garbage collection completed: collected %s objects in %.3fs", collected_objects, gc_time
                    )

                # Record optimization run
                self.prometheus_metrics.record_performance_optimization()

                optimization_time = time.time() - start_time
                logging.debug("Periodic optimization completed in %.3fs", optimization_time)

        except Exception as e:
            logging.exception("Error during periodic optimization: %s", e)

    def get_optimization_status(self) -> dict[str, Any]:
        """Get comprehensive optimization status."""
        cache_stats = self.cache.get_statistics()
        performance_summary = self.monitor.get_metrics_summary(5)
        current_metrics = self.monitor.get_current_metrics()

        return {
            "cache": cache_stats,
            "performance": performance_summary,
            "current_metrics": {
                "cpu_percent": current_metrics.cpu_percent if current_metrics else 0,
                "memory_mb": current_metrics.memory_usage_mb if current_metrics else 0,
                "threads": current_metrics.active_threads if current_metrics else 0,
                "uptime_hours": current_metrics.process_uptime / 3600 if current_metrics else 0,
            }
            if current_metrics
            else {},
            "optimization_settings": {
                "cache_max_size": self.cache.max_size,
                "cache_default_ttl": self.cache.default_ttl,
                "auto_gc_threshold_mb": self.auto_gc_threshold_mb,
                "cache_cleanup_interval": self.cache.cleanup_interval,
            },
        }
