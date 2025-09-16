#!/usr/bin/env python3
"""
Network health monitor for Vimeo Monitor.

This module monitors the health of network connections (connectivity, latency, speed).
"""

import subprocess
import time
from typing import Dict, List, Optional
import socket

try:
    import requests
    from prometheus_client import Gauge
except ImportError:
    requests = None
    
    # Define dummy classes for type checking when prometheus_client is not available
    class Gauge:
        def set(self, value): pass
        def __init__(self, *args, **kwargs): pass

try:
    import speedtest
    SPEEDTEST_AVAILABLE = True
except ImportError:
    speedtest = None
    SPEEDTEST_AVAILABLE = False

from ..config import Config
from ..logger import Logger, LoggingContext


class NetworkMonitor:
    """Monitors network health."""

    def __init__(self, config: Config, logger: Logger, registry=None):
        """Initialize network monitor.
        
        Args:
            config: Application configuration
            logger: Application logger
            registry: Prometheus registry
        """
        self.config = config
        self.logger = logger
        self.network_logger = LoggingContext(logger, "NETWORK_HEALTH")
        self.registry = registry
        
        # Check if requests is available
        if requests is None:
            self.network_logger.error(
                "requests library not installed. "
                "Install with: pip install vimeo-monitor[health]"
            )
            raise ImportError("requests library not installed")
        
        # Speedtest configuration
        self.speedtest_enabled = (
            getattr(self.config, "health_network_speedtest_enabled", False) and 
            SPEEDTEST_AVAILABLE
        )
        
        if self.speedtest_enabled and speedtest is None:
            self.network_logger.warning(
                "speedtest-cli library not installed, speedtest disabled. "
                "Install with: pip install vimeo-monitor[health]"
            )
            self.speedtest_enabled = False
        
        # Speedtest interval
        self.speedtest_interval = getattr(self.config, "health_network_speedtest_interval", 300)
        self.last_speedtest_time = 0
        
        # Ping hosts
        self.ping_hosts = getattr(self.config, "health_network_ping_hosts", ["8.8.8.8", "1.1.1.1", "vimeo.com"])
        
        # Last check time
        self.last_check_time = time.time()
        
        # Initialize metrics
        self._setup_metrics()
    
    def _setup_metrics(self):
        """Set up network health metrics."""
        # Connectivity metrics
        self.connectivity = Gauge(
            'vimeo_monitor_network_connectivity',
            'Network connectivity status (1=connected, 0=disconnected)',
            ['host'],
            registry=self.registry
        )
        
        self.latency = Gauge(
            'vimeo_monitor_network_latency_ms',
            'Network latency in milliseconds',
            ['host'],
            registry=self.registry
        )
        
        # Speed metrics (only if speedtest is enabled)
        self.download_speed = Gauge(
            'vimeo_monitor_network_download_mbps',
            'Network download speed in Mbps',
            registry=self.registry
        )
        
        self.upload_speed = Gauge(
            'vimeo_monitor_network_upload_mbps',
            'Network upload speed in Mbps',
            registry=self.registry
        )
        
        self.ping_speed = Gauge(
            'vimeo_monitor_network_ping_ms',
            'Network ping speed in milliseconds',
            registry=self.registry
        )
        
        # DNS resolution time
        self.dns_resolution = Gauge(
            'vimeo_monitor_network_dns_resolution_ms',
            'DNS resolution time in milliseconds',
            ['domain'],
            registry=self.registry
        )
    
    def update_metrics(self):
        """Update network health metrics."""
        try:
            # Update connectivity metrics
            self._update_connectivity_metrics()
            
            # Update speed metrics (if enabled and interval has passed)
            current_time = time.time()
            if (self.speedtest_enabled and 
                (current_time - self.last_speedtest_time) >= self.speedtest_interval):
                self._update_speed_metrics()
                self.last_speedtest_time = current_time
            
            # Update DNS metrics
            self._update_dns_metrics()
            
            self.last_check_time = current_time
            self.network_logger.debug("Network health metrics updated")
        except Exception as e:
            self.network_logger.error(f"Failed to update network health metrics: {e}")
    
    def _update_connectivity_metrics(self):
        """Update connectivity metrics."""
        for host in self.ping_hosts:
            try:
                # Ping the host and get latency
                latency = self._ping_host(host)
                
                if latency is not None:
                    self.connectivity.labels(host=host).set(1)
                    self.latency.labels(host=host).set(latency)
                    self.network_logger.debug(f"Host {host} is reachable with latency {latency:.2f}ms")
                else:
                    self.connectivity.labels(host=host).set(0)
                    self.network_logger.warning(f"Host {host} is unreachable")
            except Exception as e:
                self.connectivity.labels(host=host).set(0)
                self.network_logger.error(f"Error pinging host {host}: {e}")
    
    def _ping_host(self, host: str) -> Optional[float]:
        """Ping a host and return the latency.
        
        Args:
            host: Host to ping
            
        Returns:
            Latency in milliseconds, or None if host is unreachable
        """
        try:
            # Use ping command with 2 packets and 2 second timeout
            cmd = ["ping", "-c", "2", "-W", "2", host]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False  # Don't raise exception on non-zero exit code
            )
            
            # Check if ping was successful
            if result.returncode != 0:
                return None
            
            # Parse output for latency
            output = result.stdout
            if "time=" in output:
                # Find the average time
                avg_line = [line for line in output.splitlines() if "avg" in line]
                if avg_line:
                    # Format: rtt min/avg/max/mdev = 20.806/21.057/21.309/0.251 ms
                    parts = avg_line[0].split("=")[1].strip().split("/")
                    if len(parts) >= 2:
                        return float(parts[1])
            
            return None
        except Exception as e:
            self.network_logger.error(f"Error executing ping command for {host}: {e}")
            return None
    
    def _update_speed_metrics(self):
        """Update speed metrics using speedtest-cli."""
        try:
            self.network_logger.info("Running network speed test")
            
            # Create speedtest instance
            st = speedtest.Speedtest()
            
            # Get best server
            st.get_best_server()
            
            # Get ping
            ping = st.results.ping
            self.ping_speed.set(ping)
            
            # Get download speed
            download = st.download() / 1_000_000  # Convert to Mbps
            self.download_speed.set(download)
            
            # Get upload speed
            upload = st.upload() / 1_000_000  # Convert to Mbps
            self.upload_speed.set(upload)
            
            self.network_logger.info(
                f"Speed test results: ping={ping:.2f}ms, "
                f"download={download:.2f}Mbps, upload={upload:.2f}Mbps"
            )
        except Exception as e:
            self.network_logger.error(f"Failed to run speed test: {e}")
    
    def _update_dns_metrics(self):
        """Update DNS resolution metrics."""
        domains = ["vimeo.com", "google.com", "cloudflare.com"]
        
        for domain in domains:
            try:
                # Measure DNS resolution time
                start_time = time.time()
                socket.gethostbyname(domain)
                resolution_time = (time.time() - start_time) * 1000  # Convert to ms
                
                self.dns_resolution.labels(domain=domain).set(resolution_time)
                self.network_logger.debug(f"DNS resolution time for {domain}: {resolution_time:.2f}ms")
            except Exception as e:
                self.network_logger.error(f"Failed to resolve domain {domain}: {e}")
