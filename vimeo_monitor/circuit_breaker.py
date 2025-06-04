#!/usr/bin/env python3

"""Circuit breaker pattern implementation for API failure handling."""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from threading import Lock
from typing import Any, Generic, TypeVar

from vimeo_monitor.errors import (
    ErrorCategory,
    ErrorSeverity,
    VimeoMonitorError,
    create_error_context,
)

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, not allowing calls
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""

    failure_threshold: int = 5  # Number of failures to open circuit
    success_threshold: int = 3  # Number of successes to close circuit
    timeout_duration: float = 60.0  # Seconds to wait before half-open
    max_timeout_duration: float = 300.0  # Maximum timeout duration
    timeout_backoff_factor: float = 1.5  # Exponential backoff factor
    health_check_interval: float = 30.0  # Seconds between health checks
    enable_logging: bool = True  # Enable circuit breaker logging


@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker monitoring."""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_failure_time: datetime | None = None
    last_success_time: datetime | None = None
    state_change_count: int = 0
    last_state_change: datetime | None = None
    current_timeout_duration: float = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_calls == 0:
            return 100.0
        return (self.successful_calls / self.total_calls) * 100.0

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate percentage."""
        return 100.0 - self.success_rate


class CircuitBreakerError(VimeoMonitorError):
    """Exception raised when circuit breaker is open."""

    def __init__(
        self,
        message: str = "Circuit breaker is open - service unavailable",
        circuit_name: str = "unknown",
        state: CircuitState = CircuitState.OPEN,
        metrics: CircuitBreakerMetrics | None = None,
    ):
        context = create_error_context(
            component="circuit_breaker",
            operation="call_blocked",
            circuit_name=circuit_name,
            circuit_state=state.value,
            failure_rate=metrics.failure_rate if metrics else 0.0,
        )
        super().__init__(message, category=ErrorCategory.API_ERROR, severity=ErrorSeverity.HIGH, context=context)
        self.circuit_name = circuit_name
        self.state = state
        self.metrics = metrics


class CircuitBreaker(Generic[T]):
    """
    Circuit breaker implementation for handling failures gracefully.

    The circuit breaker monitors failures and automatically opens to prevent
    cascading failures, then attempts recovery through a half-open state.
    """

    def __init__(
        self, name: str, config: CircuitBreakerConfig | None = None, health_check_func: Callable[[], bool] | None = None
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.health_check_func = health_check_func

        # Circuit state
        self._state = CircuitState.CLOSED
        self._lock = Lock()

        # Metrics
        self.metrics = CircuitBreakerMetrics()
        self.metrics.current_timeout_duration = self.config.timeout_duration

        # State tracking
        self._next_attempt_time: datetime | None = None
        self._last_health_check: datetime | None = None

        # Logging
        self.logger = logging.getLogger(f"circuit_breaker.{name}")

        if self.config.enable_logging:
            self.logger.info(
                "Circuit breaker '%s' initialized - threshold: %d, timeout: %.1fs",
                self.name,
                self.config.failure_threshold,
                self.config.timeout_duration,
            )

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self._state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (failing)."""
        return self._state == CircuitState.OPEN

    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open (testing)."""
        return self._state == CircuitState.HALF_OPEN

    def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Execute a function through the circuit breaker.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open
            VimeoMonitorError: If function raises an error
        """
        with self._lock:
            self._update_state()

            if self._state == CircuitState.OPEN:
                self._log_call_blocked()
                raise CircuitBreakerError(
                    f"Circuit breaker '{self.name}' is open",
                    circuit_name=self.name,
                    state=self._state,
                    metrics=self.metrics,
                )

            # Execute the function
            self.metrics.total_calls += 1

            try:
                result = func(*args, **kwargs)
                self._record_success()
                return result

            except Exception as e:
                self._record_failure(e)
                # Re-raise as our error type if not already
                if isinstance(e, VimeoMonitorError):
                    raise
                else:
                    # Wrap in our error framework
                    from vimeo_monitor.errors import wrap_exception

                    wrapped_error = wrap_exception(
                        e, component=f"circuit_breaker.{self.name}", operation="protected_call"
                    )
                    raise wrapped_error from e

    def _update_state(self) -> None:
        """Update circuit state based on current conditions."""
        now = datetime.now()

        if self._state == CircuitState.OPEN:
            # Check if timeout has elapsed
            if self._next_attempt_time and now >= self._next_attempt_time:
                self._transition_to_half_open()

        elif self._state == CircuitState.HALF_OPEN:
            # Check if we should close or open
            if self.metrics.consecutive_successes >= self.config.success_threshold:
                self._transition_to_closed()
            elif self.metrics.consecutive_failures >= self.config.failure_threshold:
                self._transition_to_open()

        elif self._state == CircuitState.CLOSED:
            # Check if we should open
            if self.metrics.consecutive_failures >= self.config.failure_threshold:
                self._transition_to_open()

        # Perform periodic health checks
        self._perform_health_check(now)

    def _record_success(self) -> None:
        """Record a successful call."""
        self.metrics.successful_calls += 1
        self.metrics.consecutive_successes += 1
        self.metrics.consecutive_failures = 0
        self.metrics.last_success_time = datetime.now()

        if self.config.enable_logging and self._state != CircuitState.CLOSED:
            self.logger.info(
                "Circuit breaker '%s' recorded success - consecutive: %d", self.name, self.metrics.consecutive_successes
            )

    def _record_failure(self, exception: Exception) -> None:
        """Record a failed call."""
        self.metrics.failed_calls += 1
        self.metrics.consecutive_failures += 1
        self.metrics.consecutive_successes = 0
        self.metrics.last_failure_time = datetime.now()

        if self.config.enable_logging:
            self.logger.warning(
                "Circuit breaker '%s' recorded failure - consecutive: %d, error: %s",
                self.name,
                self.metrics.consecutive_failures,
                str(exception),
            )

    def _transition_to_open(self) -> None:
        """Transition circuit to open state."""
        if self._state != CircuitState.OPEN:
            self._state = CircuitState.OPEN
            self.metrics.state_change_count += 1
            self.metrics.last_state_change = datetime.now()

            # Calculate next attempt time with exponential backoff
            self._next_attempt_time = datetime.now() + timedelta(seconds=self.metrics.current_timeout_duration)

            # Apply exponential backoff
            self.metrics.current_timeout_duration = min(
                self.metrics.current_timeout_duration * self.config.timeout_backoff_factor,
                self.config.max_timeout_duration,
            )

            if self.config.enable_logging:
                self.logger.error(
                    "Circuit breaker '%s' opened - failures: %d, next attempt: %s",
                    self.name,
                    self.metrics.consecutive_failures,
                    self._next_attempt_time.isoformat() if self._next_attempt_time else "unknown",
                )

    def _transition_to_half_open(self) -> None:
        """Transition circuit to half-open state."""
        if self._state != CircuitState.HALF_OPEN:
            self._state = CircuitState.HALF_OPEN
            self.metrics.state_change_count += 1
            self.metrics.last_state_change = datetime.now()
            self._next_attempt_time = None

            if self.config.enable_logging:
                self.logger.info("Circuit breaker '%s' half-opened - testing recovery", self.name)

    def _transition_to_closed(self) -> None:
        """Transition circuit to closed state."""
        if self._state != CircuitState.CLOSED:
            self._state = CircuitState.CLOSED
            self.metrics.state_change_count += 1
            self.metrics.last_state_change = datetime.now()

            # Reset timeout duration on successful recovery
            self.metrics.current_timeout_duration = self.config.timeout_duration

            if self.config.enable_logging:
                self.logger.info(
                    "Circuit breaker '%s' closed - service recovered, successes: %d",
                    self.name,
                    self.metrics.consecutive_successes,
                )

    def _perform_health_check(self, now: datetime) -> None:
        """Perform health check if configured and due."""
        if (
            self.health_check_func
            and self._state == CircuitState.OPEN
            and (
                not self._last_health_check
                or now - self._last_health_check >= timedelta(seconds=self.config.health_check_interval)
            )
        ):
            self._last_health_check = now

            try:
                if self.health_check_func():
                    if self.config.enable_logging:
                        self.logger.info("Circuit breaker '%s' health check passed - attempting recovery", self.name)
                    self._transition_to_half_open()
            except Exception as e:
                if self.config.enable_logging:
                    self.logger.debug("Circuit breaker '%s' health check failed: %s", self.name, str(e))

    def _log_call_blocked(self) -> None:
        """Log when a call is blocked by open circuit."""
        if self.config.enable_logging:
            self.logger.warning(
                "Circuit breaker '%s' blocked call - state: %s, failures: %d, success_rate: %.1f%%",
                self.name,
                self._state.value,
                self.metrics.consecutive_failures,
                self.metrics.success_rate,
            )

    def reset(self) -> None:
        """Manually reset circuit breaker to closed state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self.metrics.consecutive_failures = 0
            self.metrics.consecutive_successes = 0
            self.metrics.current_timeout_duration = self.config.timeout_duration
            self._next_attempt_time = None

            if self.config.enable_logging:
                self.logger.info("Circuit breaker '%s' manually reset", self.name)

    def force_open(self) -> None:
        """Manually force circuit breaker to open state."""
        with self._lock:
            self._transition_to_open()

            if self.config.enable_logging:
                self.logger.warning("Circuit breaker '%s' manually opened", self.name)

    def get_status(self) -> dict[str, Any]:
        """Get current circuit breaker status."""
        return {
            "name": self.name,
            "state": self._state.value,
            "metrics": {
                "total_calls": self.metrics.total_calls,
                "successful_calls": self.metrics.successful_calls,
                "failed_calls": self.metrics.failed_calls,
                "consecutive_failures": self.metrics.consecutive_failures,
                "consecutive_successes": self.metrics.consecutive_successes,
                "success_rate": self.metrics.success_rate,
                "failure_rate": self.metrics.failure_rate,
                "state_changes": self.metrics.state_change_count,
                "current_timeout": self.metrics.current_timeout_duration,
            },
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "success_threshold": self.config.success_threshold,
                "timeout_duration": self.config.timeout_duration,
                "max_timeout_duration": self.config.max_timeout_duration,
            },
            "next_attempt": self._next_attempt_time.isoformat() if self._next_attempt_time else None,
            "last_failure": self.metrics.last_failure_time.isoformat() if self.metrics.last_failure_time else None,
            "last_success": self.metrics.last_success_time.isoformat() if self.metrics.last_success_time else None,
        }
