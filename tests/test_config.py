#!/usr/bin/env python3
"""
Test suite for configuration module.
"""

import os

# Add src to path for imports
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vimeo_monitor.config import Config


@pytest.mark.unit
class TestConfig:
    """Test cases for Config class."""

    def test_config_initialization(self):
        """Test basic config initialization."""
        config = Config()
        assert config is not None
        assert hasattr(config, "project_root")
        assert hasattr(config, "vimeo_token")
        assert hasattr(config, "vimeo_key")
        assert hasattr(config, "vimeo_secret")

    def test_project_root_detection(self):
        """Test project root detection."""
        config = Config()
        assert config.project_root is not None
        assert isinstance(config.project_root, Path)
        assert config.project_root.exists()

    def test_path_resolution(self):
        """Test path resolution functionality."""
        config = Config()

        # Test absolute path
        abs_path = "/tmp/test"
        resolved = config._resolve_path(abs_path)
        assert resolved == abs_path

        # Test relative path
        rel_path = "logs/test.log"
        resolved = config._resolve_path(rel_path)
        expected = config.project_root / rel_path
        assert resolved == str(expected.absolute())

        # Test None path
        resolved = config._resolve_path(None)
        assert resolved is None

    def test_vimeo_client_config(self):
        """Test Vimeo client configuration."""
        config = Config()
        client_config = config.get_vimeo_client_config()

        assert isinstance(client_config, dict)
        assert "token" in client_config
        assert "key" in client_config
        assert "secret" in client_config

    def test_stream_id_mapping(self):
        """Test stream ID mapping."""
        config = Config()

        # Test valid stream selection
        stream_id = config.get_stream_id()
        assert stream_id is not None
        assert isinstance(stream_id, str)
        assert stream_id.isdigit()

    def test_config_validation_with_missing_vars(self):
        """Test configuration validation with missing environment variables."""
        # Create a new config instance and manually set None values
        config = Config()

        # Temporarily set required values to None
        config.vimeo_token = None
        config.vimeo_key = None
        config.vimeo_secret = None
        config.static_image_path = None
        config.error_image_path = None

        # This should raise ValueError
        with pytest.raises(ValueError):
            config.validate()

    def test_config_validation_with_invalid_paths(self):
        """Test configuration validation with invalid file paths."""
        # Create temporary config with invalid paths
        with tempfile.TemporaryDirectory():
            # Set up environment with invalid paths
            os.environ["VIMEO_TOKEN"] = "test_token"
            os.environ["VIMEO_KEY"] = "test_key"
            os.environ["VIMEO_SECRET"] = "test_secret"
            os.environ["STATIC_IMAGE_PATH"] = "/nonexistent/path.png"
            os.environ["ERROR_IMAGE_PATH"] = "/nonexistent/error.png"

            try:
                config = Config()
                with pytest.raises(FileNotFoundError):
                    config.validate()
            finally:
                # Clean up environment
                for var in [
                    "VIMEO_TOKEN",
                    "VIMEO_KEY",
                    "VIMEO_SECRET",
                    "STATIC_IMAGE_PATH",
                    "ERROR_IMAGE_PATH",
                ]:
                    if var in os.environ:
                        del os.environ[var]


if __name__ == "__main__":
    pytest.main([__file__])
