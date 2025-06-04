#!/usr/bin/env python3

"""Network connectivity monitoring and health checking for Vimeo Monitor."""

import logging
import socket
import subprocess
import time
import urllib.error
import urllib.request
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from threading import Lock, Thread
from typing import Any, NamedTuple

from vimeo_monitor.config import ConfigManager


class NetworkStatus(Enum):
    """Network connectivity status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILING = "failing"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class MonitoringMode(Enum):
    """Network monitoring mode for adaptive behavior."""

    NORMAL = "normal"
    DEGRADED = "degraded"
    FAILURE = "failure"
    RECOVERY = "recovery"


class ConnectivityTest(NamedTuple):
    """Result of a connectivity test."""

    success: bool
    response_time: float
    error: str | None
    timestamp: datetime


@dataclass
class NetworkMetrics:
    """Network monitoring metrics."""

    total_tests: int = 0
    successful_tests: int = 0
    failed_tests: int = 0
    average_response_time: float = 0.0
    current_status: NetworkStatus = NetworkStatus.UNKNOWN
    last_success_time: datetime | None = None
    last_failure_time: datetime | None = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    uptime_percent: float = 100.0

    # Rolling metrics (last 100 tests)
    recent_tests: deque[ConnectivityTest] = field(default_factory=lambda: deque(maxlen=100))

    @property
    def failure_rate_percent(self) -> float:
        """Calculate failure rate percentage."""
        if self.total_tests == 0:
            return 0.0
        return (self.failed_tests / self.total_tests) * 100.0

    @property
    def success_rate_percent(self) -> float:
        """Calculate success rate percentage."""
        return 100.0 - self.failure_rate_percent


@dataclass
class NetworkTarget:
    """Network connectivity target configuration."""

    name: str
    host: str
    port: int = 80
    timeout: float = 5.0
    protocol: str = "tcp"  # tcp, http, https, icmp
    critical: bool = False  # If true, failure affects overall status
    priority: int = 1  # 1=highest, 3=lowest priority for fallback scenarios
    fallback_hosts: list[str] = field(default_factory=list)  # Alternative hosts

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.protocol not in ["tcp", "http", "https", "icmp"]:
            raise ValueError(f"Unsupported protocol: {self.protocol}")

        if self.port < 1 or self.port > 65535:
            raise ValueError(f"Invalid port: {self.port}")

        if self.priority < 1 or self.priority > 3:
            raise ValueError(f"Priority must be 1-3, got: {self.priority}")


@dataclass
class FallbackStrategy:
    """Network fallback strategy configuration."""

    # Adaptive monitoring intervals (seconds)
    normal_interval: int = 30
    degraded_interval: int = 45  # Slower when degraded
    failure_interval: int = 60  # Slowest when failing
    recovery_interval: int = 15  # Faster during recovery

    # Fallback thresholds
    degraded_threshold: int = 2  # Consecutive failures to enter degraded mode
    failure_threshold: int = 4  # Consecutive failures to enter failure mode
    recovery_threshold: int = 3  # Consecutive successes to exit failure mode

    # Priority-based monitoring
    enable_priority_monitoring: bool = True
    critical_only_in_failure: bool = True  # Only monitor critical targets when failing

    # Endpoint fallback
    enable_endpoint_fallback: bool = True
    fallback_timeout_multiplier: float = 1.5  # Increase timeout for fallback hosts

    # Backoff strategy
    enable_adaptive_backoff: bool = True
    max_backoff_multiplier: float = 3.0
    backoff_recovery_factor: float = 0.8


class NetworkMonitor:
    """
    Comprehensive network connectivity monitoring system with advanced fallback strategies.

    Monitors multiple network targets with different protocols and provides
    real-time network health status, metrics, failure detection, and intelligent
    fallback mechanisms for degraded connectivity scenarios.
    """

    def __init__(self, config: ConfigManager):
        """Initialize network monitor.

        Args:
            config: Configuration manager instance
        """
        self.config = config
        self.logger = logging.getLogger("network_monitor")
        self._lock = Lock()

        # Monitoring state
        self.running = False
        self.monitor_thread: Thread | None = None

        # Network targets
        self.targets: list[NetworkTarget] = []
        self._setup_default_targets()

        # Metrics for each target
        self.target_metrics: dict[str, NetworkMetrics] = {}
        for target in self.targets:
            self.target_metrics[target.name] = NetworkMetrics()

        # Overall network status and monitoring mode
        self.overall_status = NetworkStatus.UNKNOWN
        self.monitoring_mode = MonitoringMode.NORMAL
        self.status_last_updated = datetime.now()

        # Fallback strategy configuration
        self.fallback_strategy = FallbackStrategy()
        self._load_fallback_config()

        # Adaptive monitoring state
        self.current_interval = self.fallback_strategy.normal_interval
        self.last_mode_change = datetime.now()
        self.mode_change_count = 0

        # Configuration
        self.check_interval = getattr(config, "network_check_interval", 30)
        self.failure_threshold = getattr(config, "network_failure_threshold", 3)
        self.recovery_threshold = getattr(config, "network_recovery_threshold", 2)

        self.logger.info("Network monitor initialized with %d targets and fallback strategies", len(self.targets))

    def _load_fallback_config(self) -> None:
        """Load fallback strategy configuration from config manager."""
        # Load configuration values if available
        if hasattr(self.config, "network_fallback_strategy"):
            strategy_config = self.config.network_fallback_strategy

            # Update fallback strategy with config values
            for key, value in strategy_config.items():
                if hasattr(self.fallback_strategy, key):
                    setattr(self.fallback_strategy, key, value)

        self.logger.info(
            "Fallback strategy configured: adaptive_intervals=%s, priority_monitoring=%s, endpoint_fallback=%s",
            self.fallback_strategy.enable_adaptive_backoff,
            self.fallback_strategy.enable_priority_monitoring,
            self.fallback_strategy.enable_endpoint_fallback,
        )

    def _setup_default_targets(self) -> None:
        """Setup default network connectivity targets with fallback hosts."""
        # Vimeo API endpoint
        vimeo_host = "api.vimeo.com"
        if hasattr(self.config, "vimeo_api_base_url"):
            # Extract host from API base URL
            import urllib.parse

            parsed = urllib.parse.urlparse(self.config.vimeo_api_base_url)
            if parsed.hostname:
                vimeo_host = parsed.hostname

        self.targets = [
            # Primary Vimeo API connectivity
            NetworkTarget(
                name="vimeo_api",
                host=vimeo_host,
                port=443,
                timeout=10.0,
                protocol="https",
                critical=True,
                priority=1,
                fallback_hosts=["player.vimeo.com", "secure-b.vimeocdn.com"],
            ),
            # DNS resolution test
            NetworkTarget(
                name="dns_google",
                host="8.8.8.8",
                port=53,
                timeout=5.0,
                protocol="tcp",
                critical=True,
                priority=1,
                fallback_hosts=["8.8.4.4", "1.1.1.1"],
            ),
            # General internet connectivity
            NetworkTarget(
                name="internet_cloudflare",
                host="1.1.1.1",
                port=80,
                timeout=5.0,
                protocol="tcp",
                critical=False,
                priority=2,
                fallback_hosts=["8.8.8.8", "208.67.222.222"],
            ),
            # HTTP connectivity test
            NetworkTarget(
                name="http_test",
                host="httpbin.org",
                port=80,
                timeout=8.0,
                protocol="http",
                critical=False,
                priority=3,
                fallback_hosts=["postman-echo.com", "reqres.in"],
            ),
        ]

    def add_target(self, target: NetworkTarget) -> None:
        """Add a network monitoring target."""
        with self._lock:
            self.targets.append(target)
            self.target_metrics[target.name] = NetworkMetrics()
            self.logger.info(
                "Added network target: %s (%s:%d) priority=%d critical=%s",
                target.name,
                target.host,
                target.port,
                target.priority,
                target.critical,
            )

    def remove_target(self, target_name: str) -> bool:
        """Remove a network monitoring target.

        Args:
            target_name: Name of target to remove

        Returns:
            True if target was removed, False if not found
        """
        with self._lock:
            for i, target in enumerate(self.targets):
                if target.name == target_name:
                    del self.targets[i]
                    del self.target_metrics[target_name]
                    self.logger.info("Removed network target: %s", target_name)
                    return True
            return False

    def start_monitoring(self) -> None:
        """Start network monitoring in background thread."""
        if self.running:
            self.logger.warning("Network monitoring already running")
            return

        self.running = True
        self.monitor_thread = Thread(target=self._monitoring_loop, daemon=True, name="NetworkMonitor")
        self.monitor_thread.start()
        self.logger.info("Network monitoring started with fallback strategies enabled")

    def stop_monitoring(self) -> None:
        """Stop network monitoring."""
        if not self.running:
            return

        self.running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=10.0)

        self.logger.info("Network monitoring stopped")

    def _monitoring_loop(self) -> None:
        """Main monitoring loop running in background thread with adaptive intervals."""
        while self.running:
            try:
                # Run connectivity tests based on current mode
                self._run_adaptive_connectivity_tests()

                # Update overall status and monitoring mode
                self._update_overall_status()
                self._update_monitoring_mode()

                # Use adaptive interval based on current mode
                sleep_interval = self._get_adaptive_interval()
                time.sleep(sleep_interval)

            except Exception as e:
                self.logger.exception("Error in network monitoring loop: %s", str(e))
                time.sleep(self.fallback_strategy.normal_interval)

    def _run_adaptive_connectivity_tests(self) -> None:
        """Run connectivity tests with adaptive target selection based on monitoring mode."""
        targets_to_test = self._get_targets_for_current_mode()

        for target in targets_to_test:
            try:
                test_result = self._test_target_with_fallback(target)
                self._update_target_metrics(target.name, test_result)
            except Exception as e:
                self.logger.error("Error testing target %s: %s", target.name, str(e))
                # Record as failed test
                failed_test = ConnectivityTest(success=False, response_time=0.0, error=str(e), timestamp=datetime.now())
                self._update_target_metrics(target.name, failed_test)

    def _get_targets_for_current_mode(self) -> list[NetworkTarget]:
        """Get list of targets to test based on current monitoring mode and fallback strategy."""
        if not self.fallback_strategy.enable_priority_monitoring:
            return self.targets

        if self.monitoring_mode == MonitoringMode.FAILURE and self.fallback_strategy.critical_only_in_failure:
            # In failure mode, only test critical targets to reduce load
            critical_targets = [t for t in self.targets if t.critical]
            self.logger.debug("Failure mode: testing only %d critical targets", len(critical_targets))
            return critical_targets
        elif self.monitoring_mode == MonitoringMode.DEGRADED:
            # In degraded mode, prioritize critical and high-priority targets
            priority_targets = [t for t in self.targets if t.critical or t.priority <= 2]
            self.logger.debug("Degraded mode: testing %d priority targets", len(priority_targets))
            return priority_targets
        else:
            # Normal and recovery modes: test all targets
            return self.targets

    def _test_target_with_fallback(self, target: NetworkTarget) -> ConnectivityTest:
        """Test connectivity to a target with fallback host support."""
        # First try the primary host
        primary_result = self._test_target_connectivity(target)

        # If primary succeeds or fallback is disabled, return primary result
        if primary_result.success or not self.fallback_strategy.enable_endpoint_fallback:
            return primary_result

        # If primary fails and we have fallback hosts, try them
        if target.fallback_hosts:
            self.logger.debug(
                "Primary host %s failed, trying %d fallback hosts", target.host, len(target.fallback_hosts)
            )

            for fallback_host in target.fallback_hosts:
                # Create temporary target with fallback host
                fallback_target = NetworkTarget(
                    name=f"{target.name}_fallback",
                    host=fallback_host,
                    port=target.port,
                    timeout=target.timeout * self.fallback_strategy.fallback_timeout_multiplier,
                    protocol=target.protocol,
                    critical=target.critical,
                    priority=target.priority,
                )

                fallback_result = self._test_target_connectivity(fallback_target)
                if fallback_result.success:
                    self.logger.info("Fallback host %s succeeded for target %s", fallback_host, target.name)
                    # Return success but with fallback notation
                    return ConnectivityTest(
                        success=True,
                        response_time=fallback_result.response_time,
                        error=f"fallback:{fallback_host}",
                        timestamp=fallback_result.timestamp,
                    )

        # All attempts failed, return original failure
        return primary_result

    def _get_adaptive_interval(self) -> float:
        """Get adaptive monitoring interval based on current mode and fallback strategy."""
        if not self.fallback_strategy.enable_adaptive_backoff:
            return self.check_interval

        base_interval = {
            MonitoringMode.NORMAL: self.fallback_strategy.normal_interval,
            MonitoringMode.DEGRADED: self.fallback_strategy.degraded_interval,
            MonitoringMode.FAILURE: self.fallback_strategy.failure_interval,
            MonitoringMode.RECOVERY: self.fallback_strategy.recovery_interval,
        }.get(self.monitoring_mode, self.fallback_strategy.normal_interval)

        # Apply additional backoff if we've had recent mode changes
        time_since_change = (datetime.now() - self.last_mode_change).total_seconds()
        if time_since_change < 300:  # Within 5 minutes of mode change
            backoff_factor = min(1.0 + (self.mode_change_count * 0.2), self.fallback_strategy.max_backoff_multiplier)
            return base_interval * backoff_factor

        return base_interval

    def _update_monitoring_mode(self) -> None:
        """Update monitoring mode based on overall network status and implement mode transitions."""
        old_mode = self.monitoring_mode

        # Determine new mode based on status
        if self.overall_status == NetworkStatus.HEALTHY:
            new_mode = MonitoringMode.NORMAL
        elif self.overall_status == NetworkStatus.DEGRADED:
            new_mode = MonitoringMode.DEGRADED
        elif self.overall_status in [NetworkStatus.FAILING, NetworkStatus.OFFLINE]:
            new_mode = MonitoringMode.FAILURE
        else:
            new_mode = MonitoringMode.NORMAL  # Default for unknown status

        # Check for recovery mode
        if old_mode == MonitoringMode.FAILURE and new_mode == MonitoringMode.NORMAL:
            new_mode = MonitoringMode.RECOVERY
        elif self.monitoring_mode == MonitoringMode.RECOVERY and new_mode == MonitoringMode.NORMAL:
            # Stay in recovery mode for a bit longer to ensure stability
            recent_failures = any(metrics.consecutive_failures > 0 for metrics in self.target_metrics.values())
            if recent_failures:
                new_mode = MonitoringMode.RECOVERY

        # Update mode if changed
        if new_mode != old_mode:
            self.monitoring_mode = new_mode
            self.last_mode_change = datetime.now()
            self.mode_change_count += 1

            # Reset mode change count after successful period
            if new_mode == MonitoringMode.NORMAL:
                self.mode_change_count = max(0, self.mode_change_count - 1)

            self.logger.warning(
                "Network monitoring mode changed: %s -> %s (change count: %d)",
                old_mode.value,
                new_mode.value,
                self.mode_change_count,
            )

    def _test_target_connectivity(self, target: NetworkTarget) -> ConnectivityTest:
        """Test connectivity to a specific target.

        Args:
            target: Network target to test

        Returns:
            ConnectivityTest result
        """
        start_time = time.time()

        try:
            if target.protocol == "tcp":
                return self._test_tcp_connectivity(target, start_time)
            elif target.protocol in ["http", "https"]:
                return self._test_http_connectivity(target, start_time)
            elif target.protocol == "icmp":
                return self._test_icmp_connectivity(target, start_time)
            else:
                raise ValueError(f"Unsupported protocol: {target.protocol}")

        except Exception as e:
            response_time = time.time() - start_time
            return ConnectivityTest(success=False, response_time=response_time, error=str(e), timestamp=datetime.now())

    def _test_tcp_connectivity(self, target: NetworkTarget, start_time: float) -> ConnectivityTest:
        """Test TCP connectivity to target."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(target.timeout)

        try:
            result = sock.connect_ex((target.host, target.port))
            response_time = time.time() - start_time

            if result == 0:
                return ConnectivityTest(success=True, response_time=response_time, error=None, timestamp=datetime.now())
            else:
                return ConnectivityTest(
                    success=False,
                    response_time=response_time,
                    error=f"TCP connection failed (code: {result})",
                    timestamp=datetime.now(),
                )
        finally:
            sock.close()

    def _test_http_connectivity(self, target: NetworkTarget, start_time: float) -> ConnectivityTest:
        """Test HTTP/HTTPS connectivity to target."""
        url = f"{target.protocol}://{target.host}:{target.port}/"

        try:
            request = urllib.request.Request(url)
            request.add_header("User-Agent", "VimeoMonitor/1.0")

            with urllib.request.urlopen(request, timeout=target.timeout) as response:
                response_time = time.time() - start_time
                status_code = response.getcode()

                # Consider 2xx and 3xx as success
                if 200 <= status_code < 400:
                    return ConnectivityTest(
                        success=True, response_time=response_time, error=None, timestamp=datetime.now()
                    )
                else:
                    return ConnectivityTest(
                        success=False,
                        response_time=response_time,
                        error=f"HTTP error: {status_code}",
                        timestamp=datetime.now(),
                    )

        except urllib.error.HTTPError as e:
            response_time = time.time() - start_time
            return ConnectivityTest(
                success=False,
                response_time=response_time,
                error=f"HTTP error: {e.code} {e.reason}",
                timestamp=datetime.now(),
            )
        except Exception as e:
            response_time = time.time() - start_time
            return ConnectivityTest(success=False, response_time=response_time, error=str(e), timestamp=datetime.now())

    def _test_icmp_connectivity(self, target: NetworkTarget, start_time: float) -> ConnectivityTest:
        """Test ICMP (ping) connectivity to target."""
        try:
            # Use ping command (cross-platform)
            import platform

            system = platform.system().lower()

            if system == "windows":
                cmd = ["ping", "-n", "1", "-w", str(int(target.timeout * 1000)), target.host]
            else:
                cmd = ["ping", "-c", "1", "-W", str(int(target.timeout)), target.host]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=target.timeout + 1)

            response_time = time.time() - start_time

            if result.returncode == 0:
                return ConnectivityTest(success=True, response_time=response_time, error=None, timestamp=datetime.now())
            else:
                return ConnectivityTest(
                    success=False,
                    response_time=response_time,
                    error=f"Ping failed: {result.stderr.strip()}",
                    timestamp=datetime.now(),
                )

        except subprocess.TimeoutExpired:
            response_time = time.time() - start_time
            return ConnectivityTest(
                success=False, response_time=response_time, error="Ping timeout", timestamp=datetime.now()
            )
        except Exception as e:
            response_time = time.time() - start_time
            return ConnectivityTest(success=False, response_time=response_time, error=str(e), timestamp=datetime.now())

    def _update_target_metrics(self, target_name: str, test_result: ConnectivityTest) -> None:
        """Update metrics for a specific target with enhanced fallback tracking."""
        with self._lock:
            metrics = self.target_metrics[target_name]

            # Update basic counters
            metrics.total_tests += 1

            # Check if this was a fallback success
            is_fallback_success = (
                test_result.success and test_result.error and test_result.error.startswith("fallback:")
            )

            if test_result.success:
                metrics.successful_tests += 1
                metrics.consecutive_successes += 1
                metrics.consecutive_failures = 0
                metrics.last_success_time = test_result.timestamp

                if is_fallback_success:
                    fallback_host = test_result.error.split(":", 1)[1]
                    self.logger.info("Target %s recovered using fallback host %s", target_name, fallback_host)
            else:
                metrics.failed_tests += 1
                metrics.consecutive_failures += 1
                metrics.consecutive_successes = 0
                metrics.last_failure_time = test_result.timestamp

            # Add to recent tests
            metrics.recent_tests.append(test_result)

            # Update average response time
            successful_times = [t.response_time for t in metrics.recent_tests if t.success]
            if successful_times:
                metrics.average_response_time = sum(successful_times) / len(successful_times)

            # Update uptime percentage (based on recent tests)
            recent_successes = len([t for t in metrics.recent_tests if t.success])
            if len(metrics.recent_tests) > 0:
                metrics.uptime_percent = (recent_successes / len(metrics.recent_tests)) * 100.0

            # Update target status with adaptive thresholds
            degraded_threshold = self.fallback_strategy.degraded_threshold
            failure_threshold = self.fallback_strategy.failure_threshold
            recovery_threshold = self.fallback_strategy.recovery_threshold

            if metrics.consecutive_failures >= failure_threshold:
                metrics.current_status = NetworkStatus.FAILING
            elif metrics.consecutive_failures >= degraded_threshold:
                metrics.current_status = NetworkStatus.DEGRADED
            elif metrics.consecutive_successes >= recovery_threshold:
                metrics.current_status = NetworkStatus.HEALTHY

            # Log status changes with fallback context
            if test_result.success:
                if metrics.consecutive_successes == 1 and metrics.failed_tests > 0:
                    if is_fallback_success:
                        fallback_host = test_result.error.split(":", 1)[1]
                        self.logger.info(
                            "Target %s recovered via fallback %s after %d failures",
                            target_name,
                            fallback_host,
                            metrics.failed_tests,
                        )
                    else:
                        self.logger.info("Target %s recovered after %d failures", target_name, metrics.failed_tests)
            else:
                if metrics.consecutive_failures == 1:
                    self.logger.warning("Target %s failed: %s", target_name, test_result.error)
                elif metrics.consecutive_failures == failure_threshold:
                    self.logger.error(
                        "Target %s marked as FAILING after %d consecutive failures", target_name, failure_threshold
                    )

    def _update_overall_status(self) -> None:
        """Update overall network status based on all targets with enhanced fallback logic."""
        with self._lock:
            critical_failures = 0
            total_critical = 0
            any_degraded = False
            fallback_successes = 0

            for target in self.targets:
                metrics = self.target_metrics[target.name]

                # Count fallback successes from recent tests
                recent_fallback_successes = len([
                    t
                    for t in list(metrics.recent_tests)[-10:]
                    if t.success and t.error and t.error.startswith("fallback:")
                ])
                if recent_fallback_successes > 0:
                    fallback_successes += 1

                if target.critical:
                    total_critical += 1
                    if metrics.current_status == NetworkStatus.FAILING:
                        critical_failures += 1
                    elif metrics.current_status == NetworkStatus.DEGRADED:
                        any_degraded = True
                elif metrics.current_status in [NetworkStatus.DEGRADED, NetworkStatus.FAILING]:
                    any_degraded = True

            # Determine overall status with fallback considerations
            old_status = self.overall_status

            if total_critical > 0 and critical_failures >= total_critical:
                self.overall_status = NetworkStatus.OFFLINE
            elif critical_failures > 0:
                # If we have fallback successes, consider it degraded rather than failing
                if fallback_successes > 0:
                    self.overall_status = NetworkStatus.DEGRADED
                else:
                    self.overall_status = NetworkStatus.FAILING
            elif any_degraded or fallback_successes > 0:
                self.overall_status = NetworkStatus.DEGRADED
            else:
                self.overall_status = NetworkStatus.HEALTHY

            self.status_last_updated = datetime.now()

            # Log status changes with fallback context
            if old_status != self.overall_status:
                if fallback_successes > 0:
                    self.logger.warning(
                        "Network status changed: %s -> %s (%d targets using fallback)",
                        old_status.value,
                        self.overall_status.value,
                        fallback_successes,
                    )
                else:
                    self.logger.warning("Network status changed: %s -> %s", old_status.value, self.overall_status.value)

    def get_network_status(self) -> dict[str, Any]:
        """Get comprehensive network status information including fallback status.

        Returns:
            Dictionary containing network status and metrics with fallback information
        """
        with self._lock:
            target_statuses = {}
            for target in self.targets:
                metrics = self.target_metrics[target.name]

                # Check for recent fallback usage
                recent_fallbacks = [
                    t
                    for t in list(metrics.recent_tests)[-10:]
                    if t.success and t.error and t.error.startswith("fallback:")
                ]

                target_statuses[target.name] = {
                    "status": metrics.current_status.value,
                    "host": target.host,
                    "port": target.port,
                    "protocol": target.protocol,
                    "critical": target.critical,
                    "priority": target.priority,
                    "success_rate": round(metrics.success_rate_percent, 1),
                    "average_response_time": round(metrics.average_response_time, 3),
                    "consecutive_failures": metrics.consecutive_failures,
                    "consecutive_successes": metrics.consecutive_successes,
                    "last_success": metrics.last_success_time.isoformat() if metrics.last_success_time else None,
                    "last_failure": metrics.last_failure_time.isoformat() if metrics.last_failure_time else None,
                    "total_tests": metrics.total_tests,
                    "uptime_percent": round(metrics.uptime_percent, 1),
                    "fallback_hosts": target.fallback_hosts,
                    "recent_fallback_usage": len(recent_fallbacks),
                    "using_fallback": len(recent_fallbacks) > 0,
                }

            return {
                "overall_status": self.overall_status.value,
                "monitoring_mode": self.monitoring_mode.value,
                "current_interval": self.current_interval,
                "status_updated": self.status_last_updated.isoformat(),
                "monitoring_active": self.running,
                "check_interval": self.check_interval,
                "targets": target_statuses,
                "fallback_strategy": {
                    "adaptive_intervals": self.fallback_strategy.enable_adaptive_backoff,
                    "priority_monitoring": self.fallback_strategy.enable_priority_monitoring,
                    "endpoint_fallback": self.fallback_strategy.enable_endpoint_fallback,
                    "mode_changes": self.mode_change_count,
                },
                "summary": {
                    "total_targets": len(self.targets),
                    "healthy_targets": len([
                        t for t in self.targets if self.target_metrics[t.name].current_status == NetworkStatus.HEALTHY
                    ]),
                    "failing_targets": len([
                        t for t in self.targets if self.target_metrics[t.name].current_status == NetworkStatus.FAILING
                    ]),
                    "critical_targets": len([t for t in self.targets if t.critical]),
                    "using_fallback": len([
                        t
                        for t in self.targets
                        if any(
                            test.success and test.error and test.error.startswith("fallback:")
                            for test in list(self.target_metrics[t.name].recent_tests)[-5:]
                        )
                    ]),
                },
            }

    def run_immediate_test(self) -> dict[str, Any]:
        """Run immediate connectivity test for all targets with fallback support.

        Returns:
            Dictionary with test results
        """
        self.logger.info("Running immediate network connectivity test with fallback support...")
        results = {}

        for target in self.targets:
            try:
                test_result = self._test_target_with_fallback(target)
                results[target.name] = {
                    "success": test_result.success,
                    "response_time": round(test_result.response_time, 3),
                    "error": test_result.error,
                    "timestamp": test_result.timestamp.isoformat(),
                    "used_fallback": test_result.success
                    and test_result.error
                    and test_result.error.startswith("fallback:"),
                }
            except Exception as e:
                results[target.name] = {
                    "success": False,
                    "response_time": 0.0,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                    "used_fallback": False,
                }

        return {"test_completed": datetime.now().isoformat(), "results": results}

    def get_health_summary(self) -> str:
        """Get a human-readable network health summary with fallback status."""
        status = self.get_network_status()
        overall = status["overall_status"].upper()
        mode = status["monitoring_mode"].upper()
        fallback_count = status["summary"]["using_fallback"]

        fallback_suffix = f" ({fallback_count} using fallback)" if fallback_count > 0 else ""
        mode_suffix = f" [{mode}]" if mode != "NORMAL" else ""

        if overall == "HEALTHY":
            return f"🟢 Network: {overall}{mode_suffix}{fallback_suffix} - All systems operational"
        elif overall == "DEGRADED":
            failing = status["summary"]["failing_targets"]
            total = status["summary"]["total_targets"]
            return (
                f"🟡 Network: {overall}{mode_suffix}{fallback_suffix} - {failing}/{total} targets experiencing issues"
            )
        elif overall == "FAILING":
            failing = status["summary"]["failing_targets"]
            total = status["summary"]["total_targets"]
            return f"🔴 Network: {overall}{mode_suffix}{fallback_suffix} - {failing}/{total} targets failing"
        elif overall == "OFFLINE":
            return f"❌ Network: {overall}{mode_suffix}{fallback_suffix} - Critical connectivity lost"
        else:
            return f"❓ Network: {overall}{mode_suffix}{fallback_suffix} - Status unknown"

    def get_fallback_status(self) -> dict[str, Any]:
        """Get detailed fallback strategy status and metrics."""
        return {
            "monitoring_mode": self.monitoring_mode.value,
            "current_interval": self.current_interval,
            "mode_change_count": self.mode_change_count,
            "time_since_mode_change": (datetime.now() - self.last_mode_change).total_seconds(),
            "strategy": {
                "adaptive_intervals": self.fallback_strategy.enable_adaptive_backoff,
                "priority_monitoring": self.fallback_strategy.enable_priority_monitoring,
                "endpoint_fallback": self.fallback_strategy.enable_endpoint_fallback,
                "critical_only_in_failure": self.fallback_strategy.critical_only_in_failure,
                "intervals": {
                    "normal": self.fallback_strategy.normal_interval,
                    "degraded": self.fallback_strategy.degraded_interval,
                    "failure": self.fallback_strategy.failure_interval,
                    "recovery": self.fallback_strategy.recovery_interval,
                },
                "thresholds": {
                    "degraded": self.fallback_strategy.degraded_threshold,
                    "failure": self.fallback_strategy.failure_threshold,
                    "recovery": self.fallback_strategy.recovery_threshold,
                },
            },
        }
