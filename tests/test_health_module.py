#!/usr/bin/env python3
"""
Tests for the health monitoring system.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from vimeo_monitor.config import Config


class TestHealthMonitoringConfig(unittest.TestCase):
    """Test health monitoring configuration."""

    def setUp(self):
        # Save original environment
        self.original_env = os.environ.copy()

        # Set up test environment variables
        os.environ["HEALTH_MONITORING_ENABLED"] = "true"
        os.environ["HEALTH_METRICS_PORT"] = "8080"
        os.environ["HEALTH_METRICS_HOST"] = "127.0.0.1"
        os.environ["HEALTH_HARDWARE_INTERVAL"] = "15"
        os.environ["HEALTH_NETWORK_INTERVAL"] = "30"
        os.environ["HEALTH_STREAM_INTERVAL"] = "60"
        os.environ["HEALTH_HARDWARE_ENABLED"] = "true"
        os.environ["HEALTH_NETWORK_ENABLED"] = "true"
        os.environ["HEALTH_STREAM_ENABLED"] = "true"
        os.environ["HEALTH_NETWORK_PING_HOSTS"] = "8.8.8.8,1.1.1.1"
        os.environ["HEALTH_NETWORK_SPEEDTEST_ENABLED"] = "false"
        os.environ["HEALTH_STREAM_FFPROBE_TIMEOUT"] = "10"

    def tearDown(self):
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_health_config_loading(self):
        """Test that health monitoring configuration is loaded correctly."""
        config = Config()

        # Check that health monitoring is enabled
        self.assertTrue(config.health_monitoring_enabled)

        # Check core settings
        self.assertEqual(config.health_metrics_port, 8080)
        self.assertEqual(config.health_metrics_host, "127.0.0.1")

        # Check intervals
        self.assertEqual(config.health_hardware_interval, 15)
        self.assertEqual(config.health_network_interval, 30)
        self.assertEqual(config.health_stream_interval, 60)

        # Check feature toggles
        self.assertTrue(config.health_hardware_enabled)
        self.assertTrue(config.health_network_enabled)
        self.assertTrue(config.health_stream_enabled)

        # Check network configuration
        self.assertEqual(config.health_network_ping_hosts, ["8.8.8.8", "1.1.1.1"])
        self.assertFalse(config.health_network_speedtest_enabled)

        # Check stream configuration
        self.assertEqual(config.health_stream_ffprobe_timeout, 10)

    def test_health_config_defaults(self):
        """Test that health monitoring configuration defaults are set correctly."""
        # Only set the enabled flag
        os.environ.clear()
        os.environ.update(self.original_env)
        os.environ["HEALTH_MONITORING_ENABLED"] = "true"

        config = Config()

        # Check that health monitoring is enabled
        self.assertTrue(config.health_monitoring_enabled)

        # Check default core settings
        self.assertEqual(config.health_metrics_port, 8080)
        self.assertEqual(config.health_metrics_host, "0.0.0.0")

        # Check default intervals
        self.assertEqual(config.health_hardware_interval, 30)
        self.assertEqual(config.health_network_interval, 30)
        self.assertEqual(config.health_stream_interval, 60)

        # Check default feature toggles
        self.assertTrue(config.health_hardware_enabled)
        self.assertTrue(config.health_network_enabled)
        self.assertTrue(config.health_stream_enabled)

        # Check default network configuration
        self.assertEqual(
            len(config.health_network_ping_hosts), 3
        )  # Default: 8.8.8.8, 1.1.1.1, vimeo.com
        self.assertTrue(config.health_network_speedtest_enabled)
        self.assertEqual(config.health_network_speedtest_interval, 300)

        # Check default stream configuration
        self.assertEqual(config.health_stream_ffprobe_timeout, 29)

    def test_health_config_validation(self):
        """Test that health monitoring configuration validation works correctly."""
        # Test invalid port
        os.environ["HEALTH_METRICS_PORT"] = "70000"  # Invalid port

        config = Config()
        with self.assertRaises(ValueError):
            config.validate()

        # Test invalid interval
        os.environ["HEALTH_METRICS_PORT"] = "8080"  # Valid port
        os.environ["HEALTH_HARDWARE_INTERVAL"] = "0"  # Invalid interval

        config = Config()
        with self.assertRaises(ValueError):
            config.validate()

        # Test invalid speedtest interval
        os.environ["HEALTH_HARDWARE_INTERVAL"] = "10"  # Valid interval
        os.environ["HEALTH_NETWORK_SPEEDTEST_INTERVAL"] = "30"  # Too low

        config = Config()
        with self.assertRaises(ValueError):
            config.validate()


@unittest.skip("Integration test - requires health monitoring dependencies")
class TestHealthModuleIntegration(unittest.TestCase):
    """Integration tests for the health module."""

    def setUp(self):
        # Save original environment
        self.original_env = os.environ.copy()

        # Set up test environment variables
        os.environ["HEALTH_MONITORING_ENABLED"] = "true"
        os.environ["HEALTH_METRICS_PORT"] = "8081"  # Use non-default port for testing
        os.environ["HEALTH_METRICS_HOST"] = "127.0.0.1"
        os.environ["HEALTH_HARDWARE_ENABLED"] = (
            "false"  # Disable hardware monitoring for testing
        )
        os.environ["HEALTH_NETWORK_ENABLED"] = (
            "false"  # Disable network monitoring for testing
        )
        os.environ["HEALTH_STREAM_ENABLED"] = (
            "false"  # Disable stream monitoring for testing
        )

    def tearDown(self):
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_health_module_startup_shutdown(self):
        """Test that the health module can start and shut down."""
        try:
            from vimeo_monitor.health_module import HealthModule
            from vimeo_monitor.logger import Logger

            # Create mock logger
            logger = MagicMock(spec=Logger)

            # Create config
            config = Config()

            # Create health module
            health_module = HealthModule(config=config, logger=logger)

            # Start health module
            health_module.start()

            # Check that it's running
            self.assertTrue(health_module.running)

            # Shut down health module
            health_module.shutdown()

            # Check that it's not running
            self.assertFalse(health_module.running)

        except ImportError:
            self.skipTest("Health monitoring dependencies not installed")


if __name__ == "__main__":
    unittest.main()
