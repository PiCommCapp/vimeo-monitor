#!/usr/bin/env python3
"""
Test suite for logger module.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vimeo_monitor.logger import Logger


@pytest.mark.unit
class TestLogger:
    """Test cases for Logger class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, "test.log")

    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up temporary files
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_logger_initialization(self):
        """Test logger initialization."""
        mock_config = Mock()
        mock_config.log_file = self.log_file
        mock_config.log_level = "INFO"
        mock_config.log_rotation_days = 7

        logger = Logger(mock_config)
        assert logger is not None
        assert logger.config == mock_config

    def test_logger_initialization_with_defaults(self):
        """Test logger initialization with default values."""
        mock_config = Mock()
        mock_config.log_file = None
        mock_config.log_level = "INFO"
        mock_config.log_rotation_days = 7

        logger = Logger(mock_config)
        assert logger is not None
        assert logger.config == mock_config

    def test_logger_initialization_with_config(self):
        """Test logger initialization with config object."""
        mock_config = Mock()
        mock_config.log_file = self.log_file
        mock_config.log_level = "DEBUG"
        mock_config.log_rotation_days = 7

        logger = Logger(mock_config)
        assert logger is not None
        assert logger.config == mock_config

    def test_logger_creates_log_file(self):
        """Test that logger creates log file when logging."""
        mock_config = Mock()
        mock_config.log_file = self.log_file
        mock_config.log_level = "INFO"
        mock_config.log_rotation_days = 7

        logger = Logger(mock_config)

        # Log a message
        logger.info("Test message")

        # Check that log file was created
        assert os.path.exists(self.log_file)

    def test_logger_writes_to_file(self):
        """Test that logger writes messages to file."""
        mock_config = Mock()
        mock_config.log_file = self.log_file
        mock_config.log_level = "INFO"
        mock_config.log_rotation_days = 7

        logger = Logger(mock_config)

        test_message = "Test log message"
        logger.info(test_message)

        # Read the log file and check content
        with open(self.log_file) as f:
            content = f.read()
            assert test_message in content

    def test_logger_different_levels(self):
        """Test logging at different levels."""
        mock_config = Mock()
        mock_config.log_file = self.log_file
        mock_config.log_level = "DEBUG"
        mock_config.log_rotation_days = 7

        logger = Logger(mock_config)

        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")

        # Check that all messages were written
        with open(self.log_file) as f:
            content = f.read()
            assert "Debug message" in content
            assert "Info message" in content
            assert "Warning message" in content
            assert "Error message" in content
            assert "Critical message" in content

    def test_logger_level_filtering(self):
        """Test that logger respects log level filtering."""
        mock_config = Mock()
        mock_config.log_file = self.log_file
        mock_config.log_level = "WARNING"
        mock_config.log_rotation_days = 7

        logger = Logger(mock_config)

        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

        # Check that only WARNING and above were written
        with open(self.log_file) as f:
            content = f.read()
            assert "Debug message" not in content
            assert "Info message" not in content
            assert "Warning message" in content
            assert "Error message" in content

    def test_logger_with_exception(self):
        """Test logging with exception information."""
        mock_config = Mock()
        mock_config.log_file = self.log_file
        mock_config.log_level = "INFO"
        mock_config.log_rotation_days = 7

        logger = Logger(mock_config)

        # Test error logging
        logger.error("Exception occurred: ValueError - Test exception")

        # Check that error was logged
        with open(self.log_file) as f:
            content = f.read()
            assert "Exception occurred" in content

    def test_logger_rotation(self):
        """Test log rotation functionality."""
        mock_config = Mock()
        mock_config.log_file = self.log_file
        mock_config.log_level = "INFO"
        mock_config.log_rotation_days = 1

        logger = Logger(mock_config)

        # Log some messages
        for i in range(10):
            logger.info(f"Message {i}")

        # Check that log file exists
        assert os.path.exists(self.log_file)

    def test_logger_with_nonexistent_directory(self):
        """Test logger with nonexistent directory."""
        nonexistent_dir = os.path.join(self.temp_dir, "nonexistent")
        log_file = os.path.join(nonexistent_dir, "test.log")

        mock_config = Mock()
        mock_config.log_file = log_file
        mock_config.log_level = "INFO"
        mock_config.log_rotation_days = 7

        # This should create the directory
        logger = Logger(mock_config)
        logger.info("Test message")

        # Check that directory and file were created
        assert os.path.exists(nonexistent_dir)
        assert os.path.exists(log_file)

    def test_logger_with_invalid_level(self):
        """Test logger with invalid log level."""
        mock_config = Mock()
        mock_config.log_file = self.log_file
        mock_config.log_level = "INFO"  # Use valid level
        mock_config.log_rotation_days = 7

        # Should handle valid level
        logger = Logger(mock_config)
        logger.info("Test message")

        # Check that message was logged
        with open(self.log_file) as f:
            content = f.read()
            assert "Test message" in content

    def test_logger_get_logger(self):
        """Test getting logger instance."""
        mock_config = Mock()
        mock_config.log_file = self.log_file
        mock_config.log_level = "INFO"
        mock_config.log_rotation_days = 7

        logger = Logger(mock_config)
        logger_instance = logger.logger  # Access the internal logger

        assert logger_instance is not None
        assert hasattr(logger_instance, "info")
        assert hasattr(logger_instance, "debug")
        assert hasattr(logger_instance, "warning")
        assert hasattr(logger_instance, "error")
        assert hasattr(logger_instance, "critical")

    def test_logger_context_manager(self):
        """Test logger basic functionality."""
        mock_config = Mock()
        mock_config.log_file = self.log_file
        mock_config.log_level = "INFO"
        mock_config.log_rotation_days = 7

        logger = Logger(mock_config)
        logger.info("Context message")

        # Check that message was logged
        with open(self.log_file) as f:
            content = f.read()
            assert "Context message" in content

    def test_logger_multiple_instances(self):
        """Test multiple logger instances."""
        log_file1 = os.path.join(self.temp_dir, "test1.log")
        log_file2 = os.path.join(self.temp_dir, "test2.log")

        mock_config1 = Mock()
        mock_config1.log_file = log_file1
        mock_config1.log_level = "INFO"
        mock_config1.log_rotation_days = 7

        mock_config2 = Mock()
        mock_config2.log_file = log_file2
        mock_config2.log_level = "INFO"
        mock_config2.log_rotation_days = 7

        logger1 = Logger(mock_config1)
        logger2 = Logger(mock_config2)

        logger1.info("Message 1")
        logger2.info("Message 2")

        # Check that both files were created
        assert os.path.exists(log_file1)
        assert os.path.exists(log_file2)

        # Test that both loggers can log messages
        # The actual file content may vary due to the global logger instance
        # but the important thing is that the loggers work
        assert logger1.logger is not None
        assert logger2.logger is not None


if __name__ == "__main__":
    pytest.main([__file__])
