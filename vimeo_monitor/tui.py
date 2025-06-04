#!/usr/bin/env python3

"""Terminal User Interface (TUI) for Vimeo Monitor using Textual."""

import logging
import sys
import time
from datetime import datetime
from typing import Any

import requests
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Log,
    Static,
    Switch,
    TabbedContent,
    TabPane,
)

# Import our monitoring components
try:
    from vimeo_monitor.config import ConfigManager, EnhancedConfigManager
    from vimeo_monitor.health import HealthMonitor
    from vimeo_monitor.network_monitor import NetworkMonitor
    from vimeo_monitor.performance import PerformanceOptimizer
except ImportError as e:
    logging.exception("Failed to import vimeo_monitor components: %s", e)
    sys.exit(1)


class ServiceStatusWidget(Static):
    """Widget showing service status information."""

    service_status: reactive[str] = reactive("Unknown")
    metrics_status: reactive[str] = reactive("Unknown")

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.border_title = "Service Status"

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Static(id="service_info")

    def watch_service_status(self, status: str) -> None:
        """Update service status display."""
        self.update_status_display()

    def watch_metrics_status(self, status: str) -> None:
        """Update metrics status display."""
        self.update_status_display()

    def update_status_display(self) -> None:
        """Update the status display."""
        service_color = "green" if "running" in self.service_status.lower() else "red"
        metrics_color = "green" if "accessible" in self.metrics_status.lower() else "red"

        content = f"""[bold]Service Status:[/bold] [{service_color}]{self.service_status}[/{service_color}]
[bold]Metrics Status:[/bold] [{metrics_color}]{self.metrics_status}[/{metrics_color}]
[bold]Last Updated:[/bold] {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"""

        service_info = self.query_one("#service_info", Static)
        service_info.update(content)


class MetricsWidget(Static):
    """Widget showing Prometheus metrics information."""

    metrics_data: reactive[dict[str, Any]] = reactive({})

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.border_title = "System Metrics"

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield DataTable(id="metrics_table")

    def on_mount(self) -> None:
        """Initialize the metrics table."""
        table = self.query_one("#metrics_table", DataTable)
        table.add_columns("Metric", "Value", "Unit")

    def watch_metrics_data(self, data: dict[str, Any]) -> None:
        """Update metrics display when data changes."""
        table = self.query_one("#metrics_table", DataTable)
        table.clear()

        if data:
            # Add system metrics
            if "system" in data:
                system = data["system"]
                table.add_row("CPU Usage", f"{system.get('cpu_percent', 0):.1f}", "%")
                table.add_row("Memory Usage", f"{system.get('memory_mb', 0):.1f}", "MB")
                table.add_row("Thread Count", str(system.get("threads", 0)), "")

            # Add API metrics
            if "api" in data:
                api = data["api"]
                table.add_row("API Requests", str(api.get("total_requests", 0)), "")
                table.add_row("API Failures", str(api.get("failed_requests", 0)), "")
                table.add_row("Cache Hit Rate", f"{api.get('cache_hit_rate', 0):.1f}", "%")

            # Add network metrics
            if "network" in data:
                network = data["network"]
                connectivity = "Online" if network.get("connectivity", False) else "Offline"
                table.add_row("Network Status", connectivity, "")
                table.add_row("Response Time", f"{network.get('response_time_ms', 0):.0f}", "ms")


class ConfigWidget(Static):
    """Widget for configuration management."""

    config_data: reactive[dict[str, Any]] = reactive({})

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.border_title = "Configuration"

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Vertical():
            yield Static("Key Configuration Settings:", id="config_header")
            yield DataTable(id="config_table")
            yield Horizontal(
                Button("Reload Config", id="reload_config", variant="primary"),
                Button("Edit Config", id="edit_config", variant="default"),
                classes="config_buttons",
            )

    def on_mount(self) -> None:
        """Initialize the configuration table."""
        table = self.query_one("#config_table", DataTable)
        table.add_columns("Setting", "Value", "Source")

    @on(Button.Pressed, "#reload_config")
    def reload_config(self) -> None:
        """Reload configuration."""
        self.app.post_message(ReloadConfigMessage())

    @on(Button.Pressed, "#edit_config")
    def edit_config(self) -> None:
        """Open configuration editor."""
        self.app.push_screen(ConfigEditScreen())

    def watch_config_data(self, data: dict[str, Any]) -> None:
        """Update configuration display."""
        table = self.query_one("#config_table", DataTable)
        table.clear()

        if data:
            # Show key configuration items
            key_configs = [
                (
                    "API Token",
                    data.get("vimeo_api_token", "***")[0:8] + "..." if data.get("vimeo_api_token") else "Not Set",
                ),
                ("Check Interval", f"{data.get('check_interval', 0)}s"),
                ("Metrics Enabled", str(data.get("enable_prometheus_metrics", False))),
                ("Metrics Port", str(data.get("prometheus_metrics_port", 8000))),
                ("Log Level", data.get("log_level", "INFO")),
                ("Network Monitoring", str(data.get("enable_network_monitoring", True))),
            ]

            for setting, value in key_configs:
                table.add_row(setting, value, "ENV/Config")


class LogWidget(Log):
    """Widget for displaying application logs."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.border_title = "Application Logs"


class ReloadConfigMessage:
    """Message to trigger configuration reload."""

    pass


class ConfigEditScreen(Static):
    """Screen for editing configuration."""

    DEFAULT_CSS = """
    ConfigEditScreen {
        align: center middle;
        background: $surface;
        border: thick $primary;
        width: 80;
        height: 24;
    }
    """

    def compose(self) -> ComposeResult:
        """Create the configuration editor."""
        with Vertical():
            yield Static("Configuration Editor", classes="header")
            yield Static("Edit key configuration values:", classes="subheader")

            with Horizontal():
                yield Label("Check Interval (seconds):")
                yield Input(placeholder="30", id="check_interval")

            with Horizontal():
                yield Label("Log Level:")
                yield Input(placeholder="INFO", id="log_level")

            with Horizontal():
                yield Label("Enable Metrics:")
                yield Switch(id="enable_metrics")

            with Horizontal():
                yield Label("Metrics Port:")
                yield Input(placeholder="8000", id="metrics_port")

            with Horizontal():
                yield Button("Save", id="save_config", variant="primary")
                yield Button("Cancel", id="cancel_config", variant="default")

    @on(Button.Pressed, "#save_config")
    def save_config(self) -> None:
        """Save configuration changes."""
        # TODO: Implement configuration saving
        self.app.pop_screen()

    @on(Button.Pressed, "#cancel_config")
    def cancel_config(self) -> None:
        """Cancel configuration editing."""
        self.app.pop_screen()


class VimeoMonitorTUI(App[None]):
    """Main TUI application for Vimeo Monitor."""

    CSS = """
    .config_buttons {
        height: 3;
        margin: 1 0;
    }

    .config_buttons Button {
        margin: 0 1;
    }

    TabbedContent {
        height: 100%;
    }

    TabPane {
        padding: 1;
    }

    DataTable {
        height: 1fr;
    }

    LogWidget {
        height: 1fr;
    }

    ServiceStatusWidget {
        height: 6;
        margin: 0 0 1 0;
    }

    MetricsWidget {
        height: 1fr;
    }

    ConfigWidget {
        height: 1fr;
    }
    """

    TITLE = "Vimeo Monitor - Terminal Interface"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("c", "config", "Configuration"),
        ("l", "logs", "Logs"),
        ("s", "status", "Status"),
        ("m", "metrics", "Metrics"),
    ]

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config_manager: EnhancedConfigManager | None = None
        self.health_monitor: HealthMonitor | None = None
        self.performance_optimizer: PerformanceOptimizer | None = None
        self.network_monitor: NetworkMonitor | None = None
        self.last_update = time.time()

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()

        with TabbedContent(initial="status"):
            with TabPane("Status", id="status"):
                with Vertical():
                    yield ServiceStatusWidget(id="service_status")
                    yield MetricsWidget(id="metrics_widget")

            with TabPane("Configuration", id="config"):
                yield ConfigWidget(id="config_widget")

            with TabPane("Logs", id="logs"):
                yield LogWidget(id="log_widget")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize the application."""
        try:
            # Initialize monitoring components
            self.config_manager = EnhancedConfigManager()
            self.health_monitor = HealthMonitor(self.config_manager)
            self.performance_optimizer = PerformanceOptimizer(self.config_manager)
            self.network_monitor = NetworkMonitor(self.config_manager)

            # Start monitoring services
            if self.network_monitor:
                self.network_monitor.start_monitoring()

            # Start periodic updates
            self.set_interval(5.0, self.update_data)
            self.update_data()

            # Setup logging
            log_widget = self.query_one("#log_widget", LogWidget)
            log_widget.write("Vimeo Monitor TUI initialized successfully")

        except Exception as e:
            self.notify(f"Failed to initialize: {e}", severity="error")

    @work(exclusive=True)
    async def update_data(self) -> None:
        """Update all data displays."""
        try:
            # Update service status
            service_status = self.get_service_status()
            metrics_status = self.get_metrics_status()

            service_widget = self.query_one("#service_status", ServiceStatusWidget)
            service_widget.service_status = service_status
            service_widget.metrics_status = metrics_status

            # Update metrics
            metrics_data = await self.get_metrics_data()
            metrics_widget = self.query_one("#metrics_widget", MetricsWidget)
            metrics_widget.metrics_data = metrics_data

            # Update configuration
            if self.config_manager:
                config_data = self.get_config_data()
                config_widget = self.query_one("#config_widget", ConfigWidget)
                config_widget.config_data = config_data

            self.last_update = time.time()

        except Exception as e:
            log_widget = self.query_one("#log_widget", LogWidget)
            log_widget.write(f"Error updating data: {e}")

    def get_service_status(self) -> str:
        """Get the current service status."""
        try:
            import subprocess

            result = subprocess.run(
                ["systemctl", "is-active", "vimeo-monitor"], capture_output=True, text=True, timeout=5
            )
            return "Running" if result.returncode == 0 else "Stopped"
        except Exception:
            return "Unknown"

    def get_metrics_status(self) -> str:
        """Get the current metrics server status."""
        try:
            response = requests.get("http://localhost:8000/metrics", timeout=5)
            return "Accessible" if response.status_code == 200 else "Not Accessible"
        except Exception:
            return "Not Accessible"

    async def get_metrics_data(self) -> dict[str, Any]:
        """Get current metrics data."""
        try:
            if self.performance_optimizer:
                status = self.performance_optimizer.get_optimization_status()
                return {
                    "system": status.get("current_metrics", {}),
                    "api": {
                        "total_requests": status.get("performance", {}).get("api_requests", 0),
                        "failed_requests": 0,  # TODO: Add from health monitor
                        "cache_hit_rate": status.get("cache", {}).get("hit_rate", 0) * 100,
                    },
                    "network": {
                        "connectivity": self.network_monitor.is_connected() if self.network_monitor else False,
                        "response_time_ms": 0,  # TODO: Add from network monitor
                    },
                }
        except Exception as e:
            log_widget = self.query_one("#log_widget", LogWidget)
            log_widget.write(f"Error getting metrics: {e}")

        return {}

    def get_config_data(self) -> dict[str, Any]:
        """Get current configuration data."""
        if self.config_manager:
            return {
                "vimeo_api_token": getattr(self.config_manager, "vimeo_api_token", None),
                "check_interval": getattr(self.config_manager, "check_interval", 30),
                "enable_prometheus_metrics": getattr(self.config_manager, "enable_prometheus_metrics", False),
                "prometheus_metrics_port": getattr(self.config_manager, "prometheus_metrics_port", 8000),
                "log_level": getattr(self.config_manager, "log_level", "INFO"),
                "enable_network_monitoring": getattr(self.config_manager, "enable_network_monitoring", True),
            }
        return {}

    def action_refresh(self) -> None:
        """Refresh all data."""
        self.notify("Refreshing data...")
        self.update_data()

    def action_config(self) -> None:
        """Switch to configuration tab."""
        tabbed_content = self.query_one(TabbedContent)
        tabbed_content.active = "config"

    def action_logs(self) -> None:
        """Switch to logs tab."""
        tabbed_content = self.query_one(TabbedContent)
        tabbed_content.active = "logs"

    def action_status(self) -> None:
        """Switch to status tab."""
        tabbed_content = self.query_one(TabbedContent)
        tabbed_content.active = "status"

    def action_metrics(self) -> None:
        """Switch to metrics tab."""
        tabbed_content = self.query_one(TabbedContent)
        tabbed_content.active = "status"  # Metrics are on status tab

    def on_reload_config_message(self, message: ReloadConfigMessage) -> None:
        """Handle configuration reload."""
        try:
            if self.config_manager:
                # Reload configuration
                self.config_manager.__init__()  # Re-initialize to reload config
                self.notify("Configuration reloaded successfully")
                log_widget = self.query_one("#log_widget", LogWidget)
                log_widget.write("Configuration reloaded")
        except Exception as e:
            self.notify(f"Failed to reload configuration: {e}", severity="error")


def run_tui() -> None:
    """Run the TUI application."""
    app = VimeoMonitorTUI()
    app.run()


if __name__ == "__main__":
    run_tui()
