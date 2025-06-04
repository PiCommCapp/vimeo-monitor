#!/usr/bin/env python3

"""Health monitoring for API and system status tracking."""

import logging
import time
from typing import Any

from vimeo_monitor.config import ConfigManager


class HealthMonitor:
    """Tracks API health, failure states, and provides comprehensive health reporting."""

    def __init__(self, config: ConfigManager) -> None:
        """Initialize health monitor.

        Args:
            config: Configuration manager instance
        """
        self.config = config

        # API failure tracking
        self.api_failure_count = 0
        self.api_success_count = 0
        self.api_failure_mode = False
        self.last_api_error: str | None = None
        self.api_retry_interval = config.api_min_retry_interval

        # API health tracking
        self.api_response_times: list[float] = []
        self.api_total_requests = 0
        self.api_last_success_time: float | None = None
        self.api_failure_start_time: float | None = None

        # Network monitoring integration
        self.network_monitor: Any = None  # Will be set by MonitorApp

        # System health tracking
        self.system_start_time = time.time()

    def set_network_monitor(self, network_monitor: Any) -> None:
        """Set the network monitor instance for integrated health status.

        Args:
            network_monitor: NetworkMonitor instance
        """
        self.network_monitor = network_monitor
        logging.info("Network monitor integrated with health monitoring")

    def calculate_backoff(self, current_interval: int) -> int:
        """Calculate the next retry interval using exponential backoff.

        Args:
            current_interval: Current retry interval

        Returns:
            Next retry interval
        """
        if not self.config.api_enable_backoff:
            return self.config.api_min_retry_interval

        # Double the current interval
        next_interval = current_interval * 2

        # Cap at maximum
        return min(next_interval, self.config.api_max_retry_interval)

    def handle_api_failure(self, error_type: str, error_message: str) -> None:
        """Handle API failures and track consecutive failures.

        Args:
            error_type: Type of error (e.g., 'connection', 'timeout')
            error_message: Detailed error message
        """
        # Increment total request counter
        self.api_total_requests += 1

        # Reset success counter and increment failure counter
        self.api_success_count = 0
        self.api_failure_count += 1
        self.last_api_error = error_type

        # Track when failure mode started
        if self.api_failure_count == 1:
            self.api_failure_start_time = time.time()

        logging.error(
            "API failure (%s): %s. Consecutive failures: %d",
            error_type,
            error_message,
            self.api_failure_count,
        )

        # Check if we should enter failure mode
        if self.api_failure_count >= self.config.api_failure_threshold:
            if not self.api_failure_mode:
                logging.warning("Entering API failure mode after %d consecutive failures", self.api_failure_count)
                self.api_failure_mode = True

                # Log detailed failure information
                if self.api_failure_start_time:
                    failure_duration = time.time() - self.api_failure_start_time
                    logging.warning("API has been failing for %.1f seconds", failure_duration)

                # Log API health statistics
                total_failures = self.api_total_requests - len(self.api_response_times)
                if self.api_total_requests > 0:
                    failure_rate = (total_failures / self.api_total_requests) * 100
                    logging.warning(
                        "API failure rate: %.1f%% (%d failures out of %d requests)",
                        failure_rate,
                        total_failures,
                        self.api_total_requests,
                    )

    def handle_api_success(self, response_time: float | None = None) -> None:
        """Handle successful API responses and track consecutive successes.

        Args:
            response_time: Optional response time in seconds
        """
        # Track successful request
        self.api_total_requests += 1
        self.api_last_success_time = time.time()

        # Track response time if provided
        if response_time is not None:
            self.api_response_times.append(response_time)

        # Reset failure counter and increment success counter
        self.api_failure_count = 0
        self.api_success_count += 1

        # Reset failure tracking when we have a success
        self.api_failure_start_time = None

        # If we're in failure mode, check if we should exit
        if self.api_failure_mode and self.api_success_count >= self.config.api_stability_threshold:
            logging.info("Exiting API failure mode after %d consecutive successes", self.api_success_count)
            self.api_failure_mode = False
            self.api_retry_interval = self.config.api_min_retry_interval  # Reset backoff timer

            # Log recovery information
            logging.info("API service restored. Total requests since start: %d", self.api_total_requests)

    def get_health_status(self) -> dict[str, Any]:
        """Get comprehensive health status information.

        Returns:
            Dictionary containing all health metrics
        """
        current_time = time.time()

        # Calculate basic statistics
        total_failures = self.api_total_requests - len(self.api_response_times)
        failure_rate = (total_failures / self.api_total_requests * 100) if self.api_total_requests > 0 else 0

        # Calculate time since last success
        time_since_success = (current_time - self.api_last_success_time) if self.api_last_success_time else None

        # Calculate failure duration if in failure mode
        failure_duration = (current_time - self.api_failure_start_time) if self.api_failure_start_time else None

        # Calculate average response time
        avg_response_time = (
            sum(self.api_response_times) / len(self.api_response_times) if self.api_response_times else None
        )

        return {
            "api_failure_mode": self.api_failure_mode,
            "consecutive_failures": self.api_failure_count,
            "consecutive_successes": self.api_success_count,
            "total_requests": self.api_total_requests,
            "total_successes": len(self.api_response_times),
            "total_failures": total_failures,
            "failure_rate_percent": round(failure_rate, 1),
            "last_error_type": self.last_api_error,
            "time_since_last_success": round(time_since_success, 1) if time_since_success else None,
            "failure_duration": round(failure_duration, 1) if failure_duration else None,
            "current_retry_interval": self.api_retry_interval,
            "next_retry_in": self.api_retry_interval if self.api_failure_mode else self.config.check_interval,
            "average_response_time": round(avg_response_time, 3) if avg_response_time else None,
        }

    def get_enhanced_status(self, current_mode: str | None = None) -> dict[str, Any]:
        """Get enhanced health status including current mode and network information.

        Args:
            current_mode: Current application mode

        Returns:
            Enhanced health status dictionary
        """
        health = self.get_health_status()
        health["current_mode"] = current_mode

        # Add network status if network monitor is available
        if self.network_monitor:
            try:
                network_status = self.network_monitor.get_network_status()
                health["network"] = {
                    "status": network_status["overall_status"],
                    "monitoring_active": network_status["monitoring_active"],
                    "targets_healthy": network_status["summary"]["healthy_targets"],
                    "targets_total": network_status["summary"]["total_targets"],
                    "targets_failing": network_status["summary"]["failing_targets"],
                    "summary": self.network_monitor.get_health_summary(),
                }
            except Exception as e:
                health["network"] = {"status": "error", "error": str(e), "summary": "❌ Network monitoring error"}
        else:
            health["network"] = {"status": "not_monitored", "summary": "❓ Network monitoring not active"}

        # Add system uptime
        uptime_seconds = time.time() - self.system_start_time
        health["system_uptime_seconds"] = round(uptime_seconds, 1)

        return health

    def get_comprehensive_status(self) -> dict[str, Any]:
        """Get comprehensive status including detailed network information.

        Returns:
            Comprehensive status dictionary with all available metrics
        """
        status = self.get_enhanced_status()

        # Add detailed network information if available
        if self.network_monitor:
            try:
                detailed_network = self.network_monitor.get_network_status()
                status["detailed_network"] = detailed_network
            except Exception as e:
                status["detailed_network"] = {"error": str(e)}

        return status

    def log_health_summary(self) -> None:
        """Log a comprehensive health summary including network status."""
        health = self.get_enhanced_status()

        # Log API health
        if health["api_failure_mode"]:
            logging.warning(
                "API Health Summary - FAILURE MODE: %d consecutive failures, "
                "%.1f%% failure rate, failing for %.1fs, next retry in %ds",
                health["consecutive_failures"],
                health["failure_rate_percent"],
                health["failure_duration"] or 0,
                health["next_retry_in"],
            )
        else:
            logging.info(
                "API Health Summary - HEALTHY: %d consecutive successes, %.1f%% failure rate, %d total requests",
                health["consecutive_successes"],
                health["failure_rate_percent"],
                health["total_requests"],
            )

        # Log network health
        network_info = health.get("network", {})
        network_status = network_info.get("status", "unknown")
        network_summary = network_info.get("summary", "Network status unknown")

        if network_status == "healthy":
            logging.info("Network Health Summary - %s", network_summary)
        elif network_status in ["degraded", "failing"]:
            logging.warning("Network Health Summary - %s", network_summary)
        elif network_status == "offline":
            logging.error("Network Health Summary - %s", network_summary)
        else:
            logging.debug("Network Health Summary - %s", network_summary)

        # Log system uptime
        uptime = health.get("system_uptime_seconds", 0)
        if uptime < 60:
            uptime_str = f"{uptime:.0f}s"
        elif uptime < 3600:
            uptime_str = f"{uptime / 60:.1f}m"
        else:
            uptime_str = f"{uptime / 3600:.1f}h"

        logging.info("System uptime: %s", uptime_str)

    def should_retry(self) -> tuple[bool, int]:
        """Check if API should be retried and get retry interval.

        Returns:
            Tuple of (should_retry, interval_seconds)
        """
        if self.api_failure_mode:
            return True, self.api_retry_interval
        return False, self.config.check_interval

    def update_retry_interval(self) -> None:
        """Update retry interval using backoff strategy."""
        if self.api_failure_mode:
            self.api_retry_interval = self.calculate_backoff(self.api_retry_interval)

    def reset_health_tracking(self) -> None:
        """Reset all health tracking metrics (useful for testing)."""
        self.api_failure_count = 0
        self.api_success_count = 0
        self.api_failure_mode = False
        self.last_api_error = None
        self.api_retry_interval = self.config.api_min_retry_interval
        self.api_response_times = []
        self.api_total_requests = 0
        self.api_last_success_time = None
        self.api_failure_start_time = None
        self.system_start_time = time.time()

    def get_uptime_seconds(self) -> float:
        """Get uptime since first successful API call.

        Returns:
            Uptime in seconds, or 0 if no successful calls yet
        """
        if self.api_last_success_time is None:
            return 0.0
        return time.time() - self.api_last_success_time

    def run_health_check(self) -> dict[str, Any]:
        """Run comprehensive health check including network connectivity.

        Returns:
            Dictionary with health check results
        """
        results: dict[str, Any] = {
            "timestamp": time.time(),
            "api_health": "healthy" if not self.api_failure_mode else "failing",
            "system_uptime": time.time() - self.system_start_time,
        }

        # Add network health check if available
        if self.network_monitor:
            try:
                network_test = self.network_monitor.run_immediate_test()
                network_status = self.network_monitor.get_network_status()

                results["network_health"] = {
                    "status": network_status["overall_status"],
                    "immediate_test": network_test,
                    "targets_status": {name: info["success_rate"] for name, info in network_status["targets"].items()},
                }
            except Exception as e:
                results["network_health"] = {"status": "error", "error": str(e)}
        else:
            results["network_health"] = {"status": "not_monitored"}

        return results
