#!/usr/bin/env python3

"""Simple fallback TUI for Vimeo Monitor using curses."""

import curses
import logging
import subprocess
import sys
import time
from datetime import datetime
from typing import Any

import requests

# Import our monitoring components
try:
    from vimeo_monitor.config import ConfigManager, EnhancedConfigManager
    from vimeo_monitor.health import HealthMonitor
    from vimeo_monitor.network_monitor import NetworkMonitor
    from vimeo_monitor.performance import PerformanceOptimizer
except ImportError as e:
    logging.exception("Failed to import vimeo_monitor components: %s", e)
    sys.exit(1)


class SimpleTUI:
    """Simple TUI for Vimeo Monitor using curses."""

    def __init__(self) -> None:
        self.stdscr: Any = None
        self.current_tab = 0
        self.tabs = ["Status", "Metrics", "Config", "Logs"]
        self.config_manager: EnhancedConfigManager | None = None
        self.health_monitor: HealthMonitor | None = None
        self.performance_optimizer: PerformanceOptimizer | None = None
        self.network_monitor: NetworkMonitor | None = None
        self.logs: list[str] = []
        self.last_update = 0

    def initialize_components(self) -> None:
        """Initialize monitoring components."""
        try:
            self.config_manager = EnhancedConfigManager()
            self.health_monitor = HealthMonitor(self.config_manager)
            self.performance_optimizer = PerformanceOptimizer(self.config_manager)
            self.network_monitor = NetworkMonitor(self.config_manager)

            if self.network_monitor:
                self.network_monitor.start_monitoring()

            self.add_log("Vimeo Monitor Simple TUI initialized successfully")
        except Exception as e:
            self.add_log(f"Failed to initialize: {e}")

    def add_log(self, message: str) -> None:
        """Add a log message."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")
        # Keep only last 100 log entries
        if len(self.logs) > 100:
            self.logs = self.logs[-100:]

    def get_service_status(self) -> str:
        """Get the current service status."""
        try:
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

    def get_metrics_data(self) -> dict[str, Any]:
        """Get current metrics data."""
        try:
            if self.performance_optimizer:
                status = self.performance_optimizer.get_optimization_status()
                return {
                    "system": status.get("current_metrics", {}),
                    "cache": status.get("cache", {}),
                    "performance": status.get("performance", {}),
                }
        except Exception as e:
            self.add_log(f"Error getting metrics: {e}")
        return {}

    def draw_header(self, stdscr: Any) -> None:
        """Draw the header."""
        height, width = stdscr.getmaxyx()

        # Title
        title = "Vimeo Monitor - Simple TUI"
        stdscr.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)

        # Current time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        stdscr.addstr(0, width - len(current_time) - 1, current_time)

        # Tab bar
        tab_y = 1
        tab_x = 2
        for i, tab in enumerate(self.tabs):
            if i == self.current_tab:
                stdscr.addstr(tab_y, tab_x, f"[{tab}]", curses.A_REVERSE)
            else:
                stdscr.addstr(tab_y, tab_x, f" {tab} ")
            tab_x += len(tab) + 3

        # Separator line
        stdscr.addstr(2, 0, "─" * width)

    def draw_status_tab(self, stdscr: Any) -> None:
        """Draw the status tab."""
        start_y = 4

        # Service status
        service_status = self.get_service_status()
        metrics_status = self.get_metrics_status()

        stdscr.addstr(start_y, 2, "Service Status:", curses.A_BOLD)
        status_color = curses.A_NORMAL
        if service_status == "Running":
            status_color = curses.color_pair(1) if curses.has_colors() else curses.A_NORMAL
        elif service_status == "Stopped":
            status_color = curses.color_pair(2) if curses.has_colors() else curses.A_NORMAL
        stdscr.addstr(start_y, 18, service_status, status_color)

        stdscr.addstr(start_y + 1, 2, "Metrics Status:")
        metrics_color = curses.A_NORMAL
        if "Accessible" in metrics_status:
            metrics_color = curses.color_pair(1) if curses.has_colors() else curses.A_NORMAL
        else:
            metrics_color = curses.color_pair(2) if curses.has_colors() else curses.A_NORMAL
        stdscr.addstr(start_y + 1, 18, metrics_status, metrics_color)

        # Last update
        last_update_str = datetime.fromtimestamp(self.last_update).strftime("%H:%M:%S") if self.last_update else "Never"
        stdscr.addstr(start_y + 2, 2, f"Last Update: {last_update_str}")

    def draw_metrics_tab(self, stdscr: Any) -> None:
        """Draw the metrics tab."""
        start_y = 4

        metrics_data = self.get_metrics_data()

        stdscr.addstr(start_y, 2, "System Metrics:", curses.A_BOLD)

        y_offset = start_y + 1
        if "system" in metrics_data:
            system = metrics_data["system"]
            stdscr.addstr(y_offset, 4, f"CPU Usage:    {system.get('cpu_percent', 0):.1f}%")
            stdscr.addstr(y_offset + 1, 4, f"Memory:       {system.get('memory_mb', 0):.1f} MB")
            stdscr.addstr(y_offset + 2, 4, f"Threads:      {system.get('threads', 0)}")
            y_offset += 4

        if "cache" in metrics_data:
            cache = metrics_data["cache"]
            stdscr.addstr(y_offset, 2, "Cache Metrics:", curses.A_BOLD)
            stdscr.addstr(y_offset + 1, 4, f"Hit Rate:     {cache.get('hit_rate', 0) * 100:.1f}%")
            stdscr.addstr(y_offset + 2, 4, f"Size:         {cache.get('size', 0)}/{cache.get('max_size', 0)}")

    def draw_config_tab(self, stdscr: Any) -> None:
        """Draw the configuration tab."""
        start_y = 4

        stdscr.addstr(start_y, 2, "Configuration:", curses.A_BOLD)

        if self.config_manager:
            config_items = [
                ("API Token", "***" if getattr(self.config_manager, "vimeo_api_token", None) else "Not Set"),
                ("Check Interval", f"{getattr(self.config_manager, 'check_interval', 30)}s"),
                ("Metrics Enabled", str(getattr(self.config_manager, "enable_prometheus_metrics", False))),
                ("Metrics Port", str(getattr(self.config_manager, "prometheus_metrics_port", 8000))),
                ("Log Level", getattr(self.config_manager, "log_level", "INFO")),
            ]

            for i, (key, value) in enumerate(config_items):
                stdscr.addstr(start_y + 1 + i, 4, f"{key}: {value}")

    def draw_logs_tab(self, stdscr: Any) -> None:
        """Draw the logs tab."""
        height, width = stdscr.getmaxyx()
        start_y = 4
        max_lines = height - start_y - 2

        stdscr.addstr(start_y, 2, "Application Logs:", curses.A_BOLD)

        # Show last N log entries
        visible_logs = self.logs[-max_lines:] if len(self.logs) > max_lines else self.logs

        for i, log_entry in enumerate(visible_logs):
            if start_y + 1 + i < height - 1:
                # Truncate long lines
                display_text = log_entry[: width - 4] if len(log_entry) > width - 4 else log_entry
                stdscr.addstr(start_y + 1 + i, 2, display_text)

    def draw_footer(self, stdscr: Any) -> None:
        """Draw the footer with help."""
        height, width = stdscr.getmaxyx()
        footer_y = height - 1

        help_text = "TAB: Switch tabs | r: Refresh | q: Quit | ←/→: Navigate"
        stdscr.addstr(footer_y, 2, help_text[: width - 4])

    def update_data(self) -> None:
        """Update all data."""
        self.last_update = time.time()
        self.add_log("Data updated")

    def main_loop(self, stdscr: Any) -> None:
        """Main application loop."""
        self.stdscr = stdscr

        # Setup colors
        if curses.has_colors():
            curses.start_color()
            curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Success
            curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)  # Error

        # Setup screen
        curses.curs_set(0)  # Hide cursor
        stdscr.timeout(1000)  # 1 second timeout for getch

        self.initialize_components()
        self.update_data()

        while True:
            # Clear and redraw
            stdscr.clear()

            try:
                self.draw_header(stdscr)

                # Draw current tab content
                if self.current_tab == 0:
                    self.draw_status_tab(stdscr)
                elif self.current_tab == 1:
                    self.draw_metrics_tab(stdscr)
                elif self.current_tab == 2:
                    self.draw_config_tab(stdscr)
                elif self.current_tab == 3:
                    self.draw_logs_tab(stdscr)

                self.draw_footer(stdscr)

            except curses.error:
                # Handle screen too small or other drawing errors
                pass

            stdscr.refresh()

            # Handle input
            key = stdscr.getch()

            if key == ord("q") or key == ord("Q"):
                break
            elif key == ord("\t") or key == curses.KEY_RIGHT:
                self.current_tab = (self.current_tab + 1) % len(self.tabs)
            elif key == curses.KEY_LEFT:
                self.current_tab = (self.current_tab - 1) % len(self.tabs)
            elif key == ord("r") or key == ord("R"):
                self.update_data()
            elif key == -1:  # Timeout - update data periodically
                # Update every 5 seconds
                if time.time() - self.last_update > 5:
                    self.update_data()

    def cleanup(self) -> None:
        """Cleanup resources."""
        if self.network_monitor:
            self.network_monitor.stop_monitoring()


def run_simple_tui() -> None:
    """Run the simple TUI application."""
    tui = SimpleTUI()
    try:
        curses.wrapper(tui.main_loop)
    except KeyboardInterrupt:
        pass
    finally:
        tui.cleanup()


if __name__ == "__main__":
    run_simple_tui()
