#!/usr/bin/env python3
"""
Metrics collector for Vimeo Monitor health monitoring.

This module collects metrics from various health monitors and formats them
in Prometheus-compatible format.
"""

import threading
import time
from typing import Dict, List, Optional

try:
    from prometheus_client import (
        Counter,
        Gauge,
        generate_latest,
        CollectorRegistry,
        REGISTRY,
    )
except ImportError:
    # Define dummy classes for type checking when prometheus_client is not available
    class Counter:
        def inc(self, amount=1): pass
        def __init__(self, *args, **kwargs): pass
    
    class Gauge:
        def set(self, value): pass
        def __init__(self, *args, **kwargs): pass
    
    def generate_latest(registry=None):
        return b""
    
    class CollectorRegistry:
        def __init__(self, auto_describe=False): pass
    
    REGISTRY = CollectorRegistry()

from ..config import Config
from ..logger import Logger, LoggingContext


class MetricsCollector:
    """Collects and aggregates metrics from all health monitors."""

    def __init__(self, config: Config, logger: Logger, monitor=None, process_manager=None):
        """Initialize metrics collector.
        
        Args:
            config: Application configuration
            logger: Application logger
            monitor: Optional monitor instance for script health monitoring
            process_manager: Optional process manager for process health monitoring
        """
        self.config = config
        self.logger = logger
        self.metrics_logger = LoggingContext(logger, "METRICS")
        self.monitor = monitor
        self.process_manager = process_manager
        
        self.metrics_logger.info("Initializing metrics collector")
        
        # Monitors
        self.script_monitor = None
        self.system_monitor = None
        self.network_monitor = None
        self.stream_monitor = None
        
        # Collection threads
        self.collection_threads = {}
        self.running = False
        
        # Registry for all metrics
        self.registry = REGISTRY
        self.metrics_logger.info("Using Prometheus registry")
        
        # Core metrics
        self._setup_core_metrics()
        self.metrics_logger.info("Core metrics initialized")
    
    def _setup_core_metrics(self):
        """Set up core metrics that are always available."""
        # Core application metrics (not duplicated by monitors)
        self.uptime = Gauge(
            'vimeo_monitor_uptime_seconds',
            'Uptime of the Vimeo Monitor application in seconds',
            registry=self.registry
        )
        
        # Set initial values
        self.uptime.set(0)
        
        # Create a collector initialization metric
        self.collectors_initialized = Gauge(
            'vimeo_monitor_collectors_initialized',
            'Number of health collectors successfully initialized',
            registry=self.registry
        )
        self.collectors_initialized.set(0)
    
    def initialize(self):
        """Initialize metrics collection."""
        if self.running:
            self.metrics_logger.warning("Metrics collection already initialized")
            return
        
        self.metrics_logger.info("Initializing metrics collection")
        
        # Initialize monitors based on configuration
        initialized_count = self._initialize_monitors()
        self.collectors_initialized.set(initialized_count)
        
        if initialized_count == 0:
            self.metrics_logger.warning("No health collectors were initialized")
        else:
            self.metrics_logger.info(f"Successfully initialized {initialized_count} health collectors")
        
        # Set running flag before starting threads
        self.running = True
        
        # Start collection threads
        thread_count = self._start_collection_threads()
        
        if thread_count == 0:
            self.metrics_logger.warning("No collection threads were started")
        else:
            self.metrics_logger.info(f"Started {thread_count} collection threads")
        
        self.metrics_logger.info("Metrics collection initialized")
    
    def _initialize_monitors(self):
        """Initialize health monitors based on configuration.
        
        Returns:
            Number of monitors successfully initialized
        """
        initialized_count = 0
        
        # Script monitor (always enabled if monitor is provided)
        if self.monitor:
            try:
                from .script_monitor import ScriptMonitor
                self.script_monitor = ScriptMonitor(
                    config=self.config,
                    logger=self.logger,
                    monitor=self.monitor,
                    registry=self.registry
                )
                self.metrics_logger.info("Script monitor initialized")
                initialized_count += 1
            except ImportError as e:
                self.metrics_logger.error(f"Failed to initialize script monitor: {e}")
            except Exception as e:
                self.metrics_logger.error(f"Unexpected error initializing script monitor: {e}")
        
        # System monitor (hardware metrics)
        if getattr(self.config, "health_hardware_enabled", False):
            try:
                from .system_monitor import SystemMonitor
                self.system_monitor = SystemMonitor(
                    config=self.config,
                    logger=self.logger,
                    registry=self.registry
                )
                self.metrics_logger.info("System monitor initialized")
                initialized_count += 1
            except ImportError as e:
                self.metrics_logger.error(f"Failed to initialize system monitor: {e}")
            except Exception as e:
                self.metrics_logger.error(f"Unexpected error initializing system monitor: {e}")
        else:
            self.metrics_logger.info("System monitor disabled in configuration")
        
        # Network monitor
        if getattr(self.config, "health_network_enabled", False):
            try:
                from .network_monitor import NetworkMonitor
                self.network_monitor = NetworkMonitor(
                    config=self.config,
                    logger=self.logger,
                    registry=self.registry
                )
                self.metrics_logger.info("Network monitor initialized")
                initialized_count += 1
            except ImportError as e:
                self.metrics_logger.error(f"Failed to initialize network monitor: {e}")
            except Exception as e:
                self.metrics_logger.error(f"Unexpected error initializing network monitor: {e}")
        else:
            self.metrics_logger.info("Network monitor disabled in configuration")
        
        # Stream monitor
        if getattr(self.config, "health_stream_enabled", False):
            try:
                from .stream_monitor import StreamMonitor
                self.stream_monitor = StreamMonitor(
                    config=self.config,
                    logger=self.logger,
                    monitor=self.monitor,
                    process_manager=self.process_manager,
                    registry=self.registry
                )
                self.metrics_logger.info("Stream monitor initialized")
                initialized_count += 1
            except ImportError as e:
                self.metrics_logger.error(f"Failed to initialize stream monitor: {e}")
            except Exception as e:
                self.metrics_logger.error(f"Unexpected error initializing stream monitor: {e}")
        else:
            self.metrics_logger.info("Stream monitor disabled in configuration")
            
        return initialized_count
    
    def _start_collection_threads(self):
        """Start metrics collection threads.
        
        Returns:
            Number of collection threads started
        """
        thread_count = 0
        
        # Script monitor collection thread
        if self.script_monitor:
            interval = self.config.check_interval
            self._start_collection_thread("script", self.script_monitor.update_metrics, interval)
            thread_count += 1
        
        # System monitor collection thread
        if self.system_monitor:
            interval = getattr(self.config, "health_hardware_interval", 10)
            self._start_collection_thread("system", self.system_monitor.update_metrics, interval)
            thread_count += 1
        
        # Network monitor collection thread
        if self.network_monitor:
            interval = getattr(self.config, "health_network_interval", 30)
            self._start_collection_thread("network", self.network_monitor.update_metrics, interval)
            thread_count += 1
        
        # Stream monitor collection thread
        if self.stream_monitor:
            interval = getattr(self.config, "health_stream_interval", 60)
            self._start_collection_thread("stream", self.stream_monitor.update_metrics, interval)
            thread_count += 1
            
        return thread_count
    
    def _start_collection_thread(self, name: str, collection_func, interval: int):
        """Start a collection thread for a specific monitor.
        
        Args:
            name: Name of the monitor
            collection_func: Function to call for collection
            interval: Collection interval in seconds
        """
        def collection_loop():
            self.metrics_logger.info(f"Starting {name} metrics collection loop")
            collection_count = 0
            error_count = 0
            
            while self.running:
                try:
                    start_time = time.time()
                    collection_func()
                    collection_time = time.time() - start_time
                    collection_count += 1
                    
                    if collection_count % 10 == 0:  # Log every 10 collections
                        self.metrics_logger.info(
                            f"{name} metrics collected {collection_count} times, "
                            f"last collection took {collection_time:.3f}s"
                        )
                    else:
                        self.metrics_logger.debug(
                            f"{name} metrics collected in {collection_time:.3f}s"
                        )
                except Exception as e:
                    error_count += 1
                    self.metrics_logger.error(
                        f"Error collecting {name} metrics: {e} "
                        f"(error {error_count} of {collection_count + error_count} attempts)"
                    )
                
                # Sleep for the interval
                for _ in range(interval):
                    if not self.running:
                        break
                    time.sleep(1)
            
            self.metrics_logger.info(
                f"{name} metrics collection stopped after {collection_count} collections "
                f"with {error_count} errors"
            )
        
        thread = threading.Thread(
            target=collection_loop,
            name=f"metrics-{name}",
            daemon=True
        )
        thread.start()
        self.collection_threads[name] = thread
        self.metrics_logger.info(f"Started {name} metrics collection thread (interval: {interval}s)")
    
    def get_metrics(self) -> bytes:
        """Get all metrics in Prometheus format.
        
        Returns:
            Prometheus-formatted metrics as bytes
        """
        # Update uptime
        if hasattr(self.monitor, "system_start_time"):
            uptime = time.time() - self.monitor.system_start_time
            self.uptime.set(uptime)
        
        # Generate metrics
        try:
            metrics_data = generate_latest(self.registry)
            metrics_size = len(metrics_data)
            self.metrics_logger.debug(f"Generated {metrics_size} bytes of metrics data")
            return metrics_data
        except Exception as e:
            self.metrics_logger.error(f"Error generating metrics: {e}")
            return b""
    
    def shutdown(self):
        """Shutdown metrics collection."""
        if not self.running:
            self.metrics_logger.debug("Metrics collection not running, nothing to shut down")
            return
        
        self.metrics_logger.info("Shutting down metrics collection")
        self.running = False
        
        # Wait for collection threads to complete (with timeout)
        for name, thread in self.collection_threads.items():
            if thread.is_alive():
                self.metrics_logger.info(f"Waiting for {name} metrics collection thread to terminate")
                thread.join(timeout=1.0)
                if thread.is_alive():
                    self.metrics_logger.warning(f"{name} metrics collection thread did not terminate")
                else:
                    self.metrics_logger.info(f"{name} metrics collection thread terminated")
        
        self.metrics_logger.info("Metrics collection stopped")
