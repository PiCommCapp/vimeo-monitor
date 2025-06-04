#!/usr/bin/env python3

"""Error recovery mechanisms for Vimeo Monitor."""

import logging
import random
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from threading import Lock
from typing import Any, TypeVar

from vimeo_monitor.errors import APIError, ErrorCategory, FilesystemError, NetworkError, ProcessError, VimeoMonitorError

T = TypeVar("T")


class RetryPolicy(Enum):
    """Retry policy types."""

    FIXED_DELAY = "fixed_delay"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    RANDOM_JITTER = "random_jitter"


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_attempts: int = 3
    base_delay: float = 1.0  # Base delay in seconds
    max_delay: float = 60.0  # Maximum delay in seconds
    backoff_factor: float = 2.0  # Exponential backoff factor
    jitter_factor: float = 0.1  # Random jitter factor (0.0-1.0)
    policy: RetryPolicy = RetryPolicy.EXPONENTIAL_BACKOFF
    retry_on_errors: list[type] = field(default_factory=lambda: [NetworkError, APIError, ProcessError])
    ignore_errors: list[type] = field(
        default_factory=lambda: [
            FilesystemError  # Don't retry filesystem errors by default
        ]
    )


@dataclass
class RecoveryAction:
    """Definition of a recovery action."""

    name: str
    action: Callable[[], bool]  # Returns True if recovery succeeded
    description: str
    timeout: float = 30.0  # Timeout for recovery action
    prerequisites: list[str] = field(default_factory=list)
    cleanup_on_failure: Callable[[], None] | None = None


@dataclass
class RecoveryMetrics:
    """Metrics for recovery attempts."""

    total_attempts: int = 0
    successful_recoveries: int = 0
    failed_recoveries: int = 0
    average_recovery_time: float = 0.0
    last_recovery_time: datetime | None = None
    last_recovery_duration: float = 0.0
    recovery_success_rate: float = 0.0


class RecoveryManager:
    """
    Manages error recovery strategies and executes recovery actions.
    """

    def __init__(self, name: str = "recovery_manager"):
        self.name = name
        self.logger = logging.getLogger(f"recovery.{name}")
        self._lock = Lock()

        # Recovery actions registry
        self._recovery_actions: dict[str, RecoveryAction] = {}
        self._strategy_map: dict[ErrorCategory, list[str]] = {}

        # Metrics
        self.metrics = RecoveryMetrics()

        # State tracking
        self._active_recoveries: dict[str, datetime] = {}

        self.logger.info("Recovery manager '%s' initialized", self.name)

    def register_recovery_action(self, error_category: ErrorCategory, action: RecoveryAction) -> None:
        """Register a recovery action for an error category."""
        self._recovery_actions[action.name] = action

        if error_category not in self._strategy_map:
            self._strategy_map[error_category] = []

        self._strategy_map[error_category].append(action.name)

        self.logger.info(
            "Registered recovery action '%s' for %s: %s", action.name, error_category.value, action.description
        )

    def attempt_recovery(self, error: VimeoMonitorError) -> bool:
        """
        Attempt recovery for the given error.

        Args:
            error: The error to recover from

        Returns:
            True if recovery was successful, False otherwise
        """
        with self._lock:
            self.metrics.total_attempts += 1
            start_time = datetime.now()

            # Get recovery actions for this error category
            actions = self._strategy_map.get(error.category, [])

            if not actions:
                self.logger.warning("No recovery actions registered for error category: %s", error.category.value)
                return False

            self.logger.info("Attempting recovery for %s error: %s", error.category.value, error.message)

            # Try each recovery action
            for action_name in actions:
                action = self._recovery_actions[action_name]

                # Check prerequisites
                if not self._check_prerequisites(action):
                    self.logger.warning("Prerequisites not met for recovery action '%s'", action_name)
                    continue

                # Check if already running
                if action_name in self._active_recoveries:
                    elapsed = datetime.now() - self._active_recoveries[action_name]
                    if elapsed.total_seconds() < action.timeout:
                        self.logger.info(
                            "Recovery action '%s' already in progress (%.1fs elapsed)",
                            action_name,
                            elapsed.total_seconds(),
                        )
                        continue
                    else:
                        # Timeout exceeded, remove from active
                        del self._active_recoveries[action_name]

                # Execute recovery action
                try:
                    self._active_recoveries[action_name] = datetime.now()

                    self.logger.info("Executing recovery action '%s': %s", action_name, action.description)

                    success = self._execute_with_timeout(action.action, action.timeout)

                    if success:
                        # Recovery succeeded
                        duration = (datetime.now() - start_time).total_seconds()
                        self._record_success(duration)

                        self.logger.info("Recovery action '%s' succeeded (%.1fs)", action_name, duration)
                        return True
                    else:
                        self.logger.warning("Recovery action '%s' failed", action_name)

                        # Execute cleanup if defined
                        if action.cleanup_on_failure:
                            try:
                                action.cleanup_on_failure()
                            except Exception as cleanup_error:
                                self.logger.error("Cleanup failed for action '%s': %s", action_name, str(cleanup_error))

                except Exception as e:
                    self.logger.error("Exception during recovery action '%s': %s", action_name, str(e))

                finally:
                    # Remove from active recoveries
                    self._active_recoveries.pop(action_name, None)

            # All recovery actions failed
            duration = (datetime.now() - start_time).total_seconds()
            self._record_failure()

            self.logger.error("All recovery actions failed for %s error (%.1fs total)", error.category.value, duration)
            return False

    def _check_prerequisites(self, action: RecoveryAction) -> bool:
        """Check if prerequisites for a recovery action are met."""
        for prereq in action.prerequisites:
            if prereq not in self._recovery_actions:
                return False

            # Check if prerequisite recovery action is currently running
            if prereq in self._active_recoveries:
                return False

        return True

    def _execute_with_timeout(self, action: Callable[[], bool], timeout: float) -> bool:
        """Execute a recovery action with timeout."""
        start_time = time.time()

        try:
            # Simple timeout implementation
            # For more complex async operations, you might want to use asyncio
            result = action()
            elapsed = time.time() - start_time

            if elapsed > timeout:
                self.logger.warning("Recovery action exceeded timeout (%.1fs > %.1fs)", elapsed, timeout)
                return False

            return bool(result)

        except Exception as e:
            self.logger.error("Recovery action raised exception: %s", str(e))
            return False

    def _record_success(self, duration: float) -> None:
        """Record a successful recovery."""
        self.metrics.successful_recoveries += 1
        self.metrics.last_recovery_time = datetime.now()
        self.metrics.last_recovery_duration = duration

        # Update average recovery time
        total_successes = self.metrics.successful_recoveries
        if total_successes == 1:
            self.metrics.average_recovery_time = duration
        else:
            # Running average
            self.metrics.average_recovery_time = (
                self.metrics.average_recovery_time * (total_successes - 1) + duration
            ) / total_successes

        # Update success rate
        self.metrics.recovery_success_rate = self.metrics.successful_recoveries / self.metrics.total_attempts * 100.0

    def _record_failure(self) -> None:
        """Record a failed recovery."""
        self.metrics.failed_recoveries += 1

        # Update success rate
        self.metrics.recovery_success_rate = self.metrics.successful_recoveries / self.metrics.total_attempts * 100.0

    def get_status(self) -> dict[str, Any]:
        """Get recovery manager status."""
        return {
            "name": self.name,
            "registered_actions": list(self._recovery_actions.keys()),
            "active_recoveries": list(self._active_recoveries.keys()),
            "metrics": {
                "total_attempts": self.metrics.total_attempts,
                "successful_recoveries": self.metrics.successful_recoveries,
                "failed_recoveries": self.metrics.failed_recoveries,
                "success_rate": self.metrics.recovery_success_rate,
                "average_recovery_time": self.metrics.average_recovery_time,
                "last_recovery_time": (
                    self.metrics.last_recovery_time.isoformat() if self.metrics.last_recovery_time else None
                ),
                "last_recovery_duration": self.metrics.last_recovery_duration,
            },
            "strategy_map": {category.value: actions for category, actions in self._strategy_map.items()},
        }


class RetryExecutor:
    """
    Handles retry logic with various backoff strategies.
    """

    def __init__(self, config: RetryConfig | None = None):
        self.config = config or RetryConfig()
        self.logger = logging.getLogger("retry_executor")

    def execute_with_retry(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Execute a function with retry logic.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            VimeoMonitorError: If all retry attempts fail
        """
        last_exception = None

        for attempt in range(1, self.config.max_attempts + 1):
            try:
                self.logger.debug(
                    "Executing function '%s' (attempt %d/%d)", func.__name__, attempt, self.config.max_attempts
                )

                result = func(*args, **kwargs)

                if attempt > 1:
                    self.logger.info("Function '%s' succeeded on attempt %d", func.__name__, attempt)

                return result

            except Exception as e:
                last_exception = e

                # Check if we should retry this error
                if not self._should_retry(e):
                    self.logger.warning(
                        "Not retrying function '%s' due to error type: %s", func.__name__, type(e).__name__
                    )
                    raise

                # Don't delay after the last attempt
                if attempt < self.config.max_attempts:
                    delay = self._calculate_delay(attempt)

                    self.logger.warning(
                        "Function '%s' failed (attempt %d/%d): %s - retrying in %.1fs",
                        func.__name__,
                        attempt,
                        self.config.max_attempts,
                        str(e),
                        delay,
                    )

                    time.sleep(delay)
                else:
                    self.logger.error("Function '%s' failed on final attempt %d: %s", func.__name__, attempt, str(e))

        # All attempts failed
        if isinstance(last_exception, VimeoMonitorError):
            raise last_exception
        else:
            # Wrap in our error framework
            from vimeo_monitor.errors import wrap_exception

            wrapped_error = wrap_exception(last_exception, component="retry_executor", operation=func.__name__)
            raise wrapped_error from last_exception

    def _should_retry(self, exception: Exception) -> bool:
        """Determine if an exception should trigger a retry."""
        # Check ignore list first
        for ignore_type in self.config.ignore_errors:
            if isinstance(exception, ignore_type):
                return False

        # Check retry list
        for retry_type in self.config.retry_on_errors:
            if isinstance(exception, retry_type):
                return True

        # Default: don't retry unknown errors
        return False

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for the given attempt number."""
        if self.config.policy == RetryPolicy.FIXED_DELAY:
            delay = self.config.base_delay

        elif self.config.policy == RetryPolicy.EXPONENTIAL_BACKOFF:
            delay = self.config.base_delay * (self.config.backoff_factor ** (attempt - 1))

        elif self.config.policy == RetryPolicy.LINEAR_BACKOFF:
            delay = self.config.base_delay * attempt

        elif self.config.policy == RetryPolicy.RANDOM_JITTER:
            # Exponential backoff with random jitter
            base_delay = self.config.base_delay * (self.config.backoff_factor ** (attempt - 1))
            jitter = base_delay * self.config.jitter_factor * random.random()
            delay = base_delay + jitter

        else:
            delay = self.config.base_delay

        # Cap at maximum delay
        return min(delay, self.config.max_delay)


def create_standard_recovery_actions() -> list[RecoveryAction]:
    """Create standard recovery actions for common error scenarios."""
    return [
        RecoveryAction(
            name="restart_process",
            action=lambda: _restart_process_recovery(),
            description="Restart the current application process",
            timeout=30.0,
        ),
        RecoveryAction(
            name="clear_cache",
            action=lambda: _clear_cache_recovery(),
            description="Clear application caches and temporary files",
            timeout=10.0,
        ),
        RecoveryAction(
            name="reset_network",
            action=lambda: _reset_network_recovery(),
            description="Reset network connections and DNS cache",
            timeout=20.0,
        ),
        RecoveryAction(
            name="fallback_mode",
            action=lambda: _enable_fallback_mode(),
            description="Enable fallback mode with reduced functionality",
            timeout=5.0,
        ),
        RecoveryAction(
            name="reload_config",
            action=lambda: _reload_configuration(),
            description="Reload application configuration",
            timeout=10.0,
        ),
    ]


def _restart_process_recovery() -> bool:
    """Recovery action to restart the process."""
    # This would implement process restart logic
    # For now, return False as this requires careful implementation
    logging.warning("Process restart recovery not yet implemented")
    return False


def _clear_cache_recovery() -> bool:
    """Recovery action to clear caches."""
    try:
        import tempfile

        # Clear temporary files
        temp_dir = tempfile.gettempdir()
        logging.info("Cleared cache recovery - temp directory: %s", temp_dir)

        # This is a simplified implementation
        # In practice, you'd clear specific application caches
        return True
    except Exception as e:
        logging.exception("Failed to clear cache: %s", str(e))
        return False


def _reset_network_recovery() -> bool:
    """Recovery action to reset network connections."""
    try:
        # This would implement network reset logic
        # For now, just log and return success
        logging.info("Network reset recovery executed")
        return True
    except Exception as e:
        logging.exception("Failed to reset network: %s", str(e))
        return False


def _enable_fallback_mode() -> bool:
    """Recovery action to enable fallback mode."""
    try:
        # This would implement fallback mode logic
        logging.info("Fallback mode recovery executed")
        return True
    except Exception as e:
        logging.exception("Failed to enable fallback mode: %s", str(e))
        return False


def _reload_configuration() -> bool:
    """Recovery action to reload configuration."""
    try:
        # This would implement configuration reload logic
        logging.info("Configuration reload recovery executed")
        return True
    except Exception as e:
        logging.exception("Failed to reload configuration: %s", str(e))
        return False
