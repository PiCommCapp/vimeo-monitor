#!/usr/bin/env python3
"""
Configuration management module for Vimeo Monitor.

This module handles loading and validating configuration from environment variables.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


class Config:
    """Configuration class for Vimeo Monitor."""

    def __init__(self) -> None:
        """Initialize configuration by loading environment variables."""
        # Load environment variables from .env file
        load_dotenv()

        # Get project root directory (where .env file is located)
        self.project_root = Path(__file__).parent.parent.parent.absolute()

        # Vimeo API Credentials
        self.vimeo_token: str | None = os.getenv("VIMEO_TOKEN")
        self.vimeo_key: str | None = os.getenv("VIMEO_KEY")
        self.vimeo_secret: str | None = os.getenv("VIMEO_SECRET")

        # Stream Configuration
        self.stream_selection: int = int(os.getenv("STREAM_SELECTION", "1"))
        self.static_image_path: str | None = self._resolve_path(
            os.getenv("STATIC_IMAGE_PATH")
        )
        self.error_image_path: str | None = self._resolve_path(
            os.getenv("ERROR_IMAGE_PATH")
        )

        # Logging Configuration
        self.log_file: str | None = self._resolve_path(
            os.getenv("LOG_FILE", "logs/stream_monitor.log")
        )
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.log_rotation_days: int = int(os.getenv("LOG_ROTATION_DAYS", "7"))

        # Process Configuration
        self.check_interval: int = int(os.getenv("CHECK_INTERVAL", "10"))
        self.max_retries: int = int(os.getenv("MAX_RETRIES", "3"))

        # Stream IDs (hardcoded as they are static)
        self.streams = {
            1: "4797083",
            2: "4797121",
            3: "4898539",
            4: "4797153",
            5: "4797202",
            6: "4797207",
        }

    def _resolve_path(self, path: str | None) -> str | None:
        """Resolve relative paths relative to project root."""
        if not path:
            return None

        # If path is already absolute, return as-is
        if os.path.isabs(path):
            return path

        # Resolve relative to project root
        resolved = self.project_root / path
        return str(resolved.absolute())

    def validate(self) -> None:
        """Validate all required configuration and provide helpful error messages."""
        # Validate required environment variables
        required_vars = [
            ("VIMEO_TOKEN", self.vimeo_token),
            ("VIMEO_KEY", self.vimeo_key),
            ("VIMEO_SECRET", self.vimeo_secret),
            ("STATIC_IMAGE_PATH", self.static_image_path),
            ("ERROR_IMAGE_PATH", self.error_image_path),
        ]

        for var_name, var_value in required_vars:
            if not var_value:
                raise ValueError(f"Required environment variable {var_name} not set")

        # Validate file paths
        if self.static_image_path and not os.path.exists(self.static_image_path):
            raise FileNotFoundError(f"Static image not found: {self.static_image_path}")

        if self.error_image_path and not os.path.exists(self.error_image_path):
            raise FileNotFoundError(f"Error image not found: {self.error_image_path}")

        # Validate numeric values
        if self.check_interval < 1:
            raise ValueError("Check interval must be at least 1 second")

        if self.stream_selection not in self.streams:
            raise ValueError(
                f"Stream selection must be between 1 and {len(self.streams)}"
            )

        if self.log_rotation_days < 1:
            raise ValueError("Log rotation days must be at least 1")

        if self.max_retries < 1:
            raise ValueError("Max retries must be at least 1")

    def get_stream_id(self) -> str:
        """Get the stream ID for the selected stream."""
        return self.streams[self.stream_selection]

    def get_vimeo_client_config(self) -> dict:
        """Get Vimeo client configuration."""
        return {
            "token": self.vimeo_token,
            "key": self.vimeo_key,
            "secret": self.vimeo_secret,
        }


# Global configuration instance
config = Config()
