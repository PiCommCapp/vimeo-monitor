#!/usr/bin/env python3

"""Error alerting and notification system for Vimeo Monitor."""

import json
import logging
import smtplib
import time
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from threading import Lock
from typing import Any

from vimeo_monitor.errors import ErrorCategory, ErrorFormatter, ErrorSeverity, VimeoMonitorError


class AlertLevel(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationChannel(Enum):
    """Available notification channels."""

    EMAIL = "email"
    WEBHOOK = "webhook"
    CONSOLE = "console"
    FILE = "file"


@dataclass
class AlertRule:
    """Definition of an alerting rule."""

    name: str
    description: str
    error_categories: list[ErrorCategory] = field(default_factory=list)
    error_severities: list[ErrorSeverity] = field(default_factory=list)
    alert_level: AlertLevel = AlertLevel.WARNING
    channels: list[NotificationChannel] = field(default_factory=list)
    cooldown_minutes: int = 5  # Minimum time between alerts
    max_alerts_per_hour: int = 10  # Rate limiting
    require_recovery: bool = False  # Send recovery notifications
    enabled: bool = True


@dataclass
class AlertMetrics:
    """Metrics for alert tracking."""

    total_alerts: int = 0
    alerts_by_level: dict[AlertLevel, int] = field(default_factory=dict)
    alerts_by_channel: dict[NotificationChannel, int] = field(default_factory=dict)
    suppressed_alerts: int = 0
    failed_deliveries: int = 0
    last_alert_time: datetime | None = None
    active_alerts: set[str] = field(default_factory=set)


@dataclass
class EmailConfig:
    """Email notification configuration."""

    smtp_server: str
    username: str
    password: str
    from_email: str
    smtp_port: int = 587
    to_emails: list[str] = field(default_factory=list)
    use_tls: bool = True
    subject_prefix: str = "[Vimeo Monitor Alert]"


@dataclass
class WebhookConfig:
    """Webhook notification configuration."""

    url: str
    method: str = "POST"
    headers: dict[str, str] = field(default_factory=dict)
    timeout: int = 10
    retry_attempts: int = 3


class NotificationProvider(ABC):
    """Abstract base class for notification providers."""

    @abstractmethod
    def send_notification(
        self, alert_level: AlertLevel, title: str, message: str, metadata: dict[str, Any] | None = None
    ) -> bool:
        """Send a notification. Returns True if successful."""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Test the notification provider connection."""
        pass


class EmailNotificationProvider(NotificationProvider):
    """Email notification provider."""

    def __init__(self, config: EmailConfig):
        self.config = config
        self.logger = logging.getLogger("alerting.email")

    def send_notification(
        self, alert_level: AlertLevel, title: str, message: str, metadata: dict[str, Any] | None = None
    ) -> bool:
        """Send email notification."""
        try:
            # Create email message
            msg = MIMEMultipart()
            msg["From"] = self.config.from_email
            msg["To"] = ", ".join(self.config.to_emails)
            msg["Subject"] = f"{self.config.subject_prefix} {alert_level.value.upper()}: {title}"

            # Create email body
            body = self._format_email_body(alert_level, title, message, metadata)
            msg.attach(MIMEText(body, "plain"))

            # Send email
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                if self.config.use_tls:
                    server.starttls()

                server.login(self.config.username, self.config.password)
                server.send_message(msg)

            self.logger.info("Email alert sent successfully to %d recipients", len(self.config.to_emails))
            return True

        except Exception as e:
            self.logger.error("Failed to send email alert: %s", str(e))
            return False

    def test_connection(self) -> bool:
        """Test email connection."""
        try:
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                if self.config.use_tls:
                    server.starttls()
                server.login(self.config.username, self.config.password)
            return True
        except Exception as e:
            self.logger.error("Email connection test failed: %s", str(e))
            return False

    def _format_email_body(
        self, alert_level: AlertLevel, title: str, message: str, metadata: dict[str, Any] | None
    ) -> str:
        """Format email body."""
        lines = [
            f"Alert Level: {alert_level.value.upper()}",
            f"Title: {title}",
            f"Time: {datetime.now().isoformat()}",
            "",
            "Message:",
            message,
            "",
        ]

        if metadata:
            lines.extend(["Additional Information:", json.dumps(metadata, indent=2, default=str), ""])

        lines.extend(["---", "This alert was generated by Vimeo Monitor", f"System: {self.config.from_email}"])

        return "\n".join(lines)


class WebhookNotificationProvider(NotificationProvider):
    """Webhook notification provider."""

    def __init__(self, config: WebhookConfig):
        self.config = config
        self.logger = logging.getLogger("alerting.webhook")

    def send_notification(
        self, alert_level: AlertLevel, title: str, message: str, metadata: dict[str, Any] | None = None
    ) -> bool:
        """Send webhook notification."""
        for attempt in range(self.config.retry_attempts):
            try:
                payload = {
                    "alert_level": alert_level.value,
                    "title": title,
                    "message": message,
                    "timestamp": datetime.now().isoformat(),
                    "metadata": metadata or {},
                }

                data = json.dumps(payload).encode("utf-8")

                # Create request
                req = urllib.request.Request(self.config.url, data=data, method=self.config.method)

                # Add headers
                req.add_header("Content-Type", "application/json")
                for key, value in self.config.headers.items():
                    req.add_header(key, value)

                # Send request
                with urllib.request.urlopen(req, timeout=self.config.timeout) as response:
                    if 200 <= response.status < 300:
                        self.logger.info("Webhook alert sent successfully (attempt %d)", attempt + 1)
                        return True
                    else:
                        self.logger.warning("Webhook returned status %d (attempt %d)", response.status, attempt + 1)

            except Exception as e:
                self.logger.warning("Webhook alert failed (attempt %d): %s", attempt + 1, str(e))
                if attempt < self.config.retry_attempts - 1:
                    time.sleep(2**attempt)  # Exponential backoff

        self.logger.error("All webhook attempts failed")
        return False

    def test_connection(self) -> bool:
        """Test webhook connection."""
        try:
            # Send a test payload
            test_payload = {"test": True, "timestamp": datetime.now().isoformat(), "message": "Connection test"}

            data = json.dumps(test_payload).encode("utf-8")
            req = urllib.request.Request(self.config.url, data=data, method=self.config.method)
            req.add_header("Content-Type", "application/json")

            for key, value in self.config.headers.items():
                req.add_header(key, value)

            with urllib.request.urlopen(req, timeout=self.config.timeout) as response:
                return 200 <= response.status < 300

        except Exception as e:
            self.logger.error("Webhook connection test failed: %s", str(e))
            return False


class ConsoleNotificationProvider(NotificationProvider):
    """Console notification provider."""

    def __init__(self):
        self.logger = logging.getLogger("alerting.console")

    def send_notification(
        self, alert_level: AlertLevel, title: str, message: str, metadata: dict[str, Any] | None = None
    ) -> bool:
        """Send console notification."""
        try:
            # Choose appropriate log level
            log_level = {
                AlertLevel.INFO: logging.INFO,
                AlertLevel.WARNING: logging.WARNING,
                AlertLevel.ERROR: logging.ERROR,
                AlertLevel.CRITICAL: logging.CRITICAL,
            }.get(alert_level, logging.WARNING)

            # Log the alert
            alert_text = f"ALERT [{alert_level.value.upper()}] {title}: {message}"
            self.logger.log(log_level, alert_text)

            if metadata:
                self.logger.log(log_level, "Alert metadata: %s", json.dumps(metadata, default=str))

            return True

        except Exception as e:
            print(f"Console alert failed: {e}")  # Fallback to print
            return False

    def test_connection(self) -> bool:
        """Test console connection (always succeeds)."""
        return True


class FileNotificationProvider(NotificationProvider):
    """File notification provider."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.logger = logging.getLogger("alerting.file")

    def send_notification(
        self, alert_level: AlertLevel, title: str, message: str, metadata: dict[str, Any] | None = None
    ) -> bool:
        """Send file notification."""
        try:
            alert_entry = {
                "timestamp": datetime.now().isoformat(),
                "alert_level": alert_level.value,
                "title": title,
                "message": message,
                "metadata": metadata or {},
            }

            with open(self.file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(alert_entry) + "\n")

            self.logger.debug("Alert written to file: %s", self.file_path)
            return True

        except Exception as e:
            self.logger.error("Failed to write alert to file: %s", str(e))
            return False

    def test_connection(self) -> bool:
        """Test file access."""
        try:
            with open(self.file_path, "a", encoding="utf-8") as f:
                pass  # Just test if we can open for append
            return True
        except Exception:
            return False


class AlertManager:
    """
    Manages error alerting and notifications.
    """

    def __init__(self, name: str = "alert_manager"):
        self.name = name
        self.logger = logging.getLogger(f"alerting.{name}")
        self._lock = Lock()

        # Alert rules and providers
        self._alert_rules: dict[str, AlertRule] = {}
        self._notification_providers: dict[NotificationChannel, NotificationProvider] = {}

        # Metrics and state tracking
        self.metrics = AlertMetrics()
        self._alert_history: dict[str, list[datetime]] = {}  # For rate limiting
        self._last_alert_time: dict[str, datetime] = {}  # For cooldown

        # Initialize default console provider
        self._notification_providers[NotificationChannel.CONSOLE] = ConsoleNotificationProvider()

        self.logger.info("Alert manager '%s' initialized", self.name)

    def add_notification_provider(self, channel: NotificationChannel, provider: NotificationProvider) -> None:
        """Add a notification provider."""
        self._notification_providers[channel] = provider
        self.logger.info("Added notification provider for channel: %s", channel.value)

    def add_alert_rule(self, rule: AlertRule) -> None:
        """Add an alert rule."""
        self._alert_rules[rule.name] = rule
        self.logger.info("Added alert rule: %s", rule.name)

    def handle_error(self, error: VimeoMonitorError) -> None:
        """Handle an error and potentially send alerts."""
        with self._lock:
            # Find matching alert rules
            matching_rules = self._find_matching_rules(error)

            if not matching_rules:
                self.logger.debug("No alert rules match error: %s", error.message)
                return

            # Process each matching rule
            for rule in matching_rules:
                if not rule.enabled:
                    continue

                # Check cooldown
                if not self._check_cooldown(rule):
                    self.logger.debug("Alert rule '%s' in cooldown period", rule.name)
                    self.metrics.suppressed_alerts += 1
                    continue

                # Check rate limiting
                if not self._check_rate_limit(rule):
                    self.logger.warning("Alert rule '%s' rate limit exceeded", rule.name)
                    self.metrics.suppressed_alerts += 1
                    continue

                # Send alert
                self._send_alert(rule, error)

    def _find_matching_rules(self, error: VimeoMonitorError) -> list[AlertRule]:
        """Find alert rules that match the given error."""
        matching_rules = []

        for rule in self._alert_rules.values():
            # Check error category match
            if rule.error_categories and error.category not in rule.error_categories:
                continue

            # Check error severity match
            if rule.error_severities and error.severity not in rule.error_severities:
                continue

            matching_rules.append(rule)

        return matching_rules

    def _check_cooldown(self, rule: AlertRule) -> bool:
        """Check if the rule is within cooldown period."""
        if rule.cooldown_minutes <= 0:
            return True

        last_alert = self._last_alert_time.get(rule.name)
        if not last_alert:
            return True

        cooldown_period = timedelta(minutes=rule.cooldown_minutes)
        return datetime.now() - last_alert >= cooldown_period

    def _check_rate_limit(self, rule: AlertRule) -> bool:
        """Check if the rule exceeds rate limit."""
        if rule.max_alerts_per_hour <= 0:
            return True

        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)

        # Get recent alerts for this rule
        recent_alerts = self._alert_history.get(rule.name, [])

        # Remove old alerts
        recent_alerts = [alert_time for alert_time in recent_alerts if alert_time > one_hour_ago]
        self._alert_history[rule.name] = recent_alerts

        return len(recent_alerts) < rule.max_alerts_per_hour

    def _send_alert(self, rule: AlertRule, error: VimeoMonitorError) -> None:
        """Send alert for the given rule and error."""
        # Prepare alert content
        title = f"{error.category.value}: {error.message[:100]}"
        message = ErrorFormatter.format_error_details(error)
        metadata = error.to_dict()

        # Track alert
        now = datetime.now()
        self._last_alert_time[rule.name] = now

        if rule.name not in self._alert_history:
            self._alert_history[rule.name] = []
        self._alert_history[rule.name].append(now)

        # Update metrics
        self.metrics.total_alerts += 1
        self.metrics.last_alert_time = now

        if rule.alert_level not in self.metrics.alerts_by_level:
            self.metrics.alerts_by_level[rule.alert_level] = 0
        self.metrics.alerts_by_level[rule.alert_level] += 1

        # Add to active alerts
        alert_id = f"{rule.name}_{error.category.value}_{int(now.timestamp())}"
        self.metrics.active_alerts.add(alert_id)

        # Send to all configured channels
        success_count = 0
        for channel in rule.channels:
            provider = self._notification_providers.get(channel)
            if not provider:
                self.logger.warning("No provider configured for channel: %s", channel.value)
                continue

            try:
                success = provider.send_notification(rule.alert_level, title, message, metadata)

                if success:
                    success_count += 1

                    # Update channel metrics
                    if channel not in self.metrics.alerts_by_channel:
                        self.metrics.alerts_by_channel[channel] = 0
                    self.metrics.alerts_by_channel[channel] += 1
                else:
                    self.metrics.failed_deliveries += 1

            except Exception as e:
                self.logger.error("Failed to send alert via %s: %s", channel.value, str(e))
                self.metrics.failed_deliveries += 1

        if success_count > 0:
            self.logger.info(
                "Alert sent successfully via %d/%d channels for rule '%s'", success_count, len(rule.channels), rule.name
            )
        else:
            self.logger.error("Failed to send alert via any channel for rule '%s'", rule.name)

    def test_notifications(self) -> dict[NotificationChannel, bool]:
        """Test all notification providers."""
        results = {}

        for channel, provider in self._notification_providers.items():
            try:
                results[channel] = provider.test_connection()
                self.logger.info("Notification test for %s: %s", channel.value, results[channel])
            except Exception as e:
                results[channel] = False
                self.logger.error("Notification test failed for %s: %s", channel.value, str(e))

        return results

    def get_status(self) -> dict[str, Any]:
        """Get alert manager status."""
        return {
            "name": self.name,
            "rules": {
                rule_name: {
                    "enabled": rule.enabled,
                    "channels": [ch.value for ch in rule.channels],
                    "alert_level": rule.alert_level.value,
                    "cooldown_minutes": rule.cooldown_minutes,
                    "max_alerts_per_hour": rule.max_alerts_per_hour,
                }
                for rule_name, rule in self._alert_rules.items()
            },
            "providers": list(self._notification_providers.keys()),
            "metrics": {
                "total_alerts": self.metrics.total_alerts,
                "suppressed_alerts": self.metrics.suppressed_alerts,
                "failed_deliveries": self.metrics.failed_deliveries,
                "alerts_by_level": {level.value: count for level, count in self.metrics.alerts_by_level.items()},
                "alerts_by_channel": {
                    channel.value: count for channel, count in self.metrics.alerts_by_channel.items()
                },
                "active_alerts": len(self.metrics.active_alerts),
                "last_alert_time": (self.metrics.last_alert_time.isoformat() if self.metrics.last_alert_time else None),
            },
        }
