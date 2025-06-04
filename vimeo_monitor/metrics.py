#!/usr/bin/env python3

"""Prometheus metrics collection and export for Vimeo Monitor.

This module provides comprehensive metrics collection for monitoring application
performance, API health, network status, and system resources using Prometheus.
"""

import logging
import threading
import time
from typing import Any

import psutil
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Summary,
    generate_latest,
    start_http_server,
)

logger = logging.getLogger(__name__)


class PrometheusMetrics:
    """Prometheus metrics collection and export for Vimeo Monitor.

    Provides comprehensive metrics for:
    - Application performance (CPU, memory, threads)
    - API metrics (response times, success/failure rates)
    - Network connectivity metrics
    - Stream status and mode changes
    - Cache performance and hit rates
    """

    def __init__(self, enable_metrics: bool = True, metrics_port: int = 8000) -> None:
        """Initialize Prometheus metrics.

        Args:
            enable_metrics: Whether to enable metrics collection
            metrics_port: Port for metrics HTTP server
        """
        self.enable_metrics = enable_metrics
        self.metrics_port = metrics_port
        self.metrics_server = None
        self.metrics_thread = None
        self.shutdown_event = threading.Event()

        if not self.enable_metrics:
            logger.info("Prometheus metrics disabled")
            return

        # System Metrics
        self.cpu_usage = Gauge("vimeo_monitor_cpu_usage_percent", "Current CPU usage percentage")
        self.memory_usage = Gauge("vimeo_monitor_memory_usage_bytes", "Current memory usage in bytes")
        self.memory_percent = Gauge("vimeo_monitor_memory_usage_percent", "Current memory usage percentage")
        self.thread_count = Gauge("vimeo_monitor_thread_count", "Current number of threads")
        self.uptime_seconds = Gauge("vimeo_monitor_uptime_seconds", "Application uptime in seconds")

        # API Metrics
        self.api_requests_total = Counter(
            "vimeo_monitor_api_requests_total", "Total API requests", ["status", "endpoint"]
        )
        self.api_response_time = Histogram(
            "vimeo_monitor_api_response_time_seconds", "API response time in seconds", ["endpoint"]
        )
        self.api_response_time_summary = Summary(
            "vimeo_monitor_api_response_time_summary", "API response time summary", ["endpoint"]
        )
        self.api_failures_total = Counter("vimeo_monitor_api_failures_total", "Total API failures", ["error_type"])
        self.api_cache_hits_total = Counter("vimeo_monitor_api_cache_hits_total", "Total API cache hits")
        self.api_cache_misses_total = Counter("vimeo_monitor_api_cache_misses_total", "Total API cache misses")

        # Stream Metrics
        self.stream_mode = Gauge("vimeo_monitor_stream_mode", "Current stream mode", ["mode"])
        self.stream_mode_changes_total = Counter(
            "vimeo_monitor_stream_mode_changes_total", "Total stream mode changes", ["from_mode", "to_mode"]
        )
        self.stream_status = Gauge("vimeo_monitor_stream_status", "Stream status (1=live, 0=offline)", ["video_id"])

        # Network Metrics
        self.network_connectivity = Gauge(
            "vimeo_monitor_network_connectivity", "Network connectivity status", ["target", "protocol"]
        )
        self.network_response_time = Histogram(
            "vimeo_monitor_network_response_time_seconds", "Network response time", ["target", "protocol"]
        )
        self.network_failures_total = Counter(
            "vimeo_monitor_network_failures_total", "Network connectivity failures", ["target", "protocol"]
        )
        self.network_recovery_total = Counter(
            "vimeo_monitor_network_recovery_total", "Network connectivity recoveries", ["target"]
        )

        # Health Metrics
        self.health_status = Gauge("vimeo_monitor_health_status", "Overall health status (1=healthy, 0=unhealthy)")
        self.component_health = Gauge("vimeo_monitor_component_health", "Component health status", ["component"])
        self.failure_mode = Gauge("vimeo_monitor_failure_mode", "Failure mode status (1=active, 0=inactive)", ["mode"])

        # Cache Metrics
        self.cache_size = Gauge("vimeo_monitor_cache_size", "Current cache size", ["cache_type"])
        self.cache_hit_rate = Gauge("vimeo_monitor_cache_hit_rate", "Cache hit rate percentage", ["cache_type"])
        self.cache_operations_total = Counter(
            "vimeo_monitor_cache_operations_total", "Cache operations", ["cache_type", "operation"]
        )
        self.cache_evictions_total = Counter(
            "vimeo_monitor_cache_evictions_total", "Cache evictions", ["cache_type", "reason"]
        )

        # Performance Metrics
        self.gc_collections_total = Counter(
            "vimeo_monitor_gc_collections_total", "Garbage collection counts", ["generation"]
        )
        self.gc_time_seconds = Summary("vimeo_monitor_gc_time_seconds", "Garbage collection time")
        self.performance_optimization_runs_total = Counter(
            "vimeo_monitor_performance_optimization_runs_total", "Performance optimization runs"
        )

        # Application startup time
        self.start_time = time.time()

        logger.info("Prometheus metrics initialized on port %d", metrics_port)

    def start_metrics_server(self) -> None:
        """Start the Prometheus metrics HTTP server."""
        if not self.enable_metrics:
            return

        try:
            # Start HTTP server for metrics endpoint
            self.metrics_server = start_http_server(self.metrics_port)
            logger.info("Prometheus metrics server started on port %d", self.metrics_port)
            logger.info("Metrics available at: http://localhost:%d/metrics", self.metrics_port)

            # Start background metrics collection
            self.metrics_thread = threading.Thread(target=self._collect_system_metrics, daemon=True)
            self.metrics_thread.start()
            logger.info("Background metrics collection started")

        except Exception as e:
            logger.error("Failed to start metrics server: %s", e)
            self.enable_metrics = False

    def stop_metrics_server(self) -> None:
        """Stop the Prometheus metrics server."""
        if not self.enable_metrics:
            return

        logger.info("Stopping Prometheus metrics server...")
        self.shutdown_event.set()

        if self.metrics_thread and self.metrics_thread.is_alive():
            self.metrics_thread.join(timeout=5)

        logger.info("Prometheus metrics server stopped")

    def _collect_system_metrics(self) -> None:
        """Background thread to collect system metrics."""
        while not self.shutdown_event.is_set():
            try:
                # Update system metrics
                self.update_system_metrics()

                # Sleep for 5 seconds before next collection
                self.shutdown_event.wait(5)

            except Exception as e:
                logger.error("Error collecting system metrics: %s", e)
                self.shutdown_event.wait(10)  # Wait longer on error

    def update_system_metrics(self) -> None:
        """Update system-level metrics."""
        if not self.enable_metrics:
            return

        try:
            # CPU and memory metrics
            self.cpu_usage.set(psutil.cpu_percent())

            memory = psutil.virtual_memory()
            self.memory_usage.set(memory.used)
            self.memory_percent.set(memory.percent)

            # Thread count
            self.thread_count.set(threading.active_count())

            # Uptime
            uptime = time.time() - self.start_time
            self.uptime_seconds.set(uptime)

        except Exception as e:
            logger.error("Error updating system metrics: %s", e)

    def record_api_request(self, endpoint: str, response_time: float, status: str = "success") -> None:
        """Record API request metrics.

        Args:
            endpoint: API endpoint name
            response_time: Response time in seconds
            status: Request status (success/error)
        """
        if not self.enable_metrics:
            return

        try:
            self.api_requests_total.labels(status=status, endpoint=endpoint).inc()
            self.api_response_time.labels(endpoint=endpoint).observe(response_time)
            self.api_response_time_summary.labels(endpoint=endpoint).observe(response_time)

        except Exception as e:
            logger.error("Error recording API request metrics: %s", e)

    def record_api_failure(self, error_type: str) -> None:
        """Record API failure metrics.

        Args:
            error_type: Type of API error
        """
        if not self.enable_metrics:
            return

        try:
            self.api_failures_total.labels(error_type=error_type).inc()

        except Exception as e:
            logger.error("Error recording API failure metrics: %s", e)

    def record_cache_hit(self, cache_type: str = "api") -> None:
        """Record cache hit metrics.

        Args:
            cache_type: Type of cache (api, etc.)
        """
        if not self.enable_metrics:
            return

        try:
            self.api_cache_hits_total.inc()
            self.cache_operations_total.labels(cache_type=cache_type, operation="hit").inc()

        except Exception as e:
            logger.error("Error recording cache hit metrics: %s", e)

    def record_cache_miss(self, cache_type: str = "api") -> None:
        """Record cache miss metrics.

        Args:
            cache_type: Type of cache (api, etc.)
        """
        if not self.enable_metrics:
            return

        try:
            self.api_cache_misses_total.inc()
            self.cache_operations_total.labels(cache_type=cache_type, operation="miss").inc()

        except Exception as e:
            logger.error("Error recording cache miss metrics: %s", e)

    def update_cache_metrics(self, cache_type: str, size: int, hit_rate: float) -> None:
        """Update cache metrics.

        Args:
            cache_type: Type of cache
            size: Current cache size
            hit_rate: Cache hit rate (0.0 to 1.0)
        """
        if not self.enable_metrics:
            return

        try:
            self.cache_size.labels(cache_type=cache_type).set(size)
            self.cache_hit_rate.labels(cache_type=cache_type).set(hit_rate * 100)  # Convert to percentage

        except Exception as e:
            logger.error("Error updating cache metrics: %s", e)

    def record_stream_mode_change(self, from_mode: str, to_mode: str) -> None:
        """Record stream mode change.

        Args:
            from_mode: Previous stream mode
            to_mode: New stream mode
        """
        if not self.enable_metrics:
            return

        try:
            self.stream_mode_changes_total.labels(from_mode=from_mode, to_mode=to_mode).inc()

            # Clear previous mode gauge
            self.stream_mode.labels(mode=from_mode).set(0)

            # Set new mode gauge
            self.stream_mode.labels(mode=to_mode).set(1)

        except Exception as e:
            logger.error("Error recording stream mode change: %s", e)

    def update_stream_status(self, video_id: str, is_live: bool) -> None:
        """Update stream status.

        Args:
            video_id: Video ID
            is_live: Whether stream is live
        """
        if not self.enable_metrics:
            return

        try:
            self.stream_status.labels(video_id=video_id).set(1 if is_live else 0)

        except Exception as e:
            logger.error("Error updating stream status: %s", e)

    def update_network_metrics(
        self, target: str, protocol: str, connected: bool, response_time: float | None = None
    ) -> None:
        """Update network connectivity metrics.

        Args:
            target: Network target (host/service)
            protocol: Protocol used (tcp, http, icmp)
            connected: Whether connection succeeded
            response_time: Response time in seconds (if available)
        """
        if not self.enable_metrics:
            return

        try:
            self.network_connectivity.labels(target=target, protocol=protocol).set(1 if connected else 0)

            if response_time is not None:
                self.network_response_time.labels(target=target, protocol=protocol).observe(response_time)

            if not connected:
                self.network_failures_total.labels(target=target, protocol=protocol).inc()

        except Exception as e:
            logger.error("Error updating network metrics: %s", e)

    def record_network_recovery(self, target: str) -> None:
        """Record network recovery event.

        Args:
            target: Network target that recovered
        """
        if not self.enable_metrics:
            return

        try:
            self.network_recovery_total.labels(target=target).inc()

        except Exception as e:
            logger.error("Error recording network recovery: %s", e)

    def update_health_status(self, overall_healthy: bool, component_status: dict[str, bool] | None = None) -> None:
        """Update health status metrics.

        Args:
            overall_healthy: Overall system health
            component_status: Individual component health status
        """
        if not self.enable_metrics:
            return

        try:
            self.health_status.set(1 if overall_healthy else 0)

            if component_status:
                for component, healthy in component_status.items():
                    self.component_health.labels(component=component).set(1 if healthy else 0)

        except Exception as e:
            logger.error("Error updating health status: %s", e)

    def update_failure_mode(self, mode: str, active: bool) -> None:
        """Update failure mode status.

        Args:
            mode: Failure mode name
            active: Whether mode is active
        """
        if not self.enable_metrics:
            return

        try:
            self.failure_mode.labels(mode=mode).set(1 if active else 0)

        except Exception as e:
            logger.error("Error updating failure mode: %s", e)

    def record_gc_collection(self, generation: int, duration: float) -> None:
        """Record garbage collection metrics.

        Args:
            generation: GC generation (0, 1, 2)
            duration: GC duration in seconds
        """
        if not self.enable_metrics:
            return

        try:
            self.gc_collections_total.labels(generation=str(generation)).inc()
            self.gc_time_seconds.observe(duration)

        except Exception as e:
            logger.error("Error recording GC metrics: %s", e)

    def record_performance_optimization(self) -> None:
        """Record performance optimization run."""
        if not self.enable_metrics:
            return

        try:
            self.performance_optimization_runs_total.inc()

        except Exception as e:
            logger.error("Error recording performance optimization: %s", e)

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get current metrics summary.

        Returns:
            Dictionary with current metrics values
        """
        if not self.enable_metrics:
            return {"error": "Metrics not enabled"}

        try:
            return {
                "system": {
                    "cpu_percent": psutil.cpu_percent(),
                    "memory_percent": psutil.virtual_memory().percent,
                    "thread_count": threading.active_count(),
                    "uptime_seconds": time.time() - self.start_time,
                },
                "metrics_server": {
                    "enabled": self.enable_metrics,
                    "port": self.metrics_port,
                    "endpoint": f"http://localhost:{self.metrics_port}/metrics",
                },
                "collection_status": "active" if not self.shutdown_event.is_set() else "stopped",
            }

        except Exception as e:
            logger.error("Error getting metrics summary: %s", e)
            return {"error": str(e)}

    def export_metrics(self) -> str:
        """Export current metrics in Prometheus format.

        Returns:
            Metrics in Prometheus text format
        """
        if not self.enable_metrics:
            return "# Metrics not enabled\n"

        try:
            return generate_latest().decode("utf-8")

        except Exception as e:
            logger.error("Error exporting metrics: %s", e)
            return f"# Error exporting metrics: {e}\n"
