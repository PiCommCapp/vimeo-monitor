#!/usr/bin/env python3
"""
Vimeo Monitor - Main script using modular architecture.

This script monitors Vimeo live streams and displays them using VLC/FFmpeg.
"""

import signal
import sys
import time

from vimeo_monitor import LoggingContext, config, get_logger
from vimeo_monitor.monitor import Monitor
from vimeo_monitor.process_manager import ProcessManager


class VimeoMonitorApp:
    """Main application class for Vimeo Monitor."""

    def __init__(self):
        """Initialize the Vimeo Monitor application."""
        self.logger = get_logger(config)
        self.app_logger = LoggingContext(self.logger, "APP")
        self.process_manager: ProcessManager | None = None
        self.monitor: Monitor | None = None
        self.health_module = None  # Health monitoring module
        self.running = False

        # System tracking
        self.system_start_time = time.time()

    def initialize(self) -> bool:
        """Initialize all components."""
        try:
            # Validate configuration
            config.validate()
            self.app_logger.info("Configuration validated successfully")

            # Initialize process manager
            self.process_manager = ProcessManager(config, self.logger)
            self.app_logger.info("Process manager initialized")

            # Initialize monitor
            self.monitor = Monitor(config, self.logger, self.process_manager)
            self.app_logger.info("Monitor initialized")
            
            # Initialize health monitoring (optional)
            if getattr(config, "health_monitoring_enabled", False):
                try:
                    from vimeo_monitor.health_module import HealthModule
                    self.health_module = HealthModule(
                        config=config,
                        logger=self.logger,
                        monitor=self.monitor,
                        process_manager=self.process_manager
                    )
                    self.app_logger.info("Health monitoring initialized")
                except ImportError as e:
                    self.app_logger.error(
                        f"Health monitoring dependencies not installed: {e}. "
                        "Install with: pip install vimeo-monitor[health]"
                    )
                    self.health_module = None
            else:
                self.app_logger.debug("Health monitoring disabled")

            return True

        except Exception as e:
            self.app_logger.error(f"Initialization failed: {e}")
            return False

    def setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""

        def signal_handler(signum, frame):
            self.app_logger.info(
                f"Received signal {signum}, initiating graceful shutdown"
            )
            self.running = False

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def run(self) -> int:
        """Run the main monitoring loop."""
        if not self.initialize():
            return 1

        self.setup_signal_handlers()
        self.running = True
        self.app_logger.info("Starting Vimeo Monitor")
        
        # Start health monitoring if enabled
        if self.health_module:
            try:
                self.health_module.start()
                self.app_logger.info(
                    f"Health monitoring started on http://{config.health_metrics_host}:{config.health_metrics_port}/metrics"
                )
            except Exception as e:
                self.app_logger.error(f"Failed to start health monitoring: {e}")

        try:
            while self.running:
                try:
                    # Run monitoring cycle
                    self.monitor.run_monitoring_cycle()

                    # Check if stream needs restart
                    if not self.monitor.restart_stream_if_needed():
                        self.app_logger.warning("Stream restart failed")

                    # Wait for configured interval
                    time.sleep(config.check_interval)

                except KeyboardInterrupt:
                    self.app_logger.info("Received keyboard interrupt")
                    break
                except Exception as e:
                    self.app_logger.error(f"Error in main loop: {e}")
                    time.sleep(config.check_interval)  # Continue running

        except Exception as e:
            self.app_logger.error(f"Fatal error in main loop: {e}")
            return 1
        finally:
            self.shutdown()

        return 0

    def get_system_status(self) -> dict:
        """Get current system status information."""
        try:
            uptime = time.time() - self.system_start_time
            monitor_status = self.monitor.get_status_info()
            process_status = self.process_manager.get_process_status()

            status = {
                "uptime": uptime,
                "monitor_status": monitor_status,
                "process_status": process_status,
                "running": self.running,
            }
            
            # Add health monitoring status if enabled
            if self.health_module:
                status["health_monitoring"] = {
                    "enabled": True,
                    "running": getattr(self.health_module, "running", False),
                    "metrics_url": f"http://{config.health_metrics_host}:{config.health_metrics_port}/metrics"
                }
            else:
                status["health_monitoring"] = {"enabled": False}

            return status
        except Exception as e:
            self.app_logger.error(f"Failed to get system status: {e}")
            return {"error": str(e)}

    def shutdown(self) -> None:
        """Graceful shutdown of all components."""
        self.app_logger.info("Shutting down Vimeo Monitor")
        self.running = False
        
        # Shutdown health monitoring
        if self.health_module:
            try:
                self.health_module.shutdown()
                self.app_logger.info("Health monitoring stopped")
            except Exception as e:
                self.app_logger.error(f"Error shutting down health monitoring: {e}")

        if self.process_manager:
            self.process_manager.cleanup()

        self.app_logger.info("Shutdown complete")


def main() -> int:
    """Main entry point."""
    app = VimeoMonitorApp()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
