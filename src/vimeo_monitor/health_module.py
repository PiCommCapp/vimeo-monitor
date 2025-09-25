#!/usr/bin/env python3
"""
Health monitoring module for Vimeo Monitor.

This module coordinates health monitoring components and exposes a Prometheus-compatible
metrics endpoint for monitoring the health of the Vimeo Monitor application.
"""

import threading
from typing import Any

try:
    import fastapi
    import uvicorn
    from prometheus_client import CONTENT_TYPE_LATEST
except ImportError:
    fastapi = None
    uvicorn = None

from .config import Config
from .logger import Logger, LoggingContext


class HealthModule:
    """Main health monitoring coordinator."""

    def __init__(
        self,
        config: Config,
        logger: Logger,
        monitor: Any = None,
        process_manager: Any = None,
    ) -> None:
        """Initialize health monitoring module.

        Args:
            config: Application configuration
            logger: Application logger
            monitor: Optional monitor instance for script health monitoring
            process_manager: Optional process manager for process health monitoring
        """
        self.config = config
        self.logger = logger
        self.health_logger = LoggingContext(logger, "HEALTH")
        self.monitor = monitor
        self.process_manager = process_manager

        self.health_logger.info("Initializing health monitoring module")

        # Check if health monitoring dependencies are available
        if not all([fastapi, uvicorn]):
            self.health_logger.error(
                "Health monitoring dependencies not installed. "
                "Install with: pip install vimeo-monitor[health]"
            )
            raise ImportError("Health monitoring dependencies not installed")

        # Initialize metrics collector
        try:
            from .health.metrics_collector import MetricsCollector

            self.metrics_collector = MetricsCollector(
                config=config,
                logger=logger,
                monitor=monitor,
                process_manager=process_manager,
            )
            self.health_logger.info("Metrics collector initialized successfully")
        except ImportError as e:
            self.health_logger.error(f"Failed to initialize metrics collector: {e}")
            raise

        # FastAPI server
        self.app = fastapi.FastAPI(
            title="Vimeo Monitor Health",
            description="Health monitoring for Vimeo Monitor",
            version="1.0.0",
            docs_url=None,
            redoc_url=None,
        )

        # Server thread
        self.server = None
        self.server_thread: threading.Thread | None = None
        self.running = False

        # Configure routes
        self._configure_routes()
        self.health_logger.info("FastAPI routes configured")

        # Log configuration details
        self._log_configuration()

    def _log_configuration(self) -> None:
        """Log health monitoring configuration."""
        self.health_logger.info(
            f"Health metrics host: {self.config.health_metrics_host}"
        )
        self.health_logger.info(
            f"Health metrics port: {self.config.health_metrics_port}"
        )

        # Log enabled collectors
        enabled_collectors = []
        if (
            hasattr(self.config, "health_hardware_enabled")
            and self.config.health_hardware_enabled
        ):
            enabled_collectors.append("Hardware")
            self.health_logger.info(
                f"Hardware monitoring interval: {self.config.health_hardware_interval}s"
            )

        if (
            hasattr(self.config, "health_network_enabled")
            and self.config.health_network_enabled
        ):
            enabled_collectors.append("Network")
            self.health_logger.info(
                f"Network monitoring interval: {self.config.health_network_interval}s"
            )
            if (
                hasattr(self.config, "health_network_speedtest_enabled")
                and self.config.health_network_speedtest_enabled
            ):
                self.health_logger.info(
                    f"Network speedtest enabled (interval: {self.config.health_network_speedtest_interval}s)"
                )
                self.health_logger.info(
                    f"Network ping hosts: {self.config.health_network_ping_hosts}"
                )

        if (
            hasattr(self.config, "health_stream_enabled")
            and self.config.health_stream_enabled
        ):
            enabled_collectors.append("Stream")
            self.health_logger.info(
                f"Stream monitoring interval: {self.config.health_stream_interval}s"
            )
            self.health_logger.info(
                f"FFprobe timeout: {self.config.health_stream_ffprobe_timeout}s"
            )

        # Always include script health
        enabled_collectors.append("Script")

        self.health_logger.info(f"Enabled collectors: {', '.join(enabled_collectors)}")

    def _configure_routes(self) -> None:
        """Configure FastAPI routes."""

        @self.app.get("/metrics")
        async def metrics() -> fastapi.Response:
            """Prometheus metrics endpoint."""
            self.health_logger.debug("Metrics endpoint accessed")
            metrics_data = self.metrics_collector.get_metrics()
            return fastapi.Response(
                content=metrics_data, media_type=CONTENT_TYPE_LATEST
            )

        @self.app.get("/health")
        async def health() -> dict[str, str]:
            """Simple health check endpoint."""
            self.health_logger.debug("Health check endpoint accessed")
            return {"status": "healthy"}

        @self.app.get("/")
        async def root() -> dict[str, Any]:
            """Root endpoint with basic information."""
            self.health_logger.debug("Root endpoint accessed")
            return {
                "name": "Vimeo Monitor Health",
                "description": "Health monitoring for Vimeo Monitor",
                "version": "1.0.0",
                "endpoints": [
                    {"path": "/metrics", "description": "Prometheus metrics endpoint"},
                    {"path": "/health", "description": "Simple health check endpoint"},
                ],
            }

    def start(self) -> None:
        """Start health monitoring."""
        if self.running:
            self.health_logger.warning("Health monitoring already running")
            return

        self.health_logger.info("Starting health monitoring")

        # Initialize metrics collector
        self.metrics_collector.initialize()

        # Start FastAPI server in a separate thread
        self.server_thread = threading.Thread(
            target=self._run_server, daemon=True, name="health-server-thread"
        )
        self.server_thread.start()

        self.running = True
        self.health_logger.info(
            f"Health monitoring started on http://{self.config.health_metrics_host}:{self.config.health_metrics_port}"
        )
        self.health_logger.info("Available endpoints: /metrics, /health")

    def _run_server(self) -> None:
        """Run FastAPI server in a separate thread."""
        try:
            self.health_logger.info(
                f"Starting FastAPI server on {self.config.health_metrics_host}:{self.config.health_metrics_port}"
            )
            uvicorn.run(
                self.app,
                host=self.config.health_metrics_host,
                port=self.config.health_metrics_port,
                log_level="error",
                access_log=False,
            )
        except Exception as e:
            self.health_logger.error(f"Failed to start health monitoring server: {e}")

    def shutdown(self) -> None:
        """Gracefully shutdown health monitoring."""
        if not self.running:
            self.health_logger.debug(
                "Health monitoring not running, nothing to shut down"
            )
            return

        self.health_logger.info("Shutting down health monitoring")

        # Stop metrics collector
        try:
            self.metrics_collector.shutdown()
            self.health_logger.info("Metrics collector stopped")
        except Exception as e:
            self.health_logger.error(f"Error shutting down metrics collector: {e}")

        # Stop server
        self.running = False

        # Wait for server thread to complete (with timeout)
        if self.server_thread and self.server_thread.is_alive():
            self.health_logger.info("Waiting for server thread to terminate")
            self.server_thread.join(timeout=2.0)
            if self.server_thread.is_alive():
                self.health_logger.warning(
                    "Server thread did not terminate within timeout"
                )
            else:
                self.health_logger.info("Server thread terminated successfully")

        self.health_logger.info("Health monitoring stopped")
