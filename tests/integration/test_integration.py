#!/usr/bin/env python3
"""
Integration tests for the Vimeo Monitor system.
"""

import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from vimeo_monitor.config import Config
from vimeo_monitor.logger import Logger
from vimeo_monitor.monitor import Monitor
from vimeo_monitor.process_manager import ProcessManager


@pytest.mark.integration
class TestSystemIntegration:
    """Integration tests for the complete system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, "integration_test.log")
        
        # Create the log file directory if it doesn't exist
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Touch the log file to make sure it exists
        with open(self.log_file, 'a'):
            pass
            
    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up temporary files
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
        os.rmdir(self.temp_dir)

    def setup_test_config(self, integration_test_config):
        """Set up test configuration with the correct log file path."""
        integration_test_config.log_file = self.log_file
        return integration_test_config

    def test_system_initialization(self, integration_test_config):
        """Test complete system initialization."""
        # Set up test configuration
        integration_test_config = self.setup_test_config(integration_test_config)
        
        # Create logger
        logger = Logger(integration_test_config)

        # Create monitor
        process_manager = ProcessManager(integration_test_config, logger)
        monitor = Monitor(integration_test_config, logger, process_manager)

        # Create process manager
        process_manager = ProcessManager(integration_test_config, logger)

        # Verify all components are initialized
        assert logger is not None
        assert monitor is not None
        assert process_manager is not None

        # Verify logger file was created
        assert os.path.exists(self.log_file)

    def test_config_logger_integration(self, integration_test_config):
        """Test configuration and logger integration."""
        # Create logger with config
        logger = Logger(config=integration_test_config)

        # Verify logger was created with config values
        assert logger is not None
        assert logger.log_file == integration_test_config.log_file

    def test_monitor_logger_integration(self, integration_test_config):
        """Test monitor and logger integration."""
        # Set up test configuration
        integration_test_config = self.setup_test_config(integration_test_config)
        
        # Create logger
        logger = Logger(integration_test_config)

        # Create monitor
        process_manager = ProcessManager(integration_test_config, logger)
        monitor = Monitor(integration_test_config, logger, process_manager)

        # Test that monitor can log messages
        monitor.logger.info("Integration test message")

        # Verify message was logged
        with open(self.log_file) as f:
            content = f.read()
            assert "Integration test message" in content

    def test_process_manager_logger_integration(self, integration_test_config):
        """Test process manager and logger integration."""
        # Set up test configuration
        integration_test_config = self.setup_test_config(integration_test_config)
        
        # Create logger
        logger = Logger(integration_test_config)

        # Create process manager
        process_manager = ProcessManager(integration_test_config, logger)

        # Test that process manager can log messages
        process_manager.logger.info("Process manager test message")

        # Verify message was logged
        with open(self.log_file) as f:
            content = f.read()
            assert "Process manager test message" in content

    @patch("vimeo_monitor.monitor.VimeoClient")
    @patch("subprocess.Popen")
    def test_monitor_process_manager_integration(
        self, mock_popen, mock_vimeo_client, integration_test_config
    ):
        """Test monitor and process manager integration."""
        # Mock Popen to return a running process
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process is running
        mock_popen.return_value = mock_process
        
        # Mock Vimeo client
        mock_client_instance = Mock()
        mock_vimeo_client.return_value = mock_client_instance

        # Mock API response
        mock_response = {
            "data": [
                {
                    "uri": "/videos/12345",
                    "name": "Test Stream",
                    "link": "https://vimeo.com/12345",
                    "embed": {
                        "html": '<iframe src="https://player.vimeo.com/video/12345"></iframe>'
                    },
                }
            ]
        }
        mock_client_instance.get.return_value = mock_response

        # Set up test configuration
        integration_test_config = self.setup_test_config(integration_test_config)
        
        # Create logger
        logger = Logger(integration_test_config)

        # Create monitor
        process_manager = ProcessManager(integration_test_config, logger)
        monitor = Monitor(integration_test_config, logger, process_manager)

        # Test workflow: get stream URL and start process
        stream_url = monitor.get_stream_url()
        assert stream_url is not None

        # Start stream process
        process_manager.start_stream_process(stream_url)

        # Verify process was started
        assert process_manager.current_process is not None
        assert process_manager.current_mode == "stream"

    def test_error_handling_integration(self, integration_test_config):
        """Test error handling integration."""
        # Set up test configuration
        integration_test_config = self.setup_test_config(integration_test_config)
        
        # Create logger
        logger = Logger(integration_test_config)

        # Create process manager
        process_manager = ProcessManager(integration_test_config, logger)

        # Create monitor with invalid config
        invalid_config = Mock()
        invalid_config.vimeo_token = None
        invalid_config.vimeo_key = "test_key"
        invalid_config.vimeo_secret = "test_secret"
        invalid_config.stream_selection = 1
        invalid_config.check_interval = 10
        invalid_config.max_retries = 3
        
        # Set up the get_vimeo_client_config mock to return a dictionary
        invalid_config.get_vimeo_client_config.return_value = {
            "key": "test_key",
            "secret": "test_secret"
        }

        # Create a new process manager for the invalid config
        invalid_process_manager = ProcessManager(invalid_config, logger)
        invalid_monitor = Monitor(invalid_config, logger, invalid_process_manager)

        # Test that validation fails
        with pytest.raises(ValueError):
            invalid_monitor.validate_config()

    def test_log_rotation_integration(self, integration_test_config):
        """Test log rotation integration."""
        # Create logger with short rotation period
        # Create a test config with short rotation period
        test_config = Config()
        test_config.log_file = self.log_file
        test_config.log_rotation_days = 1
        logger = Logger(test_config)

        # Log multiple messages
        for i in range(10):
            logger.info(f"Test message {i}")

        # Verify log file exists and has content
        assert os.path.exists(self.log_file)

        with open(self.log_file) as f:
            content = f.read()
            assert "Test message 0" in content
            assert "Test message 9" in content

    @patch("subprocess.Popen")
    def test_process_lifecycle_integration(self, mock_popen, integration_test_config):
        """Test process lifecycle integration."""
        # Mock Popen to return a running process
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process is running
        mock_popen.return_value = mock_process
        
        # Set up test configuration
        integration_test_config = self.setup_test_config(integration_test_config)
        
        # Create logger
        logger = Logger(integration_test_config)

        # Create process manager
        process_manager = ProcessManager(integration_test_config, logger)

        # Start image process
        process_manager.start_image_process("/tmp/test.png")

        # Verify process was started
        assert process_manager.current_process is not None
        assert process_manager.current_mode == "image"
        assert process_manager.is_process_running()

        # Start error process (should stop image process)
        process_manager.start_error_process("/tmp/error.png")

        # Verify process was changed
        assert process_manager.current_process is not None
        assert process_manager.current_mode == "error"
        assert process_manager.is_process_running()

        # Stop process
        process_manager._stop_current_process()

        # Verify process was stopped
        assert process_manager.current_process is None
        assert process_manager.current_mode is None
        assert not process_manager.is_process_running()

    def test_retry_mechanism_integration(self, integration_test_config):
        """Test retry mechanism integration."""
        # Set up test configuration
        integration_test_config = self.setup_test_config(integration_test_config)
        
        # Create logger
        logger = Logger(integration_test_config)

        # Create monitor
        process_manager = ProcessManager(integration_test_config, logger)
        monitor = Monitor(integration_test_config, logger, process_manager)

        # Test retry count management
        assert monitor.retry_count == 0

        monitor.increment_retry_count()
        assert monitor.retry_count == 1

        monitor.reset_retry_count()
        assert monitor.retry_count == 0

        # Test retry decision logic
        # For this test, max_retries is 2 (from integration_test_config)
        monitor.retry_count = 1  # One retry used, one remaining
        assert monitor.should_retry() is True
        
        monitor.retry_count = 2  # At max retries, should not retry
        assert monitor.should_retry() is False

    def test_configuration_validation_integration(self, integration_test_config):
        """Test configuration validation integration."""
        # Set up test configuration
        integration_test_config = self.setup_test_config(integration_test_config)
        
        # Create logger
        logger = Logger(integration_test_config)

        # Test valid configuration
        process_manager = ProcessManager(integration_test_config, logger)
        monitor = Monitor(integration_test_config, logger, process_manager)
        monitor.validate_config()  # Should not raise exception

        # Test invalid configuration
        invalid_config = Mock()
        invalid_config.vimeo_token = None
        invalid_config.vimeo_key = "test_key"
        invalid_config.vimeo_secret = "test_secret"
        invalid_config.stream_selection = 1
        invalid_config.check_interval = 10
        invalid_config.max_retries = 3
        invalid_config.get_vimeo_client_config = Mock(return_value={
            "key": "test_key",
            "secret": "test_secret"
        })

        # Create a new process manager for the invalid config
        invalid_process_manager = ProcessManager(invalid_config, logger)
        invalid_monitor = Monitor(invalid_config, logger, invalid_process_manager)

        # Test that validation fails
        with pytest.raises(ValueError):
            invalid_monitor.validate_config()

    def test_logging_levels_integration(self, integration_test_config):
        """Test logging levels integration."""
        # Create logger with DEBUG level
        # Create a test config with DEBUG level
        test_config = Config()
        test_config.log_file = self.log_file
        test_config.log_level = "DEBUG"
        logger = Logger(test_config)

        # Log messages at different levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")

        # Verify all messages were logged
        with open(self.log_file) as f:
            content = f.read()
            assert "Debug message" in content
            assert "Info message" in content
            assert "Warning message" in content
            assert "Error message" in content
            assert "Critical message" in content

    def test_exception_handling_integration(self, integration_test_config):
        """Test exception handling integration."""
        # Set up test configuration
        integration_test_config = self.setup_test_config(integration_test_config)
        
        # Create logger
        logger = Logger(integration_test_config)

        # Create monitor
        process_manager = ProcessManager(integration_test_config, logger)
        monitor = Monitor(integration_test_config, logger, process_manager)

        # Test exception logging
        try:
            raise ValueError("Test exception")
        except ValueError:
            monitor.logger.exception("Exception occurred in integration test")

        # Verify exception was logged
        with open(self.log_file) as f:
            content = f.read()
            assert "Exception occurred in integration test" in content
            assert "ValueError" in content
            assert "Test exception" in content


@pytest.mark.integration
@pytest.mark.slow
class TestSlowIntegration:
    """Slow integration tests that may take longer to run."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, "slow_integration_test.log")

    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up temporary files
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
        os.rmdir(self.temp_dir)

    @patch("subprocess.Popen")
    def test_long_running_process_integration(self, mock_popen, integration_test_config):
        """Test long-running process integration."""
        # Mock Popen to return a running process
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process is running
        mock_popen.return_value = mock_process
        
        # Create logger
        logger = Logger(integration_test_config)

        # Create process manager
        process_manager = ProcessManager(integration_test_config, logger)

        # Start a process
        process_manager.start_image_process("/tmp/test.png")

        # Let it run for a short time
        time.sleep(0.1)

        # Verify process is still running
        assert process_manager.is_process_running()

        # Get process status
        status = process_manager.get_process_status()
        assert status["running"] is True

    @patch("subprocess.Popen")
    def test_multiple_process_cycles_integration(self, mock_popen, integration_test_config):
        """Test multiple process start/stop cycles."""
        # Mock Popen to return a running process
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process is running
        mock_popen.return_value = mock_process
        
        # Create logger
        logger = Logger(integration_test_config)

        # Create process manager
        process_manager = ProcessManager(integration_test_config, logger)

        # Test multiple process cycles
        for _i in range(3):
            # Start process
            process_manager.start_image_process("/tmp/test.png")
            assert process_manager.current_mode == "image"

            # Let it run briefly
            time.sleep(0.05)

            # Verify process is running
            assert process_manager.is_process_running()

            # Stop process (by starting a new one)
            process_manager.start_error_process("/tmp/error.png")
            assert process_manager.current_mode == "error"


if __name__ == "__main__":
    pytest.main([__file__])
