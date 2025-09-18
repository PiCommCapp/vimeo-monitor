#!/usr/bin/env python3
"""
Test suite for monitor module.
"""

import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vimeo_monitor.monitor import Monitor


@pytest.mark.unit
class TestMonitor:
    """Test cases for Monitor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_config = Mock()
        self.mock_config.vimeo_token = "test_token"
        self.mock_config.vimeo_key = "test_key"
        self.mock_config.vimeo_secret = "test_secret"
        self.mock_config.stream_selection = 1
        self.mock_config.check_interval = 10
        self.mock_config.max_retries = 3
        self.mock_config.get_vimeo_client_config.return_value = {
            "token": "test_token",
            "key": "test_key",
            "secret": "test_secret"
        }

        self.mock_logger = Mock()

    def test_monitor_initialization(self):
        """Test monitor initialization."""
        mock_process_manager = Mock()
        monitor = Monitor(self.mock_config, self.mock_logger, mock_process_manager)
        assert monitor is not None
        assert monitor.config == self.mock_config
        assert monitor.logger == self.mock_logger

    def test_monitor_initialization_with_defaults(self):
        """Test monitor initialization with default values."""
        mock_process_manager = Mock()
        monitor = Monitor(self.mock_config, self.mock_logger, mock_process_manager)
        assert monitor.check_interval == 10
        assert monitor.max_retries == 3
        assert monitor.retry_count == 0

    def test_monitor_initialization_with_custom_values(self):
        """Test monitor initialization with custom values."""
        self.mock_config.check_interval = 30
        self.mock_config.max_retries = 5
        
        mock_process_manager = Mock()
        monitor = Monitor(self.mock_config, self.mock_logger, mock_process_manager)
        assert monitor.check_interval == 30
        assert monitor.max_retries == 5

    @patch('vimeo_monitor.monitor.VimeoClient')
    def test_monitor_vimeo_client_initialization(self, mock_vimeo_client):
        """Test Vimeo client initialization."""
        mock_client_instance = Mock()
        mock_vimeo_client.return_value = mock_client_instance
        
        mock_process_manager = Mock()
        monitor = Monitor(self.mock_config, self.mock_logger, mock_process_manager)
        
        # Check that Vimeo client was initialized
        mock_vimeo_client.assert_called_once_with(
            token=self.mock_config.vimeo_token,
            key=self.mock_config.vimeo_key,
            secret=self.mock_config.vimeo_secret
        )

    def test_monitor_get_stream_url_success(self):
        """Test stream URL retrieval."""
        mock_process_manager = Mock()
        monitor = Monitor(self.mock_config, self.mock_logger, mock_process_manager)
        
        # Initially, last_stream_url should be None
        stream_url = monitor.get_stream_url()
        assert stream_url is None
        
        # Set a stream URL and test retrieval
        monitor.last_stream_url = "https://example.com/stream.m3u8"
        stream_url = monitor.get_stream_url()
        assert stream_url == "https://example.com/stream.m3u8"

    @patch('vimeo_monitor.monitor.VimeoClient')
    def test_monitor_get_stream_url_no_streams(self, mock_vimeo_client):
        """Test stream URL retrieval when no streams are available."""
        # Mock Vimeo client response
        mock_client_instance = Mock()
        mock_vimeo_client.return_value = mock_client_instance
        
        # Mock empty API response
        mock_response = {'data': []}
        mock_client_instance.get.return_value = mock_response
        
        mock_process_manager = Mock()
        monitor = Monitor(self.mock_config, self.mock_logger, mock_process_manager)
        stream_url = monitor.get_stream_url()
        
        # Check that no stream URL was returned
        assert stream_url is None

    @patch('vimeo_monitor.monitor.VimeoClient')
    def test_monitor_get_stream_url_api_error(self, mock_vimeo_client):
        """Test stream URL retrieval with API error."""
        # Mock Vimeo client response
        mock_client_instance = Mock()
        mock_vimeo_client.return_value = mock_client_instance
        
        # Mock API error
        mock_client_instance.get.side_effect = Exception("API Error")
        
        mock_process_manager = Mock()
        monitor = Monitor(self.mock_config, self.mock_logger, mock_process_manager)
        stream_url = monitor.get_stream_url()
        
        # Check that no stream URL was returned due to error
        assert stream_url is None
        # Check that error was logged
        self.mock_logger.error.assert_called()

    @patch('vimeo_monitor.monitor.VimeoClient')
    def test_monitor_get_stream_url_retry_mechanism(self, mock_vimeo_client):
        """Test retry mechanism for stream URL retrieval."""
        # Mock Vimeo client response
        mock_client_instance = Mock()
        mock_vimeo_client.return_value = mock_client_instance
        
        # Mock API response after retries
        mock_response = {
            'data': [
                {
                    'uri': '/videos/12345',
                    'name': 'Test Stream',
                    'link': 'https://vimeo.com/12345',
                    'embed': {
                        'html': '<iframe src="https://player.vimeo.com/video/12345"></iframe>'
                    }
                }
            ]
        }
        
        # First call fails, second call succeeds
        mock_client_instance.get.side_effect = [
            Exception("API Error"),
            mock_response
        ]
        
        mock_process_manager = Mock()
        monitor = Monitor(self.mock_config, self.mock_logger, mock_process_manager)
        stream_url = monitor.get_stream_url()
        
        # Check that stream URL was retrieved after retry
        assert stream_url is not None
        # Check that get was called twice (initial + retry)
        assert mock_client_instance.get.call_count == 2

    @patch('vimeo_monitor.monitor.VimeoClient')
    def test_monitor_get_stream_url_max_retries_exceeded(self, mock_vimeo_client):
        """Test when max retries are exceeded."""
        # Mock Vimeo client response
        mock_client_instance = Mock()
        mock_vimeo_client.return_value = mock_client_instance
        
        # Mock API error for all calls
        mock_client_instance.get.side_effect = Exception("API Error")
        
        mock_process_manager = Mock()
        monitor = Monitor(self.mock_config, self.mock_logger, mock_process_manager)
        stream_url = monitor.get_stream_url()
        
        # Check that no stream URL was returned
        assert stream_url is None
        # Check that get was called max_retries + 1 times
        assert mock_client_instance.get.call_count == self.mock_config.max_retries + 1

    def test_monitor_reset_retry_count(self):
        """Test retry count reset."""
        mock_process_manager = Mock()
        monitor = Monitor(self.mock_config, self.mock_logger, mock_process_manager)
        monitor.retry_count = 5
        
        monitor.reset_retry_count()
        assert monitor.retry_count == 0

    def test_monitor_increment_retry_count(self):
        """Test retry count increment."""
        mock_process_manager = Mock()
        monitor = Monitor(self.mock_config, self.mock_logger, mock_process_manager)
        initial_count = monitor.retry_count
        
        monitor.increment_retry_count()
        assert monitor.retry_count == initial_count + 1

    def test_monitor_should_retry(self):
        """Test retry decision logic."""
        mock_process_manager = Mock()
        monitor = Monitor(self.mock_config, self.mock_logger, mock_process_manager)
        
        # Should retry when under max retries
        monitor.retry_count = 2
        assert monitor.should_retry() is True
        
        # Should not retry when at max retries
        monitor.retry_count = 3
        assert monitor.should_retry() is False

    @patch('vimeo_monitor.monitor.VimeoClient')
    def test_monitor_get_stream_info(self, mock_vimeo_client):
        """Test stream info retrieval."""
        # Mock Vimeo client response
        mock_client_instance = Mock()
        mock_vimeo_client.return_value = mock_client_instance
        
        # Mock API response
        mock_response = {
            'data': [
                {
                    'uri': '/videos/12345',
                    'name': 'Test Stream',
                    'link': 'https://vimeo.com/12345',
                    'embed': {
                        'html': '<iframe src="https://player.vimeo.com/video/12345"></iframe>'
                    }
                }
            ]
        }
        mock_client_instance.get.return_value = mock_response
        
        mock_process_manager = Mock()
        monitor = Monitor(self.mock_config, self.mock_logger, mock_process_manager)
        stream_info = monitor.get_stream_info()
        
        # Check that stream info was retrieved
        assert stream_info is not None
        assert 'data' in stream_info

    @patch('vimeo_monitor.monitor.VimeoClient')
    def test_monitor_get_stream_info_error(self, mock_vimeo_client):
        """Test stream info retrieval with error."""
        # Mock Vimeo client response
        mock_client_instance = Mock()
        mock_vimeo_client.return_value = mock_client_instance
        
        # Mock API error
        mock_client_instance.get.side_effect = Exception("API Error")
        
        mock_process_manager = Mock()
        monitor = Monitor(self.mock_config, self.mock_logger, mock_process_manager)
        stream_info = monitor.get_stream_info()
        
        # Check that no stream info was returned
        assert stream_info is None
        # Check that error was logged
        self.mock_logger.error.assert_called()

    def test_monitor_validate_config(self):
        """Test configuration validation."""
        mock_process_manager = Mock()
        monitor = Monitor(self.mock_config, self.mock_logger, mock_process_manager)
        
        # Should not raise exception with valid config
        monitor.validate_config()

    def test_monitor_validate_config_missing_token(self):
        """Test configuration validation with missing token."""
        self.mock_config.vimeo_token = None
        
        mock_process_manager = Mock()
        monitor = Monitor(self.mock_config, self.mock_logger, mock_process_manager)
        
        # Should raise exception with missing token
        with pytest.raises(ValueError):
            monitor.validate_config()

    def test_monitor_validate_config_missing_key(self):
        """Test configuration validation with missing key."""
        self.mock_config.vimeo_key = None
        
        mock_process_manager = Mock()
        monitor = Monitor(self.mock_config, self.mock_logger, mock_process_manager)
        
        # Should raise exception with missing key
        with pytest.raises(ValueError):
            monitor.validate_config()

    def test_monitor_validate_config_missing_secret(self):
        """Test configuration validation with missing secret."""
        self.mock_config.vimeo_secret = None
        
        mock_process_manager = Mock()
        monitor = Monitor(self.mock_config, self.mock_logger, mock_process_manager)
        
        # Should raise exception with missing secret
        with pytest.raises(ValueError):
            monitor.validate_config()

    @patch('vimeo_monitor.monitor.VimeoClient')
    def test_monitor_check_stream_availability(self, mock_vimeo_client):
        """Test stream availability check."""
        # Mock Vimeo client response
        mock_client_instance = Mock()
        mock_vimeo_client.return_value = mock_client_instance
        
        # Mock API response
        mock_response = {
            'data': [
                {
                    'uri': '/videos/12345',
                    'name': 'Test Stream',
                    'link': 'https://vimeo.com/12345',
                    'embed': {
                        'html': '<iframe src="https://player.vimeo.com/video/12345"></iframe>'
                    }
                }
            ]
        }
        mock_client_instance.get.return_value = mock_response
        
        mock_process_manager = Mock()
        monitor = Monitor(self.mock_config, self.mock_logger, mock_process_manager)
        is_available = monitor.check_stream_availability()
        
        # Check that stream is available
        assert is_available is True

    @patch('vimeo_monitor.monitor.VimeoClient')
    def test_monitor_check_stream_availability_not_available(self, mock_vimeo_client):
        """Test stream availability check when not available."""
        # Mock Vimeo client response
        mock_client_instance = Mock()
        mock_vimeo_client.return_value = mock_client_instance
        
        # Mock empty API response
        mock_response = {'data': []}
        mock_client_instance.get.return_value = mock_response
        
        mock_process_manager = Mock()
        monitor = Monitor(self.mock_config, self.mock_logger, mock_process_manager)
        is_available = monitor.check_stream_availability()
        
        # Check that stream is not available
        assert is_available is False


if __name__ == "__main__":
    pytest.main([__file__])
