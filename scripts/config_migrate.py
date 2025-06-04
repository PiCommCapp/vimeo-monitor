#!/usr/bin/env python3

"""Configuration migration utility for Vimeo Monitor."""

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

import toml
import yaml
from dotenv import dotenv_values

# Add parent directory to path to import vimeo_monitor modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from vimeo_monitor.config import EnhancedConfigManager
from vimeo_monitor.validation import VimeoMonitorConfig


def setup_logging(level: str = "INFO") -> None:
    """Setup logging for the migration utility."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def load_env_file(env_path: str) -> dict[str, Any]:
    """Load configuration from .env file."""
    env_values = dotenv_values(env_path)

    # Convert environment variables to structured format
    config_data: dict[str, Any] = {
        "vimeo": {},
        "timing": {},
        "api_failure": {},
        "file_paths": {},
        "logging": {},
        "overlay": {},
    }

    # Define which fields should remain as strings (API credentials, IDs, etc.)
    string_fields = {
        "VIMEO_TOKEN",
        "VIMEO_KEY",
        "VIMEO_SECRET",
        "VIMEO_STREAM_ID",
        "HOLDING_IMAGE_PATH",
        "API_FAIL_IMAGE_PATH",
        "LOG_FILE",
        "LOG_LEVEL",
        "OVERLAY_POSITION",
    }

    # Define numeric fields
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

    # Define boolean fields
    boolean_fields = {"API_ENABLE_BACKOFF", "DISPLAY_NETWORK_STATUS", "OVERLAY_AUTO_HIDE", "OVERLAY_USE_TERMINAL"}

    # Map environment variables to config structure
    env_mapping = {
        # Vimeo API
        "VIMEO_TOKEN": ("vimeo", "token"),
        "VIMEO_KEY": ("vimeo", "key"),
        "VIMEO_SECRET": ("vimeo", "secret"),
        "VIMEO_STREAM_ID": ("vimeo", "stream_id"),
        # Timing
        "CHECK_INTERVAL": ("timing", "check_interval"),
        # API Failure
        "API_FAILURE_THRESHOLD": ("api_failure", "failure_threshold"),
        "API_STABILITY_THRESHOLD": ("api_failure", "stability_threshold"),
        "API_MIN_RETRY_INTERVAL": ("api_failure", "min_retry_interval"),
        "API_MAX_RETRY_INTERVAL": ("api_failure", "max_retry_interval"),
        "API_ENABLE_BACKOFF": ("api_failure", "enable_backoff"),
        # File Paths
        "HOLDING_IMAGE_PATH": ("file_paths", "holding_image_path"),
        "API_FAIL_IMAGE_PATH": ("file_paths", "api_fail_image_path"),
        # Logging
        "LOG_FILE": ("logging", "log_file"),
        "LOG_LEVEL": ("logging", "log_level"),
        "LOG_ROTATE_MAX_SIZE": ("logging", "rotate_max_size"),
        "LOG_ROTATE_BACKUP_COUNT": ("logging", "rotate_backup_count"),
        # Overlay
        "DISPLAY_NETWORK_STATUS": ("overlay", "display_network_status"),
        "OVERLAY_POSITION": ("overlay", "position"),
        "OVERLAY_OPACITY": ("overlay", "opacity"),
        "OVERLAY_UPDATE_INTERVAL": ("overlay", "update_interval"),
        "OVERLAY_AUTO_HIDE": ("overlay", "auto_hide"),
        "OVERLAY_USE_TERMINAL": ("overlay", "use_terminal"),
    }

    for env_var, value in env_values.items():
        if env_var in env_mapping and value is not None:
            section, key = env_mapping[env_var]

            # Convert value based on type
            if env_var in string_fields:
                converted_value = str(value)
            elif env_var in boolean_fields:
                converted_value = value.lower() in ("true", "1", "yes", "on")
            elif env_var in numeric_fields:
                try:
                    converted_value = int(value) if "." not in value else float(value)
                except ValueError:
                    converted_value = value
            else:
                converted_value = value

            config_data[section][key] = converted_value

    # Remove empty sections
    return {k: v for k, v in config_data.items() if v}


def convert_env_value(value: str) -> Any:
    """Convert environment variable string to appropriate type."""
    # Boolean conversion
    if value.lower() in ("true", "1", "yes", "on"):
        return True
    elif value.lower() in ("false", "0", "no", "off"):
        return False

    # Number conversion (but be careful about IDs)
    try:
        # Only convert if it looks like a number and doesn't start with 0
        if value.replace(".", "").isdigit() and not value.startswith("0"):
            if "." in value:
                return float(value)
            else:
                return int(value)
    except ValueError:
        pass

    # Return as string
    return value


def structured_to_env_format(config_data: dict[str, Any]) -> dict[str, str]:
    """Convert structured configuration to environment variable format."""
    env_vars = {}

    # Reverse mapping from structured config to environment variables
    reverse_mapping = {
        ("vimeo", "token"): "VIMEO_TOKEN",
        ("vimeo", "key"): "VIMEO_KEY",
        ("vimeo", "secret"): "VIMEO_SECRET",
        ("vimeo", "stream_id"): "VIMEO_STREAM_ID",
        ("timing", "check_interval"): "CHECK_INTERVAL",
        ("api_failure", "failure_threshold"): "API_FAILURE_THRESHOLD",
        ("api_failure", "stability_threshold"): "API_STABILITY_THRESHOLD",
        ("api_failure", "min_retry_interval"): "API_MIN_RETRY_INTERVAL",
        ("api_failure", "max_retry_interval"): "API_MAX_RETRY_INTERVAL",
        ("api_failure", "enable_backoff"): "API_ENABLE_BACKOFF",
        ("file_paths", "holding_image_path"): "HOLDING_IMAGE_PATH",
        ("file_paths", "api_fail_image_path"): "API_FAIL_IMAGE_PATH",
        ("logging", "log_file"): "LOG_FILE",
        ("logging", "log_level"): "LOG_LEVEL",
        ("logging", "rotate_max_size"): "LOG_ROTATE_MAX_SIZE",
        ("logging", "rotate_backup_count"): "LOG_ROTATE_BACKUP_COUNT",
        ("overlay", "display_network_status"): "DISPLAY_NETWORK_STATUS",
        ("overlay", "position"): "OVERLAY_POSITION",
        ("overlay", "opacity"): "OVERLAY_OPACITY",
        ("overlay", "update_interval"): "OVERLAY_UPDATE_INTERVAL",
        ("overlay", "auto_hide"): "OVERLAY_AUTO_HIDE",
        ("overlay", "use_terminal"): "OVERLAY_USE_TERMINAL",
    }

    for (section, key), env_var in reverse_mapping.items():
        if section in config_data and key in config_data[section]:
            value = config_data[section][key]
            if value is not None:
                # Convert boolean to string
                if isinstance(value, bool):
                    env_vars[env_var] = "true" if value else "false"
                else:
                    env_vars[env_var] = str(value)

    return env_vars


def migrate_env_to_yaml(input_path: str, output_path: str) -> None:
    """Migrate .env file to YAML configuration."""
    logging.info("Migrating %s to %s", input_path, output_path)

    # Load environment variables
    env_vars = load_env_file(input_path)

    # Remove sensitive API credentials - these should stay in .env for security
    config_data = {}
    for section, section_data in env_vars.items():
        if section == "vimeo":
            # Skip vimeo section entirely - API credentials must stay in .env
            logging.info("Skipping Vimeo API credentials - these will remain in .env file for security")
            continue
        else:
            config_data[section] = section_data

    # Write YAML file with warning about API credentials
    output_file = Path(output_path)
    with output_file.open("w", encoding="utf-8") as f:
        f.write("# Vimeo Monitor Configuration\n")
        f.write(f"# Migrated from: {input_path}\n")
        f.write("# \n")
        f.write("# IMPORTANT: API credentials remain in .env file for security\n")
        f.write("# Make sure your .env file contains:\n")
        f.write("# VIMEO_TOKEN=your_token\n")
        f.write("# VIMEO_KEY=your_key\n")
        f.write("# VIMEO_SECRET=your_secret\n")
        f.write("# VIMEO_STREAM_ID=your_stream_id\n\n")

        if config_data:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
        else:
            f.write("# All configuration loaded from environment variables\n")
            f.write("# Customize settings below as needed:\n\n")
            f.write("# timing:\n")
            f.write("#   check_interval: 30\n\n")
            f.write("# api_failure:\n")
            f.write("#   failure_threshold: 3\n")
            f.write("#   stability_threshold: 5\n\n")
            f.write("# logging:\n")
            f.write('#   log_level: "INFO"\n\n')
            f.write("# overlay:\n")
            f.write("#   display_network_status: true\n")

    logging.info("Successfully migrated to YAML: %s", output_path)
    logging.info("⚠️  API credentials remain in %s for security", input_path)


def migrate_env_to_toml(input_path: str, output_path: str) -> None:
    """Migrate .env file to TOML configuration."""
    logging.info("Migrating %s to %s", input_path, output_path)

    # Load environment variables
    env_vars = load_env_file(input_path)

    # Remove sensitive API credentials - these should stay in .env for security
    config_data = {}
    for section, section_data in env_vars.items():
        if section == "vimeo":
            # Skip vimeo section entirely - API credentials must stay in .env
            logging.info("Skipping Vimeo API credentials - these will remain in .env file for security")
            continue
        else:
            config_data[section] = section_data

    # Write TOML file with warning about API credentials
    output_file = Path(output_path)
    with output_file.open("w", encoding="utf-8") as f:
        f.write("# Vimeo Monitor Configuration\n")
        f.write(f"# Migrated from: {input_path}\n")
        f.write("# \n")
        f.write("# IMPORTANT: API credentials remain in .env file for security\n")
        f.write("# Make sure your .env file contains:\n")
        f.write("# VIMEO_TOKEN=your_token\n")
        f.write("# VIMEO_KEY=your_key\n")
        f.write("# VIMEO_SECRET=your_secret\n")
        f.write("# VIMEO_STREAM_ID=your_stream_id\n\n")

        if config_data:
            toml.dump(config_data, f)
        else:
            f.write("# All configuration loaded from environment variables\n")
            f.write("# Customize settings below as needed:\n\n")
            f.write("# [timing]\n")
            f.write("# check_interval = 30\n\n")
            f.write("# [api_failure]\n")
            f.write("# failure_threshold = 3\n")
            f.write("# stability_threshold = 5\n\n")
            f.write("# [logging]\n")
            f.write('# log_level = "INFO"\n\n')
            f.write("# [overlay]\n")
            f.write("# display_network_status = true\n")

    logging.info("Successfully migrated to TOML: %s", output_path)
    logging.info("⚠️  API credentials remain in %s for security", input_path)


def migrate_yaml_to_env(input_path: str, output_path: str) -> None:
    """Migrate YAML configuration to .env file."""
    logging.info("Migrating %s to %s", input_path, output_path)

    # Load YAML file
    input_file = Path(input_path)
    with input_file.open("r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f) or {}

    # Convert to environment format
    env_vars = structured_to_env_format(config_data)

    # Write .env file
    output_file = Path(output_path)
    with output_file.open("w", encoding="utf-8") as f:
        f.write("# Vimeo Monitor Environment Variables\n")
        f.write(f"# Migrated from: {input_path}\n\n")
        for key, value in sorted(env_vars.items()):
            f.write(f"{key}={value}\n")

    logging.info("Successfully migrated to .env: %s", output_path)


def migrate_toml_to_env(input_path: str, output_path: str) -> None:
    """Migrate TOML configuration to .env file."""
    logging.info("Migrating %s to %s", input_path, output_path)

    # Load TOML file
    input_file = Path(input_path)
    with input_file.open("r", encoding="utf-8") as f:
        config_data = toml.load(f) or {}

    # Convert to environment format
    env_vars = structured_to_env_format(config_data)

    # Write .env file
    output_file = Path(output_path)
    with output_file.open("w", encoding="utf-8") as f:
        f.write("# Vimeo Monitor Environment Variables\n")
        f.write(f"# Migrated from: {input_path}\n\n")
        for key, value in sorted(env_vars.items()):
            f.write(f"{key}={value}\n")

    logging.info("Successfully migrated to .env: %s", output_path)


def validate_configuration(config_path: str) -> bool:
    """Validate a configuration file."""
    try:
        # Determine file type
        path = Path(config_path)

        if path.suffix.lower() in [".yaml", ".yml"]:
            # Load YAML config data
            with path.open("r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f) or {}

            # For YAML/TOML files, we need to merge with .env for complete validation
            # since API credentials are stored separately for security
            project_root = path.parent.parent if path.parent.name == "config" else path.parent
            env_file = project_root / ".env"

            if env_file.exists():
                # Load .env data and merge
                env_data = load_env_file(str(env_file))
                # Environment data takes priority over config file data
                for section, section_data in env_data.items():
                    if section not in config_data:
                        config_data[section] = {}
                    config_data[section].update(section_data)

                logging.info("Merged configuration from %s and %s", config_path, env_file)
            else:
                logging.warning("No .env file found at %s - validation may fail for missing API credentials", env_file)

            config = VimeoMonitorConfig(**config_data)

        elif path.suffix.lower() == ".toml":
            # Load TOML config data
            with path.open("r", encoding="utf-8") as f:
                config_data = toml.load(f) or {}

            # For YAML/TOML files, we need to merge with .env for complete validation
            project_root = path.parent.parent if path.parent.name == "config" else path.parent
            env_file = project_root / ".env"

            if env_file.exists():
                # Load .env data and merge
                env_data = load_env_file(str(env_file))
                # Environment data takes priority over config file data
                for section, section_data in env_data.items():
                    if section not in config_data:
                        config_data[section] = {}
                    config_data[section].update(section_data)

                logging.info("Merged configuration from %s and %s", config_path, env_file)
            else:
                logging.warning("No .env file found at %s - validation may fail for missing API credentials", env_file)

            config = VimeoMonitorConfig(**config_data)

        elif path.suffix.lower() == ".env":
            # Load and validate .env using ConfigManager
            config_manager = EnhancedConfigManager(env_file=str(path))
            config = config_manager.get_config_object()

        else:
            logging.error("Unsupported file format: %s", path.suffix)
            return False

        if config:
            logging.info("Configuration validation successful: %s", config_path)
            logging.info("Configuration summary: %s", config.get_summary())
            return True
        else:
            logging.error("Failed to create configuration object")
            return False

    except Exception as e:
        logging.exception("Configuration validation failed: %s", e)
        return False


def main() -> None:
    """Main entry point for configuration migration utility."""
    parser = argparse.ArgumentParser(
        description="Vimeo Monitor Configuration Migration Utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Migrate .env to YAML in config directory
  python scripts/config_migrate.py env-to-yaml .env config/config.yaml

  # Migrate .env to TOML in config directory
  python scripts/config_migrate.py env-to-toml .env config/config.toml

  # Migrate YAML to .env
  python scripts/config_migrate.py yaml-to-env config/config.yaml .env

  # Migrate TOML to .env
  python scripts/config_migrate.py toml-to-env config/config.toml .env

  # Validate configuration files
  python scripts/config_migrate.py validate config/config.yaml
  python scripts/config_migrate.py validate .env

  # Create initial config from existing .env
  python scripts/config_migrate.py env-to-yaml .env config/config.yaml --validate

Note:
  - API credentials are always stored in .env file for security
  - Config files (YAML/TOML) contain non-sensitive settings only
  - Use config/ directory for configuration files
        """,
    )

    parser.add_argument(
        "command",
        choices=["env-to-yaml", "env-to-toml", "yaml-to-env", "toml-to-env", "validate"],
        help="Migration command to execute",
    )

    parser.add_argument("input_file", help="Input configuration file path")

    parser.add_argument(
        "output_file", nargs="?", help="Output configuration file path (not needed for validate command)"
    )

    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)

    try:
        if args.command == "validate":
            success = validate_configuration(args.input_file)
            sys.exit(0 if success else 1)

        elif args.output_file is None:
            logging.error("Output file path is required for migration commands")
            sys.exit(1)

        elif args.command == "env-to-yaml":
            migrate_env_to_yaml(args.input_file, args.output_file)

        elif args.command == "env-to-toml":
            migrate_env_to_toml(args.input_file, args.output_file)

        elif args.command == "yaml-to-env":
            migrate_yaml_to_env(args.input_file, args.output_file)

        elif args.command == "toml-to-env":
            migrate_toml_to_env(args.input_file, args.output_file)

        # Validate the output file
        if args.output_file:
            logging.info("Validating migrated configuration...")
            if validate_configuration(args.output_file):
                logging.info("Migration completed successfully!")
            else:
                logging.error("Migration completed but validation failed")
                sys.exit(1)

    except Exception as e:
        logging.exception("Migration failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
