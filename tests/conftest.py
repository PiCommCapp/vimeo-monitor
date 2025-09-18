#!/usr/bin/env python3
"""
Shared test fixtures and configuration for the test suite.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup is handled by the test


@pytest.fixture
def mock_config():
    """Create a mock configuration object."""
    config = Mock()
    config.vimeo_token = "test_token"
    config.vimeo_key = "test_key"
    config.vimeo_secret = "test_secret"
    config.stream_selection = 1
    config.static_image_path = "/tmp/test_image.png"
    config.error_image_path = "/tmp/test_error.png"
    config.log_file = "/tmp/test.log"
    config.log_level = "INFO"
    config.log_rotation_days = 7
    config.check_interval = 10
    config.max_retries = 3
    config.project_root = Path("/tmp")
    
    # Health monitoring configuration
    config.health_monitoring_enabled = False
    config.health_metrics_port = 8080
    config.health_metrics_host = "0.0.0.0"
    config.health_hardware_interval = 10
    config.health_network_interval = 30
    config.health_stream_interval = 60
    config.health_hardware_enabled = True
    config.health_network_enabled = True
    config.health_stream_enabled = True
    config.health_network_ping_hosts = ["8.8.8.8", "1.1.1.1"]
    config.health_network_speedtest_enabled = False
    config.health_stream_ffprobe_timeout = 15
    config.get_vimeo_client_config.return_value = {
        "token": "test_token",
        "key": "test_key",
        "secret": "test_secret"
    }
    
    return config


@pytest.fixture
def mock_logger():
    """Create a mock logger object."""
    logger = Mock()
    logger.info = Mock()
    logger.debug = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.critical = Mock()
    logger.exception = Mock()
    return logger


@pytest.fixture
def mock_vimeo_client():
    """Create a mock Vimeo client."""
    client = Mock()
    client.get = Mock()
    return client


@pytest.fixture
def mock_process():
    """Create a mock process object."""
    process = Mock()
    process.poll = Mock(return_value=None)  # Process is running
    process.pid = 12345
    process.returncode = None
    return process


@pytest.fixture
def sample_vimeo_response():
    """Sample Vimeo API response."""
    return {
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


@pytest.fixture
def empty_vimeo_response():
    """Empty Vimeo API response."""
    return {'data': []}


@pytest.fixture
def test_environment():
    """Set up test environment variables."""
    original_env = os.environ.copy()
    
    # Set test environment variables
    test_env = {
        'VIMEO_TOKEN': 'test_token',
        'VIMEO_KEY': 'test_key',
        'VIMEO_SECRET': 'test_secret',
        'STREAM_SELECTION': '1',
        'LOG_LEVEL': 'INFO',
        'CHECK_INTERVAL': '10',
        'MAX_RETRIES': '3',
        'HEALTH_MONITORING_ENABLED': 'false'
    }
    
    os.environ.update(test_env)
    
    yield test_env
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def integration_test_config():
    """Configuration for integration tests."""
    config = Mock()
    config.vimeo_token = "integration_test_token"
    config.vimeo_key = "integration_test_key"
    config.vimeo_secret = "integration_test_secret"
    config.stream_selection = 1
    config.static_image_path = "/tmp/integration_test_image.png"
    config.error_image_path = "/tmp/integration_test_error.png"
    config.log_file = "/tmp/integration_test.log"
    config.log_level = "DEBUG"
    config.log_rotation_days = 1
    config.check_interval = 5
    config.max_retries = 2
    config.project_root = Path("/tmp")
    
    # Health monitoring configuration for integration tests
    config.health_monitoring_enabled = True
    config.health_metrics_port = 8081  # Use different port for testing
    config.health_metrics_host = "127.0.0.1"
    config.health_hardware_interval = 5
    config.health_network_interval = 10
    config.health_stream_interval = 15
    config.health_hardware_enabled = False  # Disable for testing
    config.health_network_enabled = False  # Disable for testing
    config.health_stream_enabled = False  # Disable for testing
    config.health_network_ping_hosts = ["8.8.8.8"]
    config.health_network_speedtest_enabled = False
    config.health_stream_ffprobe_timeout = 5
    config.get_vimeo_client_config.return_value = {
        "token": "integration_test_token",
        "key": "integration_test_key",
        "secret": "integration_test_secret"
    }
    
    return config


# Pytest markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
