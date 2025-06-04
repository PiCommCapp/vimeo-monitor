#!/usr/bin/env python3

"""Advanced error handling framework for Vimeo Monitor."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ErrorSeverity(Enum):
    """Error severity levels for classification and handling."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categories of errors for specialized handling."""

    API_ERROR = "api_error"
    NETWORK_ERROR = "network_error"
    CONFIGURATION_ERROR = "configuration_error"
    PROCESS_ERROR = "process_error"
    FILESYSTEM_ERROR = "filesystem_error"
    VALIDATION_ERROR = "validation_error"
    RESOURCE_ERROR = "resource_error"
    UNKNOWN_ERROR = "unknown_error"


class RecoveryStrategy(Enum):
    """Recovery strategies for different error types."""

    RETRY = "retry"
    FALLBACK = "fallback"
    RESTART = "restart"
    ALERT_ONLY = "alert_only"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    CIRCUIT_BREAKER = "circuit_breaker"


@dataclass
class ErrorContext:
    """Context information for error handling."""

    timestamp: datetime = field(default_factory=datetime.now)
    component: str = "unknown"
    operation: str = "unknown"
    attempts: int = 0
    last_attempt: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    user_data: dict[str, Any] = field(default_factory=dict)


class VimeoMonitorError(Exception):
    """Base exception class for Vimeo Monitor errors."""

    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN_ERROR,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        recovery_strategy: RecoveryStrategy = RecoveryStrategy.ALERT_ONLY,
        context: ErrorContext | None = None,
        original_exception: Exception | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.recovery_strategy = recovery_strategy
        self.context = context or ErrorContext()
        self.original_exception = original_exception
        self.timestamp = datetime.now()

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for logging/reporting."""
        return {
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "recovery_strategy": self.recovery_strategy.value,
            "timestamp": self.timestamp.isoformat(),
            "component": self.context.component,
            "operation": self.context.operation,
            "attempts": self.context.attempts,
            "metadata": self.context.metadata,
            "original_exception": str(self.original_exception) if self.original_exception else None,
        }


class APIError(VimeoMonitorError):
    """API-related errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        endpoint: str | None = None,
        recovery_strategy: RecoveryStrategy = RecoveryStrategy.CIRCUIT_BREAKER,
        **kwargs: Any,
    ):
        super().__init__(message, category=ErrorCategory.API_ERROR, recovery_strategy=recovery_strategy, **kwargs)
        self.status_code = status_code
        self.endpoint = endpoint
        if self.context:
            self.context.metadata.update({"status_code": status_code, "endpoint": endpoint})


class NetworkError(VimeoMonitorError):
    """Network-related errors."""

    def __init__(self, message: str, recovery_strategy: RecoveryStrategy = RecoveryStrategy.RETRY, **kwargs: Any):
        super().__init__(
            message,
            category=ErrorCategory.NETWORK_ERROR,
            severity=ErrorSeverity.HIGH,
            recovery_strategy=recovery_strategy,
            **kwargs,
        )


class ProcessError(VimeoMonitorError):
    """Process/system execution errors."""

    def __init__(
        self,
        message: str,
        process_name: str | None = None,
        exit_code: int | None = None,
        recovery_strategy: RecoveryStrategy = RecoveryStrategy.RESTART,
        **kwargs: Any,
    ):
        super().__init__(
            message,
            category=ErrorCategory.PROCESS_ERROR,
            severity=ErrorSeverity.HIGH,
            recovery_strategy=recovery_strategy,
            **kwargs,
        )
        self.process_name = process_name
        self.exit_code = exit_code
        if self.context:
            self.context.metadata.update({"process_name": process_name, "exit_code": exit_code})


class ConfigurationError(VimeoMonitorError):
    """Configuration-related errors."""

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        config_value: str | None = None,
        recovery_strategy: RecoveryStrategy = RecoveryStrategy.ALERT_ONLY,
        **kwargs: Any,
    ):
        super().__init__(
            message,
            category=ErrorCategory.CONFIGURATION_ERROR,
            severity=ErrorSeverity.CRITICAL,
            recovery_strategy=recovery_strategy,
            **kwargs,
        )
        self.config_key = config_key
        self.config_value = config_value
        if self.context:
            self.context.metadata.update({"config_key": config_key, "config_value": config_value})


class FilesystemError(VimeoMonitorError):
    """Filesystem-related errors."""

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        operation: str | None = None,
        recovery_strategy: RecoveryStrategy = RecoveryStrategy.FALLBACK,
        **kwargs: Any,
    ):
        super().__init__(
            message, category=ErrorCategory.FILESYSTEM_ERROR, recovery_strategy=recovery_strategy, **kwargs
        )
        self.file_path = file_path
        self.operation = operation
        if self.context:
            self.context.metadata.update({"file_path": file_path, "operation": operation})


class ValidationError(VimeoMonitorError):
    """Data validation errors."""

    def __init__(
        self,
        message: str,
        field_name: str | None = None,
        field_value: Any | None = None,
        recovery_strategy: RecoveryStrategy = RecoveryStrategy.GRACEFUL_DEGRADATION,
        **kwargs: Any,
    ):
        super().__init__(
            message, category=ErrorCategory.VALIDATION_ERROR, recovery_strategy=recovery_strategy, **kwargs
        )
        self.field_name = field_name
        self.field_value = field_value
        if self.context:
            self.context.metadata.update({"field_name": field_name, "field_value": str(field_value)})


class ResourceError(VimeoMonitorError):
    """Resource availability/exhaustion errors."""

    def __init__(
        self,
        message: str,
        resource_type: str | None = None,
        recovery_strategy: RecoveryStrategy = RecoveryStrategy.GRACEFUL_DEGRADATION,
        **kwargs: Any,
    ):
        super().__init__(
            message,
            category=ErrorCategory.RESOURCE_ERROR,
            severity=ErrorSeverity.HIGH,
            recovery_strategy=recovery_strategy,
            **kwargs,
        )
        self.resource_type = resource_type
        if self.context:
            self.context.metadata.update({"resource_type": resource_type})


class ErrorFormatter:
    """Utility class for formatting error messages and reports."""

    @staticmethod
    def format_error_summary(error: VimeoMonitorError) -> str:
        """Format a concise error summary."""
        return (
            f"[{error.severity.value.upper()}] {error.category.value}: {error.message} "
            f"(Component: {error.context.component}, Operation: {error.context.operation})"
        )

    @staticmethod
    def format_error_details(error: VimeoMonitorError) -> str:
        """Format detailed error information."""
        details = [
            f"Error: {error.message}",
            f"Category: {error.category.value}",
            f"Severity: {error.severity.value}",
            f"Recovery Strategy: {error.recovery_strategy.value}",
            f"Timestamp: {error.timestamp.isoformat()}",
            f"Component: {error.context.component}",
            f"Operation: {error.context.operation}",
            f"Attempts: {error.context.attempts}",
        ]

        if error.context.metadata:
            details.append("Metadata:")
            for key, value in error.context.metadata.items():
                details.append(f"  {key}: {value}")

        if error.original_exception:
            details.append(f"Original Exception: {error.original_exception}")

        return "\n".join(details)

    @staticmethod
    def format_error_log_entry(error: VimeoMonitorError) -> str:
        """Format error for structured logging."""
        return (
            f"{error.category.value}|{error.severity.value}|{error.context.component}|"
            f"{error.context.operation}|{error.context.attempts}|{error.message}"
        )


def create_error_context(component: str, operation: str, attempts: int = 0, **metadata: Any) -> ErrorContext:
    """Create an error context with the given parameters."""
    context = ErrorContext(component=component, operation=operation, attempts=attempts)
    context.metadata.update(metadata)
    return context


def wrap_exception(
    exception: Exception,
    component: str,
    operation: str,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    recovery_strategy: RecoveryStrategy = RecoveryStrategy.ALERT_ONLY,
) -> VimeoMonitorError:
    """Wrap a standard exception in our error framework."""
    context = create_error_context(component, operation)

    # Map common exception types to our categories
    if isinstance(exception, (ConnectionError, TimeoutError)):
        return NetworkError(
            str(exception), context=context, original_exception=exception, recovery_strategy=RecoveryStrategy.RETRY
        )
    elif isinstance(exception, FileNotFoundError):
        return FilesystemError(
            str(exception), context=context, original_exception=exception, recovery_strategy=RecoveryStrategy.FALLBACK
        )
    elif isinstance(exception, ValueError):
        return ValidationError(
            str(exception),
            context=context,
            original_exception=exception,
            recovery_strategy=RecoveryStrategy.GRACEFUL_DEGRADATION,
        )
    else:
        return VimeoMonitorError(
            str(exception),
            severity=severity,
            recovery_strategy=recovery_strategy,
            context=context,
            original_exception=exception,
        )
