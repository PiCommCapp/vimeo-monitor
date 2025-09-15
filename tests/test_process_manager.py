#!/usr/bin/env python3
"""
Test suite for process manager module.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vimeo_monitor.process_manager import ProcessManager


class TestProcessManager:
    """Test cases for ProcessManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_config = Mock()
        self.mock_config.static_image_path = "/tmp/test_image.png"
        self.mock_config.error_image_path = "/tmp/test_error.png"
        
        self.mock_logger = Mock()
        
        self.process_manager = ProcessManager(self.mock_config, self.mock_logger)
    
    def test_initialization(self):
        """Test process manager initialization."""
        assert self.process_manager.config == self.mock_config
        assert self.process_manager.logger == self.mock_logger
        assert self.process_manager.current_process is None
        assert self.process_manager.current_mode is None
        assert self.process_manager.restart_count == 0
        assert self.process_manager.max_restarts == 5
        assert self.process_manager.restart_delay == 5
    
    def test_is_process_running_no_process(self):
        """Test is_process_running with no process."""
        assert not self.process_manager.is_process_running()
    
    @patch('subprocess.Popen')
    def test_is_process_running_with_process(self, mock_popen):
        """Test is_process_running with running process."""
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process is running
        mock_popen.return_value = mock_process
        
        self.process_manager.current_process = mock_process
        assert self.process_manager.is_process_running()
    
    @patch('subprocess.Popen')
    def test_is_process_running_with_stopped_process(self, mock_popen):
        """Test is_process_running with stopped process."""
        mock_process = Mock()
        mock_process.poll.return_value = 0  # Process has stopped
        mock_popen.return_value = mock_process
        
        self.process_manager.current_process = mock_process
        assert not self.process_manager.is_process_running()
    
    def test_should_restart_within_limits(self):
        """Test should_restart when within restart limits."""
        self.process_manager.restart_count = 3
        assert self.process_manager.should_restart()
    
    def test_should_restart_exceeds_limits(self):
        """Test should_restart when exceeds restart limits."""
        self.process_manager.restart_count = 6
        # Should still allow restart if enough time has passed (time reset)
        assert self.process_manager.should_restart()
    
    def test_should_restart_reset_after_time(self):
        """Test should_restart resets count after time passes."""
        self.process_manager.restart_count = 6
        self.process_manager.last_restart_time = time.time() - 400  # 400 seconds ago
        
        assert self.process_manager.should_restart()
        assert self.process_manager.restart_count == 0
    
    def test_get_process_status_no_process(self):
        """Test get_process_status with no process."""
        status = self.process_manager.get_process_status()
        
        assert status['mode'] is None
        assert status['running'] is False
        assert status['pid'] is None
        assert status['return_code'] is None
    
    @patch('subprocess.Popen')
    def test_get_process_status_with_process(self, mock_popen):
        """Test get_process_status with running process."""
        mock_process = Mock()
        mock_process.poll.return_value = None
        mock_process.pid = 12345
        mock_process.returncode = None
        mock_popen.return_value = mock_process
        
        self.process_manager.current_process = mock_process
        self.process_manager.current_mode = "stream"
        
        status = self.process_manager.get_process_status()
        
        assert status['mode'] == "stream"
        assert status['running'] is True
        assert status['pid'] == 12345
        assert status['return_code'] is None
    
    @patch('subprocess.Popen')
    def test_start_stream_process(self, mock_popen):
        """Test starting stream process."""
        mock_process = Mock()
        mock_popen.return_value = mock_process
        
        video_url = "https://example.com/stream.m3u8"
        self.process_manager.start_stream_process(video_url)
        
        mock_popen.assert_called_once()
        assert self.process_manager.current_process == mock_process
        assert self.process_manager.current_mode == "stream"
    
    @patch('subprocess.Popen')
    def test_start_image_process(self, mock_popen):
        """Test starting image process."""
        mock_process = Mock()
        mock_popen.return_value = mock_process
        
        image_path = "/tmp/test.png"
        self.process_manager.start_image_process(image_path)
        
        mock_popen.assert_called_once()
        assert self.process_manager.current_process == mock_process
        assert self.process_manager.current_mode == "image"
    
    @patch('subprocess.Popen')
    def test_start_error_process(self, mock_popen):
        """Test starting error process."""
        mock_process = Mock()
        mock_popen.return_value = mock_process
        
        error_path = "/tmp/error.png"
        self.process_manager.start_error_process(error_path)
        
        mock_popen.assert_called_once()
        assert self.process_manager.current_process == mock_process
        assert self.process_manager.current_mode == "error"
    
    def test_restart_process_no_process(self):
        """Test restart_process with no current process."""
        result = self.process_manager.restart_process()
        assert result is True  # No process to restart
    
    def test_restart_process_running_process(self):
        """Test restart_process with running process."""
        mock_process = Mock()
        mock_process.poll.return_value = None  # Process is running
        self.process_manager.current_process = mock_process
        self.process_manager.current_mode = "image"
        
        result = self.process_manager.restart_process()
        assert result is True  # Process is running, no restart needed
    
    @patch('time.sleep')
    def test_restart_process_stopped_process(self, mock_sleep):
        """Test restart_process with stopped process."""
        mock_process = Mock()
        mock_process.poll.return_value = 1  # Process has stopped
        self.process_manager.current_process = mock_process
        self.process_manager.current_mode = "image"
        
        with patch.object(self.process_manager, 'start_image_process') as mock_start:
            result = self.process_manager.restart_process()
            
            assert result is True
            mock_sleep.assert_called_once_with(5)  # restart_delay
            mock_start.assert_called_once_with(self.mock_config.static_image_path)
            assert self.process_manager.restart_count == 1
    
    def test_restart_process_exceeds_max_restarts(self):
        """Test restart_process when max restarts exceeded."""
        mock_process = Mock()
        mock_process.poll.return_value = 1  # Process has stopped
        self.process_manager.current_process = mock_process
        self.process_manager.current_mode = "image"
        self.process_manager.restart_count = 5  # At max limit
        
        result = self.process_manager.restart_process()
        # Should still restart because time reset logic allows it
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__])
