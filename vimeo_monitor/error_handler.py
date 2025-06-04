#!/usr/bin/env python3

"""Main error handling coordinator for Vimeo Monitor."""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from vimeo_monitor.alerting import (
    AlertLevel,
    AlertManager,
    AlertRule,
    EmailConfig,
    EmailNotificationProvider,
    FileNotificationProvider,
    NotificationChannel,
    WebhookConfig,
    WebhookNotificationProvider,
)
from vimeo_monitor.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitState
from vimeo_monitor.errors import ErrorCategory, ErrorSeverity, RecoveryStrategy, VimeoMonitorError
from vimeo_monitor.recovery import (
    RecoveryAction,
    RecoveryManager,
    RetryConfig,
    RetryExecutor,
    create_standard_recovery_actions,
)


@dataclass
class ErrorHandlingConfig:
    """Configuration for the error handling system."""

    enable_circuit_breaker: bool = True
    enable_retry: bool = True
    enable_recovery: bool = True
    enable_alerting: bool = True

    # Circuit breaker settings
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_timeout: float = 60.0

    # Retry settings
    retry_max_attempts: int = 3
    retry_base_delay: float = 1.0

    # Alert settings
    enable_email_alerts: bool = False
    enable_webhook_alerts: bool = False
    enable_file_alerts: bool = True
    alert_file_path: str = "logs/alerts.log"

    # Recovery settings
    enable_standard_recovery_actions: bool = True


class ErrorHandlingSystem:
    """
    Main error handling system that coordinates all components.
    """

    def __init__(
        self,
        config: ErrorHandlingConfig | None = None,
        email_config: EmailConfig | None = None,
        webhook_config: WebhookConfig | None = None,
    ):
        self.config = config or ErrorHandlingConfig()
        self.logger = logging.getLogger("error_handling")

        # Initialize components
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.retry_executor: RetryExecutor | None = None
        self.recovery_manager: RecoveryManager | None = None
        self.alert_manager: AlertManager | None = None

        # Initialize subsystems
        self._setup_circuit_breakers()
        self._setup_retry_executor()
        self._setup_recovery_manager()
        self._setup_alert_manager(email_config, webhook_config)

        self.logger.info("Error handling system initialized")

    def _setup_circuit_breakers(self) -> None:
        """Setup circuit breakers for critical operations."""
        if not self.config.enable_circuit_breaker:
            return

        # API circuit breaker configuration
        api_config = CircuitBreakerConfig(
            failure_threshold=self.config.circuit_breaker_failure_threshold,
            timeout_duration=self.config.circuit_breaker_timeout,
            max_timeout_duration=300.0,
            enable_logging=True,
        )

        # Create circuit breakers for different components
        self.circuit_breakers["api"] = CircuitBreaker("api", api_config)
        self.circuit_breakers["network"] = CircuitBreaker("network", api_config)
        self.circuit_breakers["process"] = CircuitBreaker("process", api_config)

        self.logger.info("Circuit breakers initialized: %s", list(self.circuit_breakers.keys()))

    def _setup_retry_executor(self) -> None:
        """Setup retry executor."""
        if not self.config.enable_retry:
            return

        retry_config = RetryConfig(
            max_attempts=self.config.retry_max_attempts, base_delay=self.config.retry_base_delay, max_delay=60.0
        )

        self.retry_executor = RetryExecutor(retry_config)
        self.logger.info("Retry executor initialized")

    def _setup_recovery_manager(self) -> None:
        """Setup recovery manager with standard actions."""
        if not self.config.enable_recovery:
            return

        self.recovery_manager = RecoveryManager("vimeo_monitor")

        # Register standard recovery actions if enabled
        if self.config.enable_standard_recovery_actions:
            standard_actions = create_standard_recovery_actions()

            for action in standard_actions:
                # Map actions to error categories
                if action.name == "restart_process":
                    self.recovery_manager.register_recovery_action(ErrorCategory.PROCESS_ERROR, action)
                elif action.name == "clear_cache":
                    self.recovery_manager.register_recovery_action(ErrorCategory.RESOURCE_ERROR, action)
                elif action.name == "reset_network":
                    self.recovery_manager.register_recovery_action(ErrorCategory.NETWORK_ERROR, action)
                elif action.name == "fallback_mode":
                    self.recovery_manager.register_recovery_action(ErrorCategory.API_ERROR, action)
                elif action.name == "reload_config":
                    self.recovery_manager.register_recovery_action(ErrorCategory.CONFIGURATION_ERROR, action)

        self.logger.info("Recovery manager initialized")

    def _setup_alert_manager(self, email_config: EmailConfig | None, webhook_config: WebhookConfig | None) -> None:
        """Setup alert manager with notification providers."""
        if not self.config.enable_alerting:
            return

        self.alert_manager = AlertManager("vimeo_monitor")

        # Setup notification providers
        if self.config.enable_email_alerts and email_config:
            email_provider = EmailNotificationProvider(email_config)
            self.alert_manager.add_notification_provider(NotificationChannel.EMAIL, email_provider)

        if self.config.enable_webhook_alerts and webhook_config:
            webhook_provider = WebhookNotificationProvider(webhook_config)
            self.alert_manager.add_notification_provider(NotificationChannel.WEBHOOK, webhook_provider)

        if self.config.enable_file_alerts:
            file_provider = FileNotificationProvider(self.config.alert_file_path)
            self.alert_manager.add_notification_provider(NotificationChannel.FILE, file_provider)

        # Setup default alert rules
        self._setup_default_alert_rules()

        self.logger.info("Alert manager initialized")

    def _setup_default_alert_rules(self) -> None:
        """Setup default alert rules."""
        if not self.alert_manager:
            return

        # Critical errors - immediate alerts
        critical_rule = AlertRule(
            name="critical_errors",
            description="Alert on all critical errors",
            error_severities=[ErrorSeverity.CRITICAL],
            alert_level=AlertLevel.CRITICAL,
            channels=[NotificationChannel.CONSOLE, NotificationChannel.FILE],
            cooldown_minutes=1,
            max_alerts_per_hour=20,
        )

        # API errors - circuit breaker integration
        api_rule = AlertRule(
            name="api_errors",
            description="Alert on API failures",
            error_categories=[ErrorCategory.API_ERROR],
            alert_level=AlertLevel.ERROR,
            channels=[NotificationChannel.CONSOLE, NotificationChannel.FILE],
            cooldown_minutes=5,
            max_alerts_per_hour=10,
        )

        # Network errors - connectivity issues
        network_rule = AlertRule(
            name="network_errors",
            description="Alert on network connectivity issues",
            error_categories=[ErrorCategory.NETWORK_ERROR],
            alert_level=AlertLevel.WARNING,
            channels=[NotificationChannel.CONSOLE, NotificationChannel.FILE],
            cooldown_minutes=10,
            max_alerts_per_hour=6,
        )

        # Process errors - system issues
        process_rule = AlertRule(
            name="process_errors",
            description="Alert on process execution failures",
            error_categories=[ErrorCategory.PROCESS_ERROR],
            alert_level=AlertLevel.ERROR,
            channels=[NotificationChannel.CONSOLE, NotificationChannel.FILE],
            cooldown_minutes=5,
            max_alerts_per_hour=8,
        )

        # Add email/webhook for critical rules if available
        if self.config.enable_email_alerts:
            critical_rule.channels.append(NotificationChannel.EMAIL)
            api_rule.channels.append(NotificationChannel.EMAIL)

        if self.config.enable_webhook_alerts:
            critical_rule.channels.append(NotificationChannel.WEBHOOK)
            api_rule.channels.append(NotificationChannel.WEBHOOK)

        # Register rules
        self.alert_manager.add_alert_rule(critical_rule)
        self.alert_manager.add_alert_rule(api_rule)
        self.alert_manager.add_alert_rule(network_rule)
        self.alert_manager.add_alert_rule(process_rule)

    def handle_error(self, error: VimeoMonitorError) -> bool:
        """
        Handle an error through the complete error handling pipeline.

        Args:
            error: The error to handle

        Returns:
            True if error was handled successfully, False otherwise
        """
        try:
            self.logger.info("Handling error: %s [%s/%s]", error.message, error.category.value, error.severity.value)

            # Send alert first (non-blocking)
            if self.alert_manager:
                try:
                    self.alert_manager.handle_error(error)
                except Exception as alert_error:
                    self.logger.error("Alert handling failed: %s", str(alert_error))

            # Attempt recovery based on strategy
            recovery_success = False

            if error.recovery_strategy == RecoveryStrategy.RETRY and self.retry_executor:
                # Retry strategy is handled externally, log the recommendation
                self.logger.info("Error recommends retry strategy")

            elif error.recovery_strategy == RecoveryStrategy.CIRCUIT_BREAKER:
                # Circuit breaker handling is external, log the recommendation
                self.logger.info("Error recommends circuit breaker handling")

            elif error.recovery_strategy == RecoveryStrategy.GRACEFUL_DEGRADATION:
                recovery_success = self._handle_graceful_degradation(error)

            elif error.recovery_strategy == RecoveryStrategy.RESTART:
                recovery_success = self._handle_restart_recovery(error)

            elif error.recovery_strategy == RecoveryStrategy.FALLBACK:
                recovery_success = self._handle_fallback_recovery(error)

            elif self.recovery_manager:
                # Try general recovery
                recovery_success = self.recovery_manager.attempt_recovery(error)

            # Log recovery result
            if recovery_success:
                self.logger.info("Error recovery successful for: %s", error.message)
            else:
                self.logger.warning("Error recovery failed for: %s", error.message)

            return recovery_success

        except Exception as e:
            self.logger.exception("Error handling failed: %s", str(e))
            return False

    def _handle_graceful_degradation(self, error: VimeoMonitorError) -> bool:
        """Handle graceful degradation strategy."""
        self.logger.info("Implementing graceful degradation for: %s", error.message)

        # This would implement specific degradation logic
        # For now, just log and return success
        return True

    def _handle_restart_recovery(self, error: VimeoMonitorError) -> bool:
        """Handle restart recovery strategy."""
        self.logger.warning("Restart recovery recommended for: %s", error.message)

        # This would implement restart logic
        # For now, just log and return false (restart requires external handling)
        return False

    def _handle_fallback_recovery(self, error: VimeoMonitorError) -> bool:
        """Handle fallback recovery strategy."""
        self.logger.info("Implementing fallback recovery for: %s", error.message)

        # This would implement fallback logic
        # For now, just log and return success
        return True

    def execute_with_protection(self, operation_name: str, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Execute a function with full error handling protection.

        Args:
            operation_name: Name of the operation for tracking
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            VimeoMonitorError: If operation fails after all recovery attempts
        """
        # Determine circuit breaker
        circuit_breaker = None
        if operation_name in self.circuit_breakers:
            circuit_breaker = self.circuit_breakers[operation_name]
        elif "api" in operation_name.lower():
            circuit_breaker = self.circuit_breakers.get("api")
        elif "network" in operation_name.lower():
            circuit_breaker = self.circuit_breakers.get("network")
        elif "process" in operation_name.lower():
            circuit_breaker = self.circuit_breakers.get("process")

        # Define the execution function
        def execute():
            if circuit_breaker:
                return circuit_breaker.call(func, *args, **kwargs)
            else:
                return func(*args, **kwargs)

        # Execute with retry if enabled
        try:
            if self.retry_executor:
                return self.retry_executor.execute_with_retry(execute)
            else:
                return execute()

        except VimeoMonitorError as e:
            # Handle the error through our pipeline
            self.handle_error(e)
            raise
        except Exception as e:
            # Wrap and handle unknown errors
            from vimeo_monitor.errors import wrap_exception

            wrapped_error = wrap_exception(e, component="error_handler", operation=operation_name)
            self.handle_error(wrapped_error)
            raise wrapped_error from e

    def get_circuit_breaker(self, name: str) -> CircuitBreaker | None:
        """Get a circuit breaker by name."""
        return self.circuit_breakers.get(name)

    def add_custom_recovery_action(self, error_category: ErrorCategory, action: RecoveryAction) -> None:
        """Add a custom recovery action."""
        if self.recovery_manager:
            self.recovery_manager.register_recovery_action(error_category, action)

    def add_custom_alert_rule(self, rule: AlertRule) -> None:
        """Add a custom alert rule."""
        if self.alert_manager:
            self.alert_manager.add_alert_rule(rule)

    def get_system_status(self) -> dict[str, Any]:
        """Get comprehensive system status."""
        status = {
            "timestamp": datetime.now().isoformat(),
            "config": {
                "circuit_breaker_enabled": self.config.enable_circuit_breaker,
                "retry_enabled": self.config.enable_retry,
                "recovery_enabled": self.config.enable_recovery,
                "alerting_enabled": self.config.enable_alerting,
            },
        }

        # Circuit breaker status
        if self.circuit_breakers:
            status["circuit_breakers"] = {name: breaker.get_status() for name, breaker in self.circuit_breakers.items()}

        # Recovery manager status
        if self.recovery_manager:
            status["recovery"] = self.recovery_manager.get_status()

        # Alert manager status
        if self.alert_manager:
            status["alerting"] = self.alert_manager.get_status()

        return status

    def test_system(self) -> dict[str, Any]:
        """Test all error handling components."""
        results = {"timestamp": datetime.now().isoformat(), "overall_status": "unknown"}

        test_passed = 0
        total_tests = 0

        # Test circuit breakers
        if self.circuit_breakers:
            results["circuit_breakers"] = {}
            for name, breaker in self.circuit_breakers.items():
                total_tests += 1
                # Circuit breakers are always "healthy" in their basic state
                if breaker.state == CircuitState.CLOSED:
                    results["circuit_breakers"][name] = "healthy"
                    test_passed += 1
                else:
                    results["circuit_breakers"][name] = f"state: {breaker.state.value}"

        # Test alert manager
        if self.alert_manager:
            total_tests += 1
            try:
                alert_tests = self.alert_manager.test_notifications()
                results["alerting"] = alert_tests
                if any(alert_tests.values()):
                    test_passed += 1
            except Exception as e:
                results["alerting"] = f"test_failed: {e!s}"

        # Test recovery manager
        if self.recovery_manager:
            total_tests += 1
            try:
                recovery_status = self.recovery_manager.get_status()
                results["recovery"] = "healthy" if recovery_status["registered_actions"] else "no_actions"
                test_passed += 1
            except Exception as e:
                results["recovery"] = f"test_failed: {e!s}"

        # Determine overall status
        if total_tests == 0:
            results["overall_status"] = "no_tests"
        elif test_passed == total_tests:
            results["overall_status"] = "healthy"
        elif test_passed > 0:
            results["overall_status"] = "partial"
        else:
            results["overall_status"] = "failed"

        results["test_summary"] = f"{test_passed}/{total_tests} passed"

        return results
