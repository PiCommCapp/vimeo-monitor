#!/usr/bin/env python3
"""
Error handling and recovery scenario tests.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from vimeo_monitor.config import Config
from vimeo_monitor.logger import Logger
from vimeo_monitor.monitor import Monitor
from vimeo_monitor.process_manager import ProcessManager


@pytest.mark.error_scenarios
class TestErrorHandling:
    """Test error handling and recovery scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, "error_test.log")

    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up temporary files
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
        os.rmdir(self.temp_dir)

    def test_config_validation_errors(self):
        """Test configuration validation error scenarios."""
        # Test missing Vimeo token
        with patch('vimeo_monitor.config.load_dotenv'), \
             patch.dict(os.environ, {
                 'VIMEO_KEY': 'test_key',
                 'VIMEO_SECRET': 'test_secret',
                 'STATIC_IMAGE_PATH': 'media/static_image.jpg',
                 'ERROR_IMAGE_PATH': 'media/error_image.jpg'
             }, clear=True):
            config = Config()
            with pytest.raises(ValueError):
                config.validate()

        # Test missing Vimeo key
        with patch('vimeo_monitor.config.load_dotenv'), \
             patch.dict(os.environ, {
                 'VIMEO_TOKEN': 'test_token',
                 'VIMEO_SECRET': 'test_secret',
                 'STATIC_IMAGE_PATH': 'media/static_image.jpg',
                 'ERROR_IMAGE_PATH': 'media/error_image.jpg'
             }, clear=True):
            config = Config()
            with pytest.raises(ValueError):
                config.validate()

        # Test missing Vimeo secret
        with patch('vimeo_monitor.config.load_dotenv'), \
             patch.dict(os.environ, {
                 'VIMEO_TOKEN': 'test_token',
                 'VIMEO_KEY': 'test_key',
                 'STATIC_IMAGE_PATH': 'media/static_image.jpg',
                 'ERROR_IMAGE_PATH': 'media/error_image.jpg'
             }, clear=True):
            config = Config()
            with pytest.raises(ValueError):
                config.validate()

    def test_config_invalid_paths(self):
        """Test configuration with invalid file paths."""
        with patch.dict(os.environ, {
            'VIMEO_TOKEN': 'test_token',
            'VIMEO_KEY': 'test_key',
            'VIMEO_SECRET': 'test_secret',
            'STATIC_IMAGE_PATH': '/nonexistent/path.png',
            'ERROR_IMAGE_PATH': '/nonexistent/error.png'
        }, clear=True):
            config = Config()
            with pytest.raises(FileNotFoundError):
                config.validate()

    def test_config_invalid_values(self):
        """Test configuration with invalid values."""
        with patch.dict(os.environ, {
            'VIMEO_TOKEN': 'test_token',
            'VIMEO_KEY': 'test_key',
            'VIMEO_SECRET': 'test_secret',
            'STREAM_SELECTION': 'invalid',
            'CHECK_INTERVAL': '-1',
            'MAX_RETRIES': '0'
        }, clear=True):
            config = Config()
            # Should handle invalid values gracefully
            assert config.stream_selection == 1  # Default value
            assert config.check_interval == 10  # Default value
            assert config.max_retries == 3  # Default value

    def test_logger_file_permission_errors(self):
        """Test logger with file permission errors."""
        # Test with read-only directory
        read_only_dir = os.path.join(self.temp_dir, "readonly")
        os.makedirs(read_only_dir)
        os.chmod(read_only_dir, 0o444)  # Read-only
        
        log_file = os.path.join(read_only_dir, "test.log")
        
        # This should handle permission errors gracefully
        # Create a test config with the log file
        test_config = Config()
        test_config.log_file = log_file
        logger = Logger(test_config)
        logger.info("Test message")
        
        # Clean up
        os.chmod(read_only_dir, 0o755)
        os.rmdir(read_only_dir)

    def test_logger_disk_space_errors(self):
        """Test logger with disk space errors."""
        # Mock disk space error
        with patch('vimeo_monitor.config.load_dotenv'), \
             patch('builtins.open', side_effect=OSError("No space left on device")):
            # Create a test config with the log file
            test_config = Config()
            test_config.log_file = self.log_file
            logger = Logger(test_config)
            # Should handle disk space errors gracefully
            logger.info("Test message")

    def test_monitor_api_connection_errors(self, mock_config, mock_logger):
        """Test monitor with API connection errors."""
        with patch('vimeo_monitor.monitor.VimeoClient') as mock_vimeo_client:
            # Mock connection error
            mock_client_instance = Mock()
            mock_vimeo_client.return_value = mock_client_instance
            mock_client_instance.get.side_effect = ConnectionError("Connection failed")
            
            mock_process_manager = Mock()
            monitor = Monitor(mock_config, mock_logger, mock_process_manager)
            stream_url = monitor.get_stream_url()
            
            # Should return None and log error
            assert stream_url is None
            mock_logger.error.assert_called()

    def test_monitor_api_timeout_errors(self, mock_config, mock_logger):
        """Test monitor with API timeout errors."""
        with patch('vimeo_monitor.monitor.VimeoClient') as mock_vimeo_client:
            # Mock timeout error
            mock_client_instance = Mock()
            mock_vimeo_client.return_value = mock_client_instance
            mock_client_instance.get.side_effect = TimeoutError("Request timed out")
            
            mock_process_manager = Mock()
            monitor = Monitor(mock_config, mock_logger, mock_process_manager)
            stream_url = monitor.get_stream_url()
            
            # Should return None and log error
            assert stream_url is None
            mock_logger.error.assert_called()

    def test_monitor_api_rate_limit_errors(self, mock_config, mock_logger):
        """Test monitor with API rate limit errors."""
        with patch('vimeo_monitor.monitor.VimeoClient') as mock_vimeo_client:
            # Mock rate limit error
            mock_client_instance = Mock()
            mock_vimeo_client.return_value = mock_client_instance
            mock_client_instance.get.side_effect = Exception("Rate limit exceeded")
            
            mock_process_manager = Mock()
            monitor = Monitor(mock_config, mock_logger, mock_process_manager)
            stream_url = monitor.get_stream_url()
            
            # Should return None and log error
            assert stream_url is None
            mock_logger.error.assert_called()

    def test_monitor_retry_exhaustion(self, mock_config, mock_logger):
        """Test monitor when retries are exhausted."""
        with patch('vimeo_monitor.monitor.VimeoClient') as mock_vimeo_client:
            # Mock persistent error
            mock_client_instance = Mock()
            mock_vimeo_client.return_value = mock_client_instance
            mock_client_instance.get.side_effect = Exception("Persistent error")
            
            mock_process_manager = Mock()
            monitor = Monitor(mock_config, mock_logger, mock_process_manager)
            stream_url = monitor.get_stream_url()
            
            # Should return None after max retries
            assert stream_url is None
            assert mock_client_instance.get.call_count == mock_config.max_retries + 1

    def test_process_manager_process_creation_errors(self, mock_config, mock_logger):
        """Test process manager with process creation errors."""
        with patch('subprocess.Popen', side_effect=OSError("Process creation failed")):
            process_manager = ProcessManager(mock_config, mock_logger)
            
            # Should handle process creation errors gracefully
            process_manager.start_stream_process("https://example.com/stream.m3u8")
            
            # Process should not be started
            assert process_manager.current_process is None
            mock_logger.error.assert_called()

    def test_process_manager_process_crash_recovery(self, mock_config, mock_logger):
        """Test process manager process crash recovery."""
        with patch('subprocess.Popen') as mock_popen:
            # Mock process that crashes
            mock_process = Mock()
            mock_process.poll.return_value = 1  # Process crashed
            mock_popen.return_value = mock_process
            
            process_manager = ProcessManager(mock_config, mock_logger)
            process_manager.start_stream_process("https://example.com/stream.m3u8")
            
            # Simulate process crash
            process_manager.current_process = mock_process
            
            # Test restart logic
            result = process_manager.restart_process()
            assert result is True
            assert process_manager.restart_count == 1

    def test_process_manager_max_restarts_exceeded(self, mock_config, mock_logger):
        """Test process manager when max restarts are exceeded."""
        with patch('subprocess.Popen') as mock_popen:
            # Mock process that keeps crashing
            mock_process = Mock()
            mock_process.poll.return_value = 1  # Process crashed
            mock_popen.return_value = mock_process
            
            process_manager = ProcessManager(mock_config, mock_logger)
            process_manager.restart_count = mock_config.max_retries
            
            # Test restart when max retries exceeded
            result = process_manager.restart_process()
            # Should still allow restart due to time reset logic
            assert result is True

    def test_process_manager_zombie_process_handling(self, mock_config, mock_logger):
        """Test process manager zombie process handling."""
        with patch('subprocess.Popen') as mock_popen:
            # Mock zombie process
            mock_process = Mock()
            mock_process.poll.return_value = None  # Process appears running
            mock_process.pid = 12345
            mock_popen.return_value = mock_process
            
            process_manager = ProcessManager(mock_config, mock_logger)
            process_manager.start_stream_process("https://example.com/stream.m3u8")
            
            # Simulate zombie process
            process_manager.current_process = mock_process
            
            # Test zombie detection
            is_running = process_manager.is_process_running()
            assert is_running is True

    def test_network_failure_scenarios(self, mock_config, mock_logger):
        """Test network failure scenarios."""
        with patch('vimeo_monitor.monitor.VimeoClient') as mock_vimeo_client:
            # Mock various network errors
            network_errors = [
                ConnectionError("Network unreachable"),
                TimeoutError("Connection timed out"),
                Exception("DNS resolution failed"),
                Exception("SSL certificate error")
            ]
            
            for error in network_errors:
                mock_client_instance = Mock()
                mock_vimeo_client.return_value = mock_client_instance
                mock_client_instance.get.side_effect = error
                
                mock_process_manager = Mock()
                monitor = Monitor(mock_config, mock_logger, mock_process_manager)
                stream_url = monitor.get_stream_url()
                
                # Should handle all network errors gracefully
                assert stream_url is None
                mock_logger.error.assert_called()

    def test_memory_exhaustion_scenarios(self, mock_config, mock_logger):
        """Test memory exhaustion scenarios."""
        with patch('vimeo_monitor.monitor.VimeoClient') as mock_vimeo_client:
            # Mock memory error
            mock_client_instance = Mock()
            mock_vimeo_client.return_value = mock_client_instance
            mock_client_instance.get.side_effect = MemoryError("Out of memory")
            
            mock_process_manager = Mock()
            monitor = Monitor(mock_config, mock_logger, mock_process_manager)
            stream_url = monitor.get_stream_url()
            
            # Should handle memory errors gracefully
            assert stream_url is None
            mock_logger.error.assert_called()

    def test_concurrent_access_errors(self, mock_config, mock_logger):
        """Test concurrent access error scenarios."""
        with patch('vimeo_monitor.monitor.VimeoClient') as mock_vimeo_client:
            # Mock concurrent access error
            mock_client_instance = Mock()
            mock_vimeo_client.return_value = mock_client_instance
            mock_client_instance.get.side_effect = Exception("Resource locked")
            
            mock_process_manager = Mock()
            monitor = Monitor(mock_config, mock_logger, mock_process_manager)
            stream_url = monitor.get_stream_url()
            
            # Should handle concurrent access errors gracefully
            assert stream_url is None
            mock_logger.error.assert_called()

    def test_corrupted_data_handling(self, mock_config, mock_logger):
        """Test corrupted data handling scenarios."""
        with patch('vimeo_monitor.monitor.VimeoClient') as mock_vimeo_client:
            # Mock corrupted response
            mock_client_instance = Mock()
            mock_vimeo_client.return_value = mock_client_instance
            mock_client_instance.get.return_value = "corrupted data"
            
            mock_process_manager = Mock()
            monitor = Monitor(mock_config, mock_logger, mock_process_manager)
            stream_url = monitor.get_stream_url()
            
            # Should handle corrupted data gracefully
            assert stream_url is None
            mock_logger.error.assert_called()

    def test_system_resource_exhaustion(self, mock_config, mock_logger):
        """Test system resource exhaustion scenarios."""
        with patch('subprocess.Popen', side_effect=OSError("Too many open files")):
            process_manager = ProcessManager(mock_config, mock_logger)
            
            # Should handle resource exhaustion gracefully
            process_manager.start_stream_process("https://example.com/stream.m3u8")
            
            # Process should not be started
            assert process_manager.current_process is None
            mock_logger.error.assert_called()

    def test_graceful_degradation(self, mock_config, mock_logger):
        """Test graceful degradation scenarios."""
        with patch('vimeo_monitor.monitor.VimeoClient') as mock_vimeo_client:
            # Mock partial failure
            mock_client_instance = Mock()
            mock_vimeo_client.return_value = mock_client_instance
            mock_client_instance.get.side_effect = Exception("Partial failure")
            
            mock_process_manager = Mock()
            monitor = Monitor(mock_config, mock_logger, mock_process_manager)
            
            # Test that system continues to function despite errors
            stream_url = monitor.get_stream_url()
            assert stream_url is None
            
            # Test that retry count is managed correctly
            assert monitor.retry_count <= monitor.max_retries
            
            # Test that system can recover
            monitor.reset_retry_count()
            assert monitor.retry_count == 0


if __name__ == "__main__":
    pytest.main([__file__])
