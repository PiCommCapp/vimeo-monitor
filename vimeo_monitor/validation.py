#!/usr/bin/env python3

"""Configuration validation schemas for Vimeo Monitor application."""

import logging
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class VimeoAPIConfig(BaseModel):
    """Vimeo API configuration schema."""

    token: str = Field(..., description="Vimeo API token")
    key: str = Field(..., description="Vimeo API key")
    secret: str = Field(..., description="Vimeo API secret")
    stream_id: str = Field(..., description="Vimeo stream ID")

    @field_validator("token", "key", "secret", "stream_id")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        """Validate that API credentials are not empty."""
        if not v or not v.strip():
            raise ValueError("API credentials cannot be empty")
        return v.strip()


class TimingConfig(BaseModel):
    """Timing configuration schema."""

    check_interval: int = Field(
        default=30, ge=1, le=3600, description="Interval between stream checks in seconds (1-3600)"
    )


class APIFailureConfig(BaseModel):
    """API failure handling configuration schema."""

    failure_threshold: int = Field(
        default=3, ge=1, le=100, description="Number of consecutive failures before entering failure mode (1-100)"
    )
    stability_threshold: int = Field(
        default=5, ge=1, le=100, description="Number of consecutive successes needed to exit failure mode (1-100)"
    )
    min_retry_interval: int = Field(default=10, ge=1, le=3600, description="Minimum retry interval in seconds (1-3600)")
    max_retry_interval: int = Field(
        default=300, ge=10, le=86400, description="Maximum retry interval in seconds (10-86400)"
    )
    enable_backoff: bool = Field(default=True, description="Enable exponential backoff for API retries")

    @model_validator(mode="after")
    def validate_intervals(self) -> "APIFailureConfig":
        """Validate that min_retry_interval < max_retry_interval."""
        if self.min_retry_interval >= self.max_retry_interval:
            raise ValueError("min_retry_interval must be less than max_retry_interval")
        return self


class FilePathConfig(BaseModel):
    """File path configuration schema."""

    holding_image_path: str | None = Field(default=None, description="Path to holding image")
    api_fail_image_path: str | None = Field(default=None, description="Path to API failure image")

    @field_validator("holding_image_path", "api_fail_image_path")
    @classmethod
    def validate_file_path(cls, v: str | None) -> str | None:
        """Validate that file paths exist if specified."""
        if v is None:
            return v

        path = Path(v)
        if not path.exists():
            logging.warning("File path does not exist: %s", v)
        elif not path.is_file():
            raise ValueError(f"Path is not a file: {v}")

        return str(path.resolve())


class LoggingConfig(BaseModel):
    """Logging configuration schema."""

    log_file: str = Field(default="./logs/vimeo_monitor.logs", description="Log file path")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO", description="Log level")
    rotate_max_size: int = Field(
        default=10485760,  # 10MB
        ge=1024,  # 1KB minimum
        le=1073741824,  # 1GB maximum
        description="Maximum log file size before rotation (1KB-1GB)",
    )
    rotate_backup_count: int = Field(default=5, ge=0, le=100, description="Number of backup log files to keep (0-100)")

    @field_validator("log_file")
    @classmethod
    def validate_log_file_path(cls, v: str) -> str:
        """Validate log file path and create directory if needed."""
        log_path = Path(v)

        # Create parent directory if it doesn't exist
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Check if path is writable
        try:
            # Test write by creating/touching the file
            log_path.touch(exist_ok=True)
        except (PermissionError, OSError) as e:
            raise ValueError(f"Cannot write to log file path: {v} - {e}") from e

        return str(log_path.resolve())


class OverlayConfig(BaseModel):
    """Network status overlay configuration schema."""

    display_network_status: bool = Field(default=True, description="Enable network status overlay display")
    position: Literal["top-left", "top-right", "bottom-left", "bottom-right"] = Field(
        default="top-right", description="Position of network status overlay"
    )
    opacity: float = Field(default=0.8, ge=0.0, le=1.0, description="Opacity of network status overlay (0.0-1.0)")
    update_interval: int = Field(default=2, ge=1, le=60, description="Update interval for overlay in seconds (1-60)")
    auto_hide: bool = Field(default=False, description="Auto-hide overlay when stream is healthy")
    use_terminal: bool = Field(default=False, description="Force terminal mode for overlay (disable GUI)")


class VimeoMonitorConfig(BaseModel):
    """Complete Vimeo Monitor configuration schema."""

    vimeo: VimeoAPIConfig
    timing: TimingConfig = Field(default_factory=TimingConfig)
    api_failure: APIFailureConfig = Field(default_factory=APIFailureConfig)
    file_paths: FilePathConfig = Field(default_factory=FilePathConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    overlay: OverlayConfig = Field(default_factory=OverlayConfig)

    class Config:
        """Pydantic configuration."""

        extra = "forbid"  # Forbid extra fields
        validate_assignment = True  # Validate on assignment
        str_strip_whitespace = True  # Strip whitespace from strings

    def to_env_dict(self) -> dict[str, str]:
        """Convert configuration to environment variable format."""
        env_dict = {
            # Vimeo API
            "VIMEO_TOKEN": self.vimeo.token,
            "VIMEO_KEY": self.vimeo.key,
            "VIMEO_SECRET": self.vimeo.secret,
            "VIMEO_STREAM_ID": self.vimeo.stream_id,
            # Timing
            "CHECK_INTERVAL": str(self.timing.check_interval),
            # API Failure
            "API_FAILURE_THRESHOLD": str(self.api_failure.failure_threshold),
            "API_STABILITY_THRESHOLD": str(self.api_failure.stability_threshold),
            "API_MIN_RETRY_INTERVAL": str(self.api_failure.min_retry_interval),
            "API_MAX_RETRY_INTERVAL": str(self.api_failure.max_retry_interval),
            "API_ENABLE_BACKOFF": str(self.api_failure.enable_backoff).lower(),
            # File Paths
            "HOLDING_IMAGE_PATH": self.file_paths.holding_image_path or "",
            "API_FAIL_IMAGE_PATH": self.file_paths.api_fail_image_path or "",
            # Logging
            "LOG_FILE": self.logging.log_file,
            "LOG_LEVEL": self.logging.log_level,
            "LOG_ROTATE_MAX_SIZE": str(self.logging.rotate_max_size),
            "LOG_ROTATE_BACKUP_COUNT": str(self.logging.rotate_backup_count),
            # Overlay
            "DISPLAY_NETWORK_STATUS": str(self.overlay.display_network_status).lower(),
            "OVERLAY_POSITION": self.overlay.position,
            "OVERLAY_OPACITY": str(self.overlay.opacity),
            "OVERLAY_UPDATE_INTERVAL": str(self.overlay.update_interval),
            "OVERLAY_AUTO_HIDE": str(self.overlay.auto_hide).lower(),
            "OVERLAY_USE_TERMINAL": str(self.overlay.use_terminal).lower(),
        }

        # Remove empty values
        return {k: v for k, v in env_dict.items() if v}

    def get_summary(self) -> dict[str, Any]:
        """Get configuration summary for logging."""
        return {
            "stream_id": self.vimeo.stream_id,
            "check_interval": self.timing.check_interval,
            "api_failure_threshold": self.api_failure.failure_threshold,
            "api_stability_threshold": self.api_failure.stability_threshold,
            "api_enable_backoff": self.api_failure.enable_backoff,
            "log_level": self.logging.log_level,
            "display_network_status": self.overlay.display_network_status,
            "overlay_position": self.overlay.position,
            "overlay_opacity": self.overlay.opacity,
        }
