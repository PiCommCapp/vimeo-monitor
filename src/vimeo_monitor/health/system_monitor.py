#!/usr/bin/env python3
"""
System health monitor for Vimeo Monitor.

This module monitors the health of the system hardware (CPU, memory, temperature, disk).
"""

import os
import platform
import time

try:
    import psutil
    from prometheus_client import Gauge
except ImportError:
    psutil = None

    # Define dummy classes for type checking when prometheus_client is not available
    class Gauge:
        def set(self, value):
            pass

        def __init__(self, *args, **kwargs):
            pass


from ..config import Config
from ..logger import Logger, LoggingContext


class SystemMonitor:
    """Monitors system hardware health."""

    def __init__(self, config: Config, logger: Logger, registry=None):
        """Initialize system monitor.

        Args:
            config: Application configuration
            logger: Application logger
            registry: Prometheus registry
        """
        self.config = config
        self.logger = logger
        self.system_logger = LoggingContext(logger, "SYSTEM_HEALTH")
        self.registry = registry

        # Check if psutil is available
        if psutil is None:
            self.system_logger.error(
                "psutil library not installed. "
                "Install with: pip install vimeo-monitor[health]"
            )
            raise ImportError("psutil library not installed")

        # Last check time
        self.last_check_time = time.time()

        # System information
        self.is_raspberry_pi = self._is_raspberry_pi()
        self.system_logger.info(f"Running on Raspberry Pi: {self.is_raspberry_pi}")

        # Initialize metrics
        self._setup_metrics()

    def _is_raspberry_pi(self) -> bool:
        """Check if running on a Raspberry Pi.

        Returns:
            True if running on a Raspberry Pi, False otherwise
        """
        # Check for Raspberry Pi model file
        if os.path.exists("/proc/device-tree/model"):
            with open("/proc/device-tree/model") as f:
                model = f.read()
                if "raspberry pi" in model.lower():
                    return True

        # Check for ARM architecture on Linux
        if platform.system() == "Linux" and platform.machine().startswith("arm"):
            return True

        return False

    def _setup_metrics(self):
        """Set up system health metrics."""
        # CPU metrics
        self.cpu_usage = Gauge(
            "vimeo_monitor_cpu_usage_percent",
            "CPU usage in percent",
            registry=self.registry,
        )

        self.cpu_temperature = Gauge(
            "vimeo_monitor_cpu_temperature_celsius",
            "CPU temperature in Celsius",
            registry=self.registry,
        )

        self.cpu_load_1 = Gauge(
            "vimeo_monitor_cpu_load_1",
            "CPU load average (1 minute)",
            registry=self.registry,
        )

        self.cpu_load_5 = Gauge(
            "vimeo_monitor_cpu_load_5",
            "CPU load average (5 minutes)",
            registry=self.registry,
        )

        self.cpu_load_15 = Gauge(
            "vimeo_monitor_cpu_load_15",
            "CPU load average (15 minutes)",
            registry=self.registry,
        )

        # Memory metrics
        self.memory_usage = Gauge(
            "vimeo_monitor_memory_usage_percent",
            "Memory usage in percent",
            registry=self.registry,
        )

        self.memory_available = Gauge(
            "vimeo_monitor_memory_available_bytes",
            "Available memory in bytes",
            registry=self.registry,
        )

        self.memory_total = Gauge(
            "vimeo_monitor_memory_total_bytes",
            "Total memory in bytes",
            registry=self.registry,
        )

        # Disk metrics
        self.disk_usage = Gauge(
            "vimeo_monitor_disk_usage_percent",
            "Disk usage in percent",
            ["mountpoint"],
            registry=self.registry,
        )

        self.disk_free = Gauge(
            "vimeo_monitor_disk_free_bytes",
            "Free disk space in bytes",
            ["mountpoint"],
            registry=self.registry,
        )

        # Process metrics
        self.process_cpu = Gauge(
            "vimeo_monitor_process_cpu_percent",
            "CPU usage of the Vimeo Monitor process in percent",
            registry=self.registry,
        )

        self.process_memory = Gauge(
            "vimeo_monitor_process_memory_percent",
            "Memory usage of the Vimeo Monitor process in percent",
            registry=self.registry,
        )

    def update_metrics(self):
        """Update system health metrics."""
        try:
            # Update CPU metrics
            self._update_cpu_metrics()

            # Update memory metrics
            self._update_memory_metrics()

            # Update disk metrics
            self._update_disk_metrics()

            # Update process metrics
            self._update_process_metrics()

            self.last_check_time = time.time()
            self.system_logger.debug("System health metrics updated")
        except Exception as e:
            self.system_logger.error(f"Failed to update system health metrics: {e}")

    def _update_cpu_metrics(self):
        """Update CPU metrics."""
        # CPU usage
        self.cpu_usage.set(psutil.cpu_percent(interval=None))

        # CPU temperature (Raspberry Pi specific)
        if self.is_raspberry_pi:
            try:
                temp = self._get_raspberry_pi_temperature()
                if temp is not None:
                    self.cpu_temperature.set(temp)
            except Exception as e:
                self.system_logger.error(f"Failed to get Raspberry Pi temperature: {e}")

        # CPU load
        load1, load5, load15 = psutil.getloadavg()
        self.cpu_load_1.set(load1)
        self.cpu_load_5.set(load5)
        self.cpu_load_15.set(load15)

    def _get_raspberry_pi_temperature(self) -> float | None:
        """Get Raspberry Pi CPU temperature.

        Returns:
            CPU temperature in Celsius, or None if not available
        """
        try:
            # Try vcgencmd first (most reliable)
            import subprocess

            result = subprocess.run(
                ["vcgencmd", "measure_temp"], capture_output=True, text=True, check=True
            )
            temp_str = result.stdout.strip()
            if "temp=" in temp_str and "'C" in temp_str:
                # Format: temp=42.8'C
                temp = float(temp_str.split("=")[1].split("'")[0])
                return temp
        except (ImportError, FileNotFoundError, subprocess.SubprocessError):
            pass

        # Try thermal zone (Linux)
        try:
            if os.path.exists("/sys/class/thermal/thermal_zone0/temp"):
                with open("/sys/class/thermal/thermal_zone0/temp") as f:
                    temp = int(f.read().strip()) / 1000.0
                    return temp
        except (OSError, ValueError):
            pass

        return None

    def _update_memory_metrics(self):
        """Update memory metrics."""
        memory = psutil.virtual_memory()

        self.memory_usage.set(memory.percent)
        self.memory_available.set(memory.available)
        self.memory_total.set(memory.total)

    def _update_disk_metrics(self):
        """Update disk metrics."""
        # Get root partition
        root = psutil.disk_usage("/")
        self.disk_usage.labels(mountpoint="/").set(root.percent)
        self.disk_free.labels(mountpoint="/").set(root.free)

        # Get project directory partition
        project_dir = str(self.config.project_root)
        project_disk = psutil.disk_usage(project_dir)
        self.disk_usage.labels(mountpoint=project_dir).set(project_disk.percent)
        self.disk_free.labels(mountpoint=project_dir).set(project_disk.free)

    def _update_process_metrics(self):
        """Update process metrics."""
        try:
            # Get current process
            process = psutil.Process()

            # CPU usage
            self.process_cpu.set(process.cpu_percent(interval=None))

            # Memory usage
            self.process_memory.set(process.memory_percent())
        except Exception as e:
            self.system_logger.error(f"Failed to update process metrics: {e}")
