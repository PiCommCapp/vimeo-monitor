#!/usr/bin/env python3
"""
Script health monitor for Vimeo Monitor.

This module monitors the health of the Vimeo Monitor script and integrates
with the existing Monitor class.
"""

import time

try:
    from prometheus_client import Counter, Gauge
except ImportError:
    # Define dummy classes for type checking when prometheus_client is not available
    class Counter:
        def inc(self, amount=1):
            pass

        def __init__(self, *args, **kwargs):
            pass

    class Gauge:
        def set(self, value):
            pass

        def __init__(self, *args, **kwargs):
            pass


from ..config import Config
from ..logger import Logger, LoggingContext
from ..monitor import Monitor, StreamStatus


class ScriptMonitor:
    """Monitors the health of the Vimeo Monitor script."""

    def __init__(self, config: Config, logger: Logger, monitor: Monitor, registry=None):
        """Initialize script monitor.

        Args:
            config: Application configuration
            logger: Application logger
            monitor: Monitor instance to monitor
            registry: Prometheus registry
        """
        self.config = config
        self.logger = logger
        self.script_logger = LoggingContext(logger, "SCRIPT_HEALTH")
        self.monitor = monitor
        self.registry = registry

        # Last check time
        self.last_check_time = time.time()

        # Initialize metrics
        self._setup_metrics()

    def _setup_metrics(self):
        """Set up script health metrics."""
        # Script health metrics
        self.script_health = Gauge(
            "vimeo_monitor_script_health",
            "Health status of the Vimeo Monitor script (1=healthy, 0=unhealthy)",
            registry=self.registry,
        )

        self.api_requests = Counter(
            "vimeo_monitor_api_requests_total",
            "Total number of API requests made",
            registry=self.registry,
        )

        self.api_errors = Counter(
            "vimeo_monitor_api_errors_total",
            "Total number of API errors encountered",
            registry=self.registry,
        )

        self.stream_status = Gauge(
            "vimeo_monitor_stream_status",
            "Current stream status (1=live, 0=offline, -1=error)",
            registry=self.registry,
        )

        self.stream_uptime = Gauge(
            "vimeo_monitor_stream_uptime_seconds",
            "Stream uptime in seconds",
            registry=self.registry,
        )

        self.consecutive_errors = Gauge(
            "vimeo_monitor_consecutive_errors",
            "Number of consecutive errors encountered",
            registry=self.registry,
        )

        self.time_since_last_success = Gauge(
            "vimeo_monitor_time_since_last_success_seconds",
            "Time since last successful API check in seconds",
            registry=self.registry,
        )

    def update_metrics(self):
        """Update script health metrics."""
        try:
            # Get health information from monitor
            if hasattr(self.monitor, "get_health_info"):
                health_info = self.monitor.get_health_info()
                self._update_from_health_info(health_info)

            # Get stream status
            if hasattr(self.monitor, "current_status"):
                self._update_stream_status(self.monitor.current_status)

            # Update script health based on monitor's is_healthy method
            if hasattr(self.monitor, "is_healthy"):
                is_healthy = self.monitor.is_healthy()
                self.script_health.set(1 if is_healthy else 0)

            self.last_check_time = time.time()
            self.script_logger.debug("Script health metrics updated")
        except Exception as e:
            self.script_logger.error(f"Failed to update script health metrics: {e}")

    def _update_from_health_info(self, health_info: dict):
        """Update metrics from health info dictionary.

        Args:
            health_info: Health information dictionary from Monitor
        """
        # Update consecutive errors
        if "consecutive_errors" in health_info:
            self.consecutive_errors.set(health_info["consecutive_errors"])

        # Update time since last success
        if "time_since_last_success" in health_info:
            self.time_since_last_success.set(health_info["time_since_last_success"])

        # Update script health
        if "is_healthy" in health_info:
            self.script_health.set(1 if health_info["is_healthy"] else 0)

    def _update_stream_status(self, status: StreamStatus | None):
        """Update stream status metric.

        Args:
            status: Current stream status
        """
        if status is None:
            return

        # Map StreamStatus to numeric values
        status_map = {
            StreamStatus.LIVE: 1,
            StreamStatus.OFFLINE: 0,
            StreamStatus.ERROR: -1,
        }

        if status in status_map:
            self.stream_status.set(status_map[status])
