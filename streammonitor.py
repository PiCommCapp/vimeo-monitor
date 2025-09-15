#!/usr/bin/env python3
"""
Vimeo Monitor - Main script using modular architecture.

This script monitors Vimeo live streams and displays them using VLC/FFmpeg.
"""

import time
import signal
import sys
from typing import Optional

from vimeo_monitor import config, get_logger, LoggingContext
from vimeo_monitor.process_manager import ProcessManager
from vimeo_monitor.monitor import Monitor


class VimeoMonitorApp:
    """Main application class for Vimeo Monitor."""
    
    def __init__(self):
        """Initialize the Vimeo Monitor application."""
        self.logger = get_logger(config)
        self.app_logger = LoggingContext(self.logger, "APP")
        self.process_manager: Optional[ProcessManager] = None
        self.monitor: Optional[Monitor] = None
        self.running = False
    
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
            
            return True
            
        except Exception as e:
            self.app_logger.error(f"Initialization failed: {e}")
            return False
    
    def setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.app_logger.info(f"Received signal {signum}, initiating graceful shutdown")
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
        
        try:
            while self.running:
                try:
                    # Run monitoring cycle
                    self.monitor.run_monitoring_cycle()
                    
                    # Check process health
                    if not self.process_manager.health_check():
                        self.app_logger.warning("Process health check failed")
                        self.process_manager.restart_process()
                    
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
    
    def shutdown(self) -> None:
        """Graceful shutdown of all components."""
        self.app_logger.info("Shutting down Vimeo Monitor")
        self.running = False
        
        if self.process_manager:
            self.process_manager.cleanup()
        
        self.app_logger.info("Shutdown complete")


def main() -> int:
    """Main entry point."""
    app = VimeoMonitorApp()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())