#!/usr/bin/env python3

"""Enhanced configuration management for Vimeo Monitor application."""

import logging
import os
from pathlib import Path
from typing import Any, TypeVar

import toml
import yaml
from dotenv import load_dotenv
from pydantic import ValidationError

from vimeo_monitor.config_watcher import ConfigBackupManager, ConfigWatcher
from vimeo_monitor.validation import VimeoMonitorConfig

T = TypeVar("T")


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""


class EnhancedConfigManager:
    """Enhanced configuration management with YAML/TOML support, validation, and live reload."""

    def __init__(
        self,
        env_file: str = ".env",
        config_file: str | None = None,
        enable_live_reload: bool = False,
        enable_backup: bool = True,
    ) -> None:
        """Initialize enhanced configuration manager.

        Args:
            env_file: Path to environment file to load
            config_file: Optional path to YAML/TOML configuration file
            enable_live_reload: Enable live reload of configuration changes
            enable_backup: Enable automatic configuration backups
        """
        self._env_file = env_file
        self._config_file = config_file
        self._enable_live_reload = enable_live_reload
        self._enable_backup = enable_backup

        # Configuration data
        self._config: VimeoMonitorConfig | None = None
        self._raw_data: dict[str, Any] = {}

        # Live reload and backup components
        self._watcher: ConfigWatcher | None = None
        self._backup_manager: ConfigBackupManager | None = None

        if self._enable_backup:
            self._backup_manager = ConfigBackupManager()

        # Load initial configuration
        self._load_configuration()

        # Setup live reload if enabled
        if self._enable_live_reload:
            self._setup_live_reload()

    def _load_configuration(self) -> None:
        """Load configuration from all sources with priority order."""
        # Start with empty data
        config_data: dict[str, Any] = {}

        # 1. Load from configuration file (lowest priority)
        if self._config_file:
            config_data.update(self._load_config_file())

        # 2. Load from environment variables (higher priority)
        env_data = self._load_environment_variables()
        config_data.update(env_data)

        # 3. Environment variables override config file values
        self._raw_data = config_data

        # Validate and create configuration object
        self._validate_and_create_config(config_data)

    def _load_config_file(self) -> dict[str, Any]:
        """Load configuration from YAML or TOML file."""
        if not self._config_file:
            return {}

        config_path = Path(self._config_file)
        if not config_path.exists():
            logging.warning("Configuration file not found: %s", self._config_file)
            return {}

        try:
            # Create backup before loading if backup is enabled
            if self._enable_backup and self._backup_manager:
                self._backup_manager.create_backup(str(config_path), "auto")

            with config_path.open("r", encoding="utf-8") as f:
                if config_path.suffix.lower() in [".yaml", ".yml"]:
                    data = yaml.safe_load(f) or {}
                elif config_path.suffix.lower() == ".toml":
                    data = toml.load(f) or {}
                else:
                    raise ConfigurationError(f"Unsupported configuration file format: {config_path.suffix}")

            logging.info("Loaded configuration from: %s", self._config_file)
            return self._flatten_config_data(data)

        except (yaml.YAMLError, toml.TomlDecodeError) as e:
            raise ConfigurationError(f"Error parsing configuration file {self._config_file}: {e}") from e
        except Exception as e:
            raise ConfigurationError(f"Error loading configuration file {self._config_file}: {e}") from e

    def _load_environment_variables(self) -> dict[str, Any]:
        """Load configuration from environment variables."""
        # Load .env file first
        if Path(self._env_file).exists():
            load_dotenv(self._env_file)
            logging.debug("Loaded environment from %s", self._env_file)

        # Convert environment variables to structured data
        env_data = {}
        env_mapping = {
            # Vimeo API (keep as strings)
            "VIMEO_TOKEN": ("vimeo", "token"),
            "VIMEO_KEY": ("vimeo", "key"),
            "VIMEO_SECRET": ("vimeo", "secret"),
            "VIMEO_STREAM_ID": ("vimeo", "stream_id"),
            # Timing (convert to numbers)
            "CHECK_INTERVAL": ("timing", "check_interval"),
            # API Failure (convert to numbers)
            "API_FAILURE_THRESHOLD": ("api_failure", "failure_threshold"),
            "API_STABILITY_THRESHOLD": ("api_failure", "stability_threshold"),
            "API_MIN_RETRY_INTERVAL": ("api_failure", "min_retry_interval"),
            "API_MAX_RETRY_INTERVAL": ("api_failure", "max_retry_interval"),
            "API_ENABLE_BACKOFF": ("api_failure", "enable_backoff"),
            # File Paths (keep as strings)
            "HOLDING_IMAGE_PATH": ("file_paths", "holding_image_path"),
            "API_FAIL_IMAGE_PATH": ("file_paths", "api_fail_image_path"),
            # Logging (mixed)
            "LOG_FILE": ("logging", "log_file"),
            "LOG_LEVEL": ("logging", "log_level"),
            "LOG_ROTATE_MAX_SIZE": ("logging", "rotate_max_size"),
            "LOG_ROTATE_BACKUP_COUNT": ("logging", "rotate_backup_count"),
            # Overlay (mixed)
            "DISPLAY_NETWORK_STATUS": ("overlay", "display_network_status"),
            "OVERLAY_POSITION": ("overlay", "position"),
            "OVERLAY_OPACITY": ("overlay", "opacity"),
            "OVERLAY_UPDATE_INTERVAL": ("overlay", "update_interval"),
            "OVERLAY_AUTO_HIDE": ("overlay", "auto_hide"),
            "OVERLAY_USE_TERMINAL": ("overlay", "use_terminal"),
        }

        # Fields that should be converted to numbers
        numeric_fields = {
            "CHECK_INTERVAL",
            "API_FAILURE_THRESHOLD",
            "API_STABILITY_THRESHOLD",
            "API_MIN_RETRY_INTERVAL",
            "API_MAX_RETRY_INTERVAL",
            "LOG_ROTATE_MAX_SIZE",
            "LOG_ROTATE_BACKUP_COUNT",
            "OVERLAY_OPACITY",
            "OVERLAY_UPDATE_INTERVAL",
        }

        # Fields that should be converted to booleans
        boolean_fields = {"API_ENABLE_BACKOFF", "DISPLAY_NETWORK_STATUS", "OVERLAY_AUTO_HIDE", "OVERLAY_USE_TERMINAL"}

        for env_var, (section, key) in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                if section not in env_data:
                    env_data[section] = {}

                # Convert based on field type
                if env_var in boolean_fields:
                    converted_value = value.lower() in ("true", "1", "yes", "on")
                elif env_var in numeric_fields:
                    converted_value = self._convert_to_number(value)
                else:
                    # Keep as string, but handle empty values
                    converted_value = value if value else None

                env_data[section][key] = converted_value

        return env_data

    def _convert_to_number(self, value: str) -> int | float:
        """Convert string value to number (int or float)."""
        try:
            # Try integer first
            if "." not in value:
                return int(value)
            else:
                return float(value)
        except ValueError:
            # If conversion fails, return as string
            return value

    def _flatten_config_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Flatten nested configuration data for compatibility."""
        # This method is for when config files have nested structure
        # but we need flat structure for legacy compatibility
        return data

    def _validate_and_create_config(self, config_data: dict[str, Any]) -> None:
        """Validate configuration data and create config object."""
        try:
            self._config = VimeoMonitorConfig(**config_data)
            logging.info("Configuration validation successful")
        except ValidationError as e:
            error_msg = f"Configuration validation failed: {e}"
            logging.exception(error_msg)
            raise ConfigurationError(error_msg) from e

    def _setup_live_reload(self) -> None:
        """Setup live reload functionality."""
        self._watcher = ConfigWatcher(self._handle_config_change)

        # Watch environment file
        if Path(self._env_file).exists():
            self._watcher.add_file(self._env_file)

        # Watch configuration file
        if self._config_file and Path(self._config_file).exists():
            self._watcher.add_file(self._config_file)

        self._watcher.start()

    def _handle_config_change(self, config_path: str) -> bool:
        """Handle configuration file changes for live reload."""
        try:
            logging.info("Reloading configuration due to file change: %s", config_path)

            # Create backup before reloading
            if self._enable_backup and self._backup_manager:
                self._backup_manager.create_backup(config_path, "pre_reload")

            # Reload configuration
            old_config = self._config
            self._load_configuration()

            # Log what changed
            if old_config and self._config:
                self._log_config_changes(old_config, self._config)

            return True

        except Exception as e:
            logging.exception("Failed to reload configuration: %s", e)
            return False

    def _log_config_changes(self, old_config: VimeoMonitorConfig, new_config: VimeoMonitorConfig) -> None:
        """Log what configuration values changed."""
        old_summary = old_config.get_summary()
        new_summary = new_config.get_summary()

        changes = []
        for key, new_value in new_summary.items():
            old_value = old_summary.get(key)
            if old_value != new_value:
                changes.append(f"{key}: {old_value} -> {new_value}")

        if changes:
            logging.info("Configuration changes: %s", ", ".join(changes))
        else:
            logging.info("Configuration reloaded with no changes")

    # Property accessors for backward compatibility
    @property
    def vimeo_token(self) -> str | None:
        """Vimeo API token."""
        return self._config.vimeo.token if self._config else None

    @property
    def vimeo_key(self) -> str | None:
        """Vimeo API key."""
        return self._config.vimeo.key if self._config else None

    @property
    def vimeo_secret(self) -> str | None:
        """Vimeo API secret."""
        return self._config.vimeo.secret if self._config else None

    @property
    def vimeo_stream_id(self) -> str | None:
        """Vimeo stream ID."""
        return self._config.vimeo.stream_id if self._config else None

    @property
    def check_interval(self) -> int:
        """Interval between stream checks in seconds."""
        return self._config.timing.check_interval if self._config else 30

    @property
    def api_failure_threshold(self) -> int:
        """Number of consecutive failures before entering failure mode."""
        return self._config.api_failure.failure_threshold if self._config else 3

    @property
    def api_stability_threshold(self) -> int:
        """Number of consecutive successes needed to exit failure mode."""
        return self._config.api_failure.stability_threshold if self._config else 5

    @property
    def api_min_retry_interval(self) -> int:
        """Minimum retry interval in seconds."""
        return self._config.api_failure.min_retry_interval if self._config else 10

    @property
    def api_max_retry_interval(self) -> int:
        """Maximum retry interval in seconds."""
        return self._config.api_failure.max_retry_interval if self._config else 300

    @property
    def api_enable_backoff(self) -> bool:
        """Enable exponential backoff for API retries."""
        return self._config.api_failure.enable_backoff if self._config else True

    @property
    def holding_image_path(self) -> str | None:
        """Path to holding image."""
        return self._config.file_paths.holding_image_path if self._config else None

    @property
    def api_fail_image_path(self) -> str | None:
        """Path to API failure image."""
        return self._config.file_paths.api_fail_image_path if self._config else None

    @property
    def log_file(self) -> str:
        """Log file path."""
        return self._config.logging.log_file if self._config else "./logs/vimeo_monitor.logs"

    @property
    def log_level(self) -> str:
        """Log level."""
        return self._config.logging.log_level if self._config else "INFO"

    @property
    def log_rotate_max_size(self) -> int:
        """Maximum log file size before rotation."""
        return self._config.logging.rotate_max_size if self._config else 10485760

    @property
    def log_rotate_backup_count(self) -> int:
        """Number of backup log files to keep."""
        return self._config.logging.rotate_backup_count if self._config else 5

    @property
    def display_network_status(self) -> bool:
        """Enable network status overlay display."""
        return self._config.overlay.display_network_status if self._config else True

    @property
    def overlay_position(self) -> str:
        """Position of network status overlay."""
        return self._config.overlay.position if self._config else "top-right"

    @property
    def overlay_opacity(self) -> float:
        """Opacity of network status overlay."""
        return self._config.overlay.opacity if self._config else 0.8

    @property
    def overlay_update_interval(self) -> int:
        """Update interval for overlay in seconds."""
        return self._config.overlay.update_interval if self._config else 2

    @property
    def overlay_auto_hide(self) -> bool:
        """Auto-hide overlay when stream is healthy."""
        return self._config.overlay.auto_hide if self._config else False

    @property
    def overlay_use_terminal(self) -> bool:
        """Force terminal mode for overlay (disable GUI)."""
        return self._config.overlay.use_terminal if self._config else False

    def get_summary(self) -> dict[str, Any]:
        """Get configuration summary for logging."""
        return self._config.get_summary() if self._config else {}

    def get_config_object(self) -> VimeoMonitorConfig | None:
        """Get the validated configuration object."""
        return self._config

    def reload_configuration(self) -> None:
        """Manually reload configuration from all sources."""
        self._load_configuration()

    def export_to_yaml(self, output_path: str) -> None:
        """Export current configuration to YAML file."""
        if not self._config:
            raise ConfigurationError("No valid configuration to export")

        config_dict = self._config.model_dump()
        output_file = Path(output_path)

        with output_file.open("w", encoding="utf-8") as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)

        logging.info("Configuration exported to YAML: %s", output_path)

    def export_to_toml(self, output_path: str) -> None:
        """Export current configuration to TOML file."""
        if not self._config:
            raise ConfigurationError("No valid configuration to export")

        config_dict = self._config.model_dump()
        output_file = Path(output_path)

        with output_file.open("w", encoding="utf-8") as f:
            toml.dump(config_dict, f)

        logging.info("Configuration exported to TOML: %s", output_path)

    def export_to_env(self, output_path: str) -> None:
        """Export current configuration to .env file."""
        if not self._config:
            raise ConfigurationError("No valid configuration to export")

        env_dict = self._config.to_env_dict()
        output_file = Path(output_path)

        with output_file.open("w", encoding="utf-8") as f:
            for key, value in sorted(env_dict.items()):
                f.write(f"{key}={value}\n")

        logging.info("Configuration exported to ENV: %s", output_path)

    def cleanup(self) -> None:
        """Cleanup resources (stop watchers, etc.)."""
        if self._watcher:
            self._watcher.stop()

        if self._backup_manager:
            self._backup_manager.cleanup_old_backups()


# Backward compatibility alias
ConfigManager = EnhancedConfigManager
