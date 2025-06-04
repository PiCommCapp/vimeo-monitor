#!/usr/bin/env python3

"""Main application orchestrator for Vimeo stream monitoring."""

import argparse
import logging
import logging.handlers
import sys
import time
from pathlib import Path
from typing import Any

from vimeo_monitor.client import VimeoAPIClient
from vimeo_monitor.config import ConfigManager, ConfigurationError
from vimeo_monitor.health import HealthMonitor
from vimeo_monitor.network_monitor import NetworkMonitor
from vimeo_monitor.overlay import NetworkStatusOverlay
from vimeo_monitor.performance import PerformanceOptimizer
from vimeo_monitor.stream import StreamManager


def setup_logging(config: ConfigManager) -> None:
    """Configure logging with rotating file handler for automatic log rotation.

    Args:
        config: Configuration manager instance
    """
    log_file = config.log_file
    log_level = config.log_level
    max_size = config.log_rotate_max_size
    backup_count = config.log_rotate_backup_count

    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure logging with proper handler types
    handlers: list[logging.Handler] = [logging.StreamHandler()]

    # Add rotating file handler if LOG_FILE is specified
    if log_file:
        rotating_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_size, backupCount=backup_count, encoding="utf-8"
        )
        handlers.append(rotating_handler)

    # Enhanced logging format with more detail
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s")

    # Apply formatter to all handlers
    for handler in handlers:
        handler.setFormatter(formatter)

    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        handlers=handlers,
        format="%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
    )

    # Log rotation configuration info
    if log_file:
        logging.info("Log rotation configured: max_size=%d bytes, backup_count=%d", max_size, backup_count)


class MonitorApp:
    """Main application orchestrator that coordinates all components."""

    def __init__(self, env_file: str = ".env", config_file: str | None = None) -> None:
        """Initialize the monitor application.

        Args:
            env_file: Path to environment file
            config_file: Optional path to YAML/TOML configuration file
        """
        try:
            # Auto-detect config file if not specified
            if config_file is None:
                # Look for config files in config directory
                project_root = Path(__file__).parent.parent
                yaml_config = project_root / "config" / "config.yaml"
                toml_config = project_root / "config" / "config.toml"

                if yaml_config.exists():
                    config_file = str(yaml_config)
                    logging.debug("Auto-detected YAML config: %s", config_file)
                elif toml_config.exists():
                    config_file = str(toml_config)
                    logging.debug("Auto-detected TOML config: %s", config_file)

            # Initialize enhanced configuration with file support
            from vimeo_monitor.config import EnhancedConfigManager

            self.config = EnhancedConfigManager(
                env_file=env_file, config_file=config_file, enable_live_reload=True, enable_backup=True
            )

            # Setup logging as early as possible
            setup_logging(self.config)

            # Initialize performance optimization system
            enable_performance_optimization = getattr(self.config, "enable_performance_optimization", True)
            if enable_performance_optimization:
                self.performance_optimizer = PerformanceOptimizer(self.config)
                logging.info("Performance optimization enabled")
            else:
                self.performance_optimizer = None
                logging.info("Performance optimization disabled")

            # Initialize components with dependency injection
            self.health_monitor = HealthMonitor(self.config)
            self.api_client = VimeoAPIClient(self.config, self.health_monitor, self.performance_optimizer)
            self.stream_manager = StreamManager(self.config, self.health_monitor)
            self.network_monitor = NetworkMonitor(self.config)

            # Integrate network monitor with health monitor
            self.health_monitor.set_network_monitor(self.network_monitor)

            # Initialize overlay if enabled
            self.status_overlay: NetworkStatusOverlay | None = None
            if self.config.display_network_status:
                self.status_overlay = NetworkStatusOverlay(
                    lambda: self.health_monitor.get_enhanced_status(self.stream_manager.current_mode)
                )

            # Application state
            self.keep_looping = True

            logging.info("Monitor application initialized successfully")

        except ConfigurationError as e:
            logging.exception("Configuration error: %s", e)
            raise
        except Exception as e:
            logging.exception("Failed to initialize monitor application: %s", e)
            raise

    def start(self) -> None:
        """Start the monitoring application."""
        try:
            self._log_startup_info()
            self._validate_system()

            # Start performance optimization services
            if self.performance_optimizer:
                self.performance_optimizer.start()
                logging.info("Performance optimization services started")

            # Start network monitoring
            if getattr(self.config, "enable_network_monitoring", True):
                self.network_monitor.start_monitoring()
                logging.info("Network monitoring started")

            # Start overlay if configured
            if self.status_overlay:
                self.status_overlay.start()
                logging.info("Network status overlay started")

            # Run main monitoring loop
            self._run_monitoring_loop()

        except KeyboardInterrupt:
            logging.info("Received interrupt signal. Shutting down...")
        except Exception as e:
            logging.exception("Unexpected error in monitoring application: %s", e)
        finally:
            self._shutdown()

    def _log_startup_info(self) -> None:
        """Log application startup information."""
        config_summary = self.config.get_summary()
        api_info = self.api_client.get_api_info()

        logging.info("Starting Vimeo stream monitor...")
        logging.info("Configuration: %s", config_summary)
        logging.info("API Configuration: %s", api_info)
        logging.info(
            "API Failure Handling: Threshold=%d, Stability=%d, Backoff=%s",
            self.config.api_failure_threshold,
            self.config.api_stability_threshold,
            self.config.api_enable_backoff,
        )

        # Log performance optimization status
        if self.performance_optimizer:
            perf_status = self.performance_optimizer.get_optimization_status()
            metrics_summary = self.performance_optimizer.prometheus_metrics.get_metrics_summary()

            logging.info(
                "Performance Optimization: Cache=%d/%d entries, Monitor=enabled",
                perf_status["cache"]["size"],
                perf_status["cache"]["max_size"],
            )

            # Log metrics server status
            if metrics_summary.get("metrics_server", {}).get("enabled"):
                metrics_endpoint = metrics_summary["metrics_server"]["endpoint"]
                logging.info("Prometheus metrics server enabled: %s", metrics_endpoint)
            else:
                logging.info("Prometheus metrics disabled")

    def _validate_system(self) -> None:
        """Validate system configuration and dependencies."""
        # Validate API configuration
        if not self.api_client.validate_configuration():
            raise ConfigurationError("Invalid API configuration")

        # Validate media paths
        media_validation = self.stream_manager.validate_media_paths()
        logging.info("Media path validation: %s", media_validation)

        # Log warnings for missing optional files
        if not media_validation["holding_image_exists"] and self.config.holding_image_path:
            logging.warning("Holding image configured but not found: %s", self.config.holding_image_path)

        if not media_validation["api_fail_image_exists"] and self.config.api_fail_image_path:
            logging.warning("API failure image configured but not found: %s", self.config.api_fail_image_path)

    def _run_monitoring_loop(self) -> None:
        """Run the main monitoring loop."""
        loop_count = 0
        health_log_interval = max(10, int(300 / self.config.check_interval))  # Log health every ~5 minutes
        performance_log_interval = max(20, int(600 / self.config.check_interval))  # Log performance every ~10 minutes

        while self.keep_looping:
            try:
                loop_count += 1

                # Get stream data from API (with caching if enabled)
                response_data = self.api_client.get_stream_data()

                # Determine mode based on response and failure state
                new_mode = self.stream_manager.determine_mode(response_data)

                # Handle mode changes
                self.stream_manager.handle_mode_change(new_mode, response_data)

                # Check if current process is still healthy
                self.stream_manager.check_process_health()

                # Periodic performance optimization
                if self.performance_optimizer and loop_count % 5 == 0:  # Every 5 loops
                    self.performance_optimizer.periodic_optimization()

                # Log periodic health summary
                if loop_count % health_log_interval == 0:
                    self.health_monitor.log_health_summary()

                # Log periodic performance summary
                if self.performance_optimizer and loop_count % performance_log_interval == 0:
                    self._log_performance_summary()

                # Wait before next check with appropriate interval
                self._wait_for_next_check()

            except KeyboardInterrupt:
                logging.info("Received interrupt signal in monitoring loop")
                self.keep_looping = False
            except Exception as e:
                logging.exception("Unexpected error in monitoring loop: %s", e)
                time.sleep(self.config.check_interval)

    def _log_performance_summary(self) -> None:
        """Log comprehensive performance summary."""
        if not self.performance_optimizer:
            return

        perf_status = self.performance_optimizer.get_optimization_status()

        # Cache statistics
        cache_stats = perf_status.get("cache", {})
        cache_hit_rate = cache_stats.get("hit_rate", 0) * 100

        # Performance metrics
        perf_metrics = perf_status.get("performance", {})
        current_metrics = perf_status.get("current_metrics", {})

        logging.info(
            "🚀 Performance Summary - Cache: %.1f%% hit rate (%d/%d entries) | "
            "CPU: %.1f%% | Memory: %.1fMB | Threads: %d | API Avg: %.0fms",
            cache_hit_rate,
            cache_stats.get("size", 0),
            cache_stats.get("max_size", 0),
            current_metrics.get("cpu_percent", 0),
            current_metrics.get("memory_mb", 0),
            current_metrics.get("threads", 0),
            perf_metrics.get("api_response_time", {}).get("avg_ms", 0),
        )

    def _wait_for_next_check(self) -> None:
        """Wait for the appropriate interval before next check."""
        if self.health_monitor.api_failure_mode:
            wait_time = self.health_monitor.api_retry_interval
            logging.info("In API failure mode. Waiting %d seconds before retry...", wait_time)
            time.sleep(wait_time)
            self.health_monitor.update_retry_interval()
        else:
            time.sleep(self.config.check_interval)

    def _shutdown(self) -> None:
        """Gracefully shutdown the application."""
        logging.info("Shutting down monitor application...")

        # Log final performance summary
        if self.performance_optimizer:
            self._log_performance_summary()

        # Log final health summary
        self.health_monitor.log_health_summary()

        # Stop performance optimization services
        if self.performance_optimizer:
            self.performance_optimizer.stop()
            logging.info("Performance optimization services stopped")

        # Stop network monitoring
        self.network_monitor.stop_monitoring()
        logging.info("Network monitoring stopped")

        # Stop overlay
        if self.status_overlay:
            self.status_overlay.stop()
            logging.info("Network status overlay stopped")

        # Shutdown stream manager
        self.stream_manager.shutdown()

        logging.info("Monitor application shutdown complete")

    def stop(self) -> None:
        """Stop the monitoring loop (for external control)."""
        self.keep_looping = False

    def get_performance_status(self) -> dict[str, Any]:
        """Get current performance status for external monitoring."""
        if self.performance_optimizer:
            return self.performance_optimizer.get_optimization_status()
        return {"error": "Performance optimization not enabled"}

    def clear_caches(self) -> None:
        """Clear all caches for fresh data."""
        if self.performance_optimizer:
            self.performance_optimizer.cache.clear()
            logging.info("All caches cleared")
        else:
            logging.info("No caches to clear")


def main() -> None:
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="Vimeo Stream Monitor")
    parser.add_argument("--env-file", default=".env", help="Path to environment file (default: .env)")
    parser.add_argument(
        "--config-file", help="Path to YAML/TOML configuration file (default: auto-detect from config/)"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Override log level from configuration",
    )

    args = parser.parse_args()

    try:
        app = MonitorApp(env_file=args.env_file, config_file=args.config_file)

        # Override log level if specified
        if args.log_level:
            logging.getLogger().setLevel(getattr(logging, args.log_level))
            logging.info("Log level overridden to: %s", args.log_level)

        app.start()
    except ConfigurationError as e:
        logging.exception("Configuration error: %s", e)
        sys.exit(1)
    except Exception as e:
        logging.exception("Fatal error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
