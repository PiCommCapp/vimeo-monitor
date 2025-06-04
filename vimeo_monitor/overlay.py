#!/usr/bin/env python3

import logging
import os
import threading
import time
from collections.abc import Callable
from typing import Any

# Try to import tkinter, gracefully handle if not available
try:
    import tkinter as tk

    _tkinter_available = True
except ImportError:
    _tkinter_available = False
    tk = None  # type: ignore[assignment]


class NetworkStatusOverlay:
    """
    Network status display with GUI overlay (if available) or terminal fallback.

    Provides real-time status updates without blocking the main application,
    with configurable positioning, opacity, and update intervals.
    """

    def __init__(self, status_callback: Callable[[], dict[str, Any]]) -> None:
        """
        Initialize the network status overlay.

        Args:
            status_callback: Function that returns current status information
        """
        self.status_callback = status_callback
        self.running = False
        self.overlay_thread: threading.Thread | None = None
        self.root: Any = None  # tk.Tk if available, None otherwise

        # Configuration from environment
        self.enabled = os.getenv("DISPLAY_NETWORK_STATUS", "true").lower() == "true"
        self.position = os.getenv("OVERLAY_POSITION", "top-right")
        self.opacity = float(os.getenv("OVERLAY_OPACITY", "0.8"))
        self.update_interval = int(os.getenv("OVERLAY_UPDATE_INTERVAL", "2"))
        self.auto_hide = os.getenv("OVERLAY_AUTO_HIDE", "false").lower() == "true"
        self.use_terminal = os.getenv("OVERLAY_USE_TERMINAL", "auto").lower()

        # UI elements
        self.status_labels: dict[str, Any] = {}

        # Determine display mode
        if not _tkinter_available:
            if self.use_terminal == "auto":
                self.use_terminal_display = True
                logging.warning("tkinter not available, using terminal status display")
            else:
                logging.error("tkinter not available and terminal display not enabled")
                self.enabled = False
                return
        else:
            self.use_terminal_display = self.use_terminal == "true"

        logging.info(
            "Network status overlay initialized: enabled=%s, mode=%s, position=%s",
            self.enabled,
            "terminal" if self.use_terminal_display else "gui",
            self.position,
        )

    def start(self) -> None:
        """Start the overlay display in a separate thread."""
        if not self.enabled:
            logging.info("Network status overlay disabled by configuration")
            return

        if self.running:
            logging.warning("Overlay already running")
            return

        self.running = True
        self.overlay_thread = threading.Thread(target=self._run_overlay, daemon=True)
        self.overlay_thread.start()
        logging.info("Network status overlay started (%s mode)", "terminal" if self.use_terminal_display else "gui")

    def stop(self) -> None:
        """Stop the overlay display and clean up resources."""
        if not self.running:
            return

        self.running = False

        if not self.use_terminal_display and self.root:
            try:
                # Schedule the GUI cleanup on the main thread
                self.root.after(0, self._cleanup_gui)
            except Exception:
                # GUI already destroyed or not available
                pass

        if self.overlay_thread and self.overlay_thread.is_alive():
            self.overlay_thread.join(timeout=2.0)

        logging.info("Network status overlay stopped")

    def _cleanup_gui(self) -> None:
        """Clean up GUI resources safely."""
        if not _tkinter_available or self.use_terminal_display:
            return

        try:
            if self.root:
                self.root.quit()
                self.root.destroy()
                self.root = None
        except Exception:
            # GUI already destroyed
            pass

    def _run_overlay(self) -> None:
        """Main overlay loop running in separate thread."""
        try:
            if self.use_terminal_display:
                self._run_terminal_display()
            else:
                self._create_overlay_window()
                self._update_loop()
        except Exception as e:
            logging.exception("Error in overlay thread: %s", e)
        finally:
            if not self.use_terminal_display:
                self._cleanup_gui()

    def _run_terminal_display(self) -> None:
        """Run terminal-based status display."""
        start_time = time.time()

        while self.running:
            try:
                # Get current status
                status = self.status_callback()

                # Check if we should auto-hide (skip display)
                if self.auto_hide and not status.get("api_failure_mode", False):
                    time.sleep(self.update_interval)
                    continue

                # Display status in terminal
                self._display_terminal_status(status, start_time)

                # Wait before next update
                time.sleep(self.update_interval)

            except Exception as e:
                logging.exception("Error updating terminal overlay: %s", e)
                time.sleep(self.update_interval)

    def _display_terminal_status(self, status: dict[str, Any], start_time: float) -> None:
        """Display status information in terminal format."""
        # Create status summary
        mode = status.get("current_mode", "unknown") or "unknown"

        if status.get("api_failure_mode", False):
            api_status = f"❌ FAILING ({status.get('consecutive_failures', 0)})"
        else:
            api_status = f"✅ HEALTHY ({status.get('consecutive_successes', 0)})"

        if mode == "stream":
            stream_status = "🟢 ACTIVE"
        elif mode == "api_failure":
            stream_status = "🔴 API_FAILURE"
        else:
            stream_status = "🟡 STANDBY"

        failure_rate = status.get("failure_rate_percent", 0)
        total_requests = status.get("total_requests", 0)

        # Network status from enhanced health info
        network_info = status.get("network", {})
        network_status = network_info.get("status", "unknown")
        network_summary = network_info.get("summary", "Network status unknown")

        if network_status == "healthy":
            network_indicator = "🟢 HEALTHY"
        elif network_status == "degraded":
            network_indicator = "🟡 DEGRADED"
        elif network_status == "failing":
            network_indicator = "🔴 FAILING"
        elif network_status == "offline":
            network_indicator = "❌ OFFLINE"
        elif network_status == "not_monitored":
            network_indicator = "❓ NOT_MONITORED"
        else:
            network_indicator = f"❓ {network_status.upper()}"

        uptime_seconds = time.time() - start_time
        if uptime_seconds < 60:
            uptime = f"{uptime_seconds:.0f}s"
        elif uptime_seconds < 3600:
            uptime = f"{uptime_seconds / 60:.1f}m"
        else:
            uptime = f"{uptime_seconds / 3600:.1f}h"

        # Log enhanced status summary with network information
        logging.info(
            "🎥 Status: Mode=%s | API=%s | Stream=%s | Network=%s | Failures=%.1f%% (%d reqs) | Uptime=%s",
            mode.upper(),
            api_status,
            stream_status,
            network_indicator,
            failure_rate,
            total_requests,
            uptime,
        )

        # Log detailed network summary if available
        if network_info.get("monitoring_active", False):
            targets_healthy = network_info.get("targets_healthy", 0)
            targets_total = network_info.get("targets_total", 0)
            targets_failing = network_info.get("targets_failing", 0)

            # Get fallback information from detailed network status
            detailed_network = status.get("detailed_network", {})
            monitoring_mode = detailed_network.get("monitoring_mode", "normal")
            fallback_count = detailed_network.get("summary", {}).get("using_fallback", 0)

            # Create fallback status string
            fallback_info = f", {fallback_count} using fallback" if fallback_count > 0 else ""
            mode_info = f" [{monitoring_mode.upper()}]" if monitoring_mode != "normal" else ""

            logging.info(
                "🌐 Network Details: %d/%d targets healthy, %d failing%s%s - %s",
                targets_healthy,
                targets_total,
                targets_failing,
                fallback_info,
                mode_info,
                network_summary,
            )

    def _create_overlay_window(self) -> None:
        """Create and configure the overlay window."""
        if not _tkinter_available or not tk:
            return

        self.root = tk.Tk()
        self.root.title("Vimeo Monitor Status")

        # Configure window properties
        self.root.attributes("-topmost", True)  # type: ignore[misc]  # Keep on top
        self.root.attributes("-alpha", self.opacity)  # type: ignore[misc]  # Set transparency
        self.root.overrideredirect(True)  # Remove window decorations

        # Configure colors and styling
        bg_color = "#2c3e50"
        text_color = "#ecf0f1"

        self.root.configure(bg=bg_color)

        # Create main frame
        main_frame = tk.Frame(self.root, bg=bg_color, padx=10, pady=8)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title label
        title_label = tk.Label(
            main_frame, text="🎥 Vimeo Monitor", font=("Arial", 10, "bold"), bg=bg_color, fg=text_color
        )
        title_label.pack(anchor=tk.W)

        # Status labels
        status_fields = [
            ("mode", "Mode"),
            ("api_status", "API Status"),
            ("stream_status", "Stream"),
            ("network_status", "Network"),
            ("failures", "Failures"),
            ("last_success", "Last Success"),
            ("uptime", "Uptime"),
        ]

        for field, label_text in status_fields:
            self.status_labels[field] = tk.Label(
                main_frame, text=f"{label_text}: --", font=("Arial", 9), bg=bg_color, fg=text_color, anchor=tk.W
            )
            self.status_labels[field].pack(anchor=tk.W, pady=1)

        # Position the window
        self._position_window()

    def _position_window(self) -> None:
        """Position the overlay window based on configuration."""
        if not _tkinter_available or not self.root:
            return

        # Update window to get accurate size
        self.root.update_idletasks()

        window_width = self.root.winfo_reqwidth()
        window_height = self.root.winfo_reqheight()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Calculate position based on configuration
        margin = 10

        if self.position == "top-left":
            x, y = margin, margin
        elif self.position == "top-right":
            x, y = screen_width - window_width - margin, margin
        elif self.position == "bottom-left":
            x, y = margin, screen_height - window_height - margin
        elif self.position == "bottom-right":
            x, y = screen_width - window_width - margin, screen_height - window_height - margin
        else:
            # Default to top-right
            x, y = screen_width - window_width - margin, margin

        self.root.geometry(f"+{x}+{y}")

    def _update_loop(self) -> None:
        """Main update loop for the GUI overlay."""
        if not _tkinter_available:
            return

        start_time = time.time()

        while self.running and self.root:
            try:
                # Get current status
                status = self.status_callback()

                # Check if we should auto-hide
                if self.auto_hide and not status.get("api_failure_mode", False):
                    if self.root.winfo_viewable():
                        self.root.withdraw()
                    time.sleep(self.update_interval)
                    continue
                else:
                    if not self.root.winfo_viewable():
                        self.root.deiconify()

                # Update display
                self._update_status_display(status, start_time)

                # Schedule next update
                time.sleep(self.update_interval)

            except Exception as e:
                # Window was destroyed or other error
                if "invalid command name" not in str(e):
                    logging.exception("Error updating GUI overlay: %s", e)
                break

    def _update_status_display(self, status: dict[str, Any], start_time: float) -> None:
        """Update the status display with current information."""
        if not _tkinter_available or not self.root:
            return

        try:
            # Mode status
            mode = status.get("current_mode", "unknown")
            self.status_labels["mode"].config(text=f"Mode: {mode}")

            # API status
            if status.get("api_failure_mode", False):
                api_text = f"❌ Failing ({status.get('consecutive_failures', 0)})"
                api_color = "#e74c3c"
            else:
                api_text = f"✅ Healthy ({status.get('consecutive_successes', 0)})"
                api_color = "#27ae60"

            self.status_labels["api_status"].config(text=f"API: {api_text}", fg=api_color)

            # Stream status
            if mode == "stream":
                stream_text = "🟢 Active"
                stream_color = "#27ae60"
            elif mode == "api_failure":
                stream_text = "🔴 API Failure"
                stream_color = "#e74c3c"
            else:
                stream_text = "🟡 Standby"
                stream_color = "#f39c12"

            self.status_labels["stream_status"].config(text=f"Stream: {stream_text}", fg=stream_color)

            # Network status
            network_status = status.get("network", {}).get("status", "unknown")
            if network_status == "healthy":
                network_text = "🟢 HEALTHY"
            elif network_status == "degraded":
                network_text = "🟡 DEGRADED"
            elif network_status == "failing":
                network_text = "🔴 FAILING"
            elif network_status == "offline":
                network_text = "❌ OFFLINE"
            elif network_status == "not_monitored":
                network_text = "❓ NOT_MONITORED"
            else:
                network_text = f"❓ {network_status.upper()}"

            self.status_labels["network_status"].config(text=f"Network: {network_text}")

            # Failure information
            failure_rate = status.get("failure_rate_percent", 0)
            total_requests = status.get("total_requests", 0)
            self.status_labels["failures"].config(text=f"Failures: {failure_rate:.1f}% ({total_requests} reqs)")

            # Last success time
            time_since_success = status.get("time_since_last_success")
            if time_since_success is not None:
                if time_since_success < 60:
                    success_text = f"{time_since_success:.0f}s ago"
                elif time_since_success < 3600:
                    success_text = f"{time_since_success / 60:.1f}m ago"
                else:
                    success_text = f"{time_since_success / 3600:.1f}h ago"
            else:
                success_text = "Never"

            self.status_labels["last_success"].config(text=f"Last Success: {success_text}")

            # Uptime
            uptime_seconds = time.time() - start_time
            if uptime_seconds < 60:
                uptime_text = f"{uptime_seconds:.0f}s"
            elif uptime_seconds < 3600:
                uptime_text = f"{uptime_seconds / 60:.1f}m"
            else:
                uptime_text = f"{uptime_seconds / 3600:.1f}h"

            self.status_labels["uptime"].config(text=f"Uptime: {uptime_text}")

        except Exception as e:
            # Window was destroyed or other error
            if "invalid command name" not in str(e):
                logging.exception("Error updating status display: %s", e)

    def is_running(self) -> bool:
        """Check if the overlay is currently running."""
        return self.running

    def update_configuration(self) -> None:
        """Update overlay configuration from environment variables."""
        old_enabled = self.enabled
        self.enabled = os.getenv("DISPLAY_NETWORK_STATUS", "true").lower() == "true"
        self.position = os.getenv("OVERLAY_POSITION", "top-right")
        self.opacity = float(os.getenv("OVERLAY_OPACITY", "0.8"))
        self.update_interval = int(os.getenv("OVERLAY_UPDATE_INTERVAL", "2"))
        self.auto_hide = os.getenv("OVERLAY_AUTO_HIDE", "false").lower() == "true"

        # Restart if enabled state changed
        if old_enabled != self.enabled:
            if self.enabled:
                self.start()
            else:
                self.stop()

        # Update window properties if running and using GUI
        if self.running and not self.use_terminal_display and self.root:
            try:
                self.root.attributes("-alpha", self.opacity)  # type: ignore[misc]
                self._position_window()
            except Exception:
                pass

        logging.info(
            "Overlay configuration updated: enabled=%s, mode=%s, position=%s",
            self.enabled,
            "terminal" if self.use_terminal_display else "gui",
            self.position,
        )
