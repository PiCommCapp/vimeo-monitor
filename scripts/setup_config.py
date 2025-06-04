#!/usr/bin/env python3

"""Configuration setup utility for Vimeo Monitor."""

import argparse
import logging
import shutil
import sys
from pathlib import Path


def setup_logging(level: str = "INFO") -> None:
    """Setup logging for the setup utility."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def copy_config_template(config_type: str, force: bool = False) -> bool:
    """Copy configuration template to working file.

    Args:
        config_type: Type of config (yaml or toml)
        force: Overwrite existing files

    Returns:
        True if file was created, False if skipped
    """
    project_root = Path(__file__).parent.parent
    template_file = project_root / "config" / f"config.{config_type}.example"
    target_file = project_root / "config" / f"config.{config_type}"

    if not template_file.exists():
        logging.error("Template file not found: %s", template_file)
        return False

    if target_file.exists() and not force:
        logging.info("Config file already exists: %s (use --force to overwrite)", target_file)
        return False

    try:
        shutil.copy2(template_file, target_file)
        logging.info("Created configuration file: %s", target_file)
        return True
    except Exception as e:
        logging.exception("Failed to copy config template: %s", e)
        return False


def copy_env_template(force: bool = False) -> bool:
    """Copy .env template to working file.

    Args:
        force: Overwrite existing .env file

    Returns:
        True if file was created, False if skipped
    """
    project_root = Path(__file__).parent.parent
    template_file = project_root / ".env.example"
    target_file = project_root / ".env"

    if not template_file.exists():
        logging.error("Template file not found: %s", template_file)
        return False

    if target_file.exists() and not force:
        logging.info("Environment file already exists: %s (use --force to overwrite)", target_file)
        return False

    try:
        shutil.copy2(template_file, target_file)
        logging.info("Created environment file: %s", target_file)
        logging.warning("IMPORTANT: Edit %s with your actual API credentials!", target_file)
        return True
    except Exception as e:
        logging.exception("Failed to copy environment template: %s", e)
        return False


def validate_api_credentials() -> bool:
    """Validate that API credentials are configured.

    Returns:
        True if credentials appear to be configured, False otherwise
    """
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"

    if not env_file.exists():
        logging.error("Environment file not found: %s", env_file)
        logging.info("Run 'python scripts/setup_config.py --env' to create it")
        return False

    required_vars = ["VIMEO_TOKEN", "VIMEO_KEY", "VIMEO_SECRET", "VIMEO_STREAM_ID"]
    missing_vars = []
    placeholder_vars = []

    try:
        with env_file.open("r", encoding="utf-8") as f:
            content = f.read()

        for var in required_vars:
            if f"{var}=" not in content:
                missing_vars.append(var)
            elif f"{var}=your_" in content or f"{var}=your-" in content:
                placeholder_vars.append(var)

        if missing_vars:
            logging.error("Missing required environment variables: %s", ", ".join(missing_vars))
            return False

        if placeholder_vars:
            logging.warning("Environment variables still contain placeholder values: %s", ", ".join(placeholder_vars))
            logging.warning("Please edit %s with your actual API credentials", env_file)
            return False

        logging.info("API credentials appear to be configured ✅")
        return True

    except Exception as e:
        logging.exception("Failed to validate environment file: %s", e)
        return False


def check_directory_structure() -> None:
    """Check and create required directory structure."""
    project_root = Path(__file__).parent.parent

    required_dirs = ["config", "logs", "media", "config_backups"]

    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                logging.info("Created directory: %s", dir_path)
            except Exception as e:
                logging.exception("Failed to create directory %s: %s", dir_path, e)
        else:
            logging.debug("Directory exists: %s", dir_path)


def test_configuration() -> bool:
    """Test the current configuration.

    Returns:
        True if configuration is valid, False otherwise
    """
    try:
        # Add parent directory to path to import vimeo_monitor modules
        sys.path.insert(0, str(Path(__file__).parent.parent))

        from vimeo_monitor.config import EnhancedConfigManager

        # Try to load configuration
        config_manager = EnhancedConfigManager()
        config_obj = config_manager.get_config_object()

        if config_obj:
            logging.info("Configuration validation successful ✅")
            logging.info("Configuration summary: %s", config_obj.get_summary())
            return True
        else:
            logging.error("Failed to create configuration object")
            return False

    except Exception as e:
        logging.exception("Configuration validation failed: %s", e)
        return False


def main() -> None:
    """Main entry point for configuration setup utility."""
    parser = argparse.ArgumentParser(
        description="Vimeo Monitor Configuration Setup Utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initial setup (creates .env and config.yaml)
  python scripts/setup_config.py --init

  # Create environment file only
  python scripts/setup_config.py --env

  # Create YAML configuration file
  python scripts/setup_config.py --yaml

  # Create TOML configuration file
  python scripts/setup_config.py --toml

  # Validate current configuration
  python scripts/setup_config.py --validate

  # Force overwrite existing files
  python scripts/setup_config.py --init --force
        """,
    )

    parser.add_argument("--init", action="store_true", help="Initialize complete configuration (.env + config.yaml)")
    parser.add_argument("--env", action="store_true", help="Create .env file from template")
    parser.add_argument("--yaml", action="store_true", help="Create config.yaml file from template")
    parser.add_argument("--toml", action="store_true", help="Create config.toml file from template")
    parser.add_argument("--validate", action="store_true", help="Validate current configuration")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)

    # If no specific action, show help
    if not any([args.init, args.env, args.yaml, args.toml, args.validate]):
        parser.print_help()
        return

    try:
        # Check/create directory structure
        check_directory_structure()

        success = True

        if args.init:
            logging.info("Initializing Vimeo Monitor configuration...")
            success &= copy_env_template(args.force)
            success &= copy_config_template("yaml", args.force)

        if args.env:
            success &= copy_env_template(args.force)

        if args.yaml:
            success &= copy_config_template("yaml", args.force)

        if args.toml:
            success &= copy_config_template("toml", args.force)

        if args.validate:
            if not validate_api_credentials():
                success = False
            else:
                success &= test_configuration()

        if success:
            if not args.validate:
                logging.info("")
                logging.info("🎉 Configuration setup completed successfully!")
                logging.info("")
                logging.info("Next steps:")
                logging.info("1. Edit .env with your actual Vimeo API credentials")
                logging.info("2. Customize config/config.yaml with your preferences")
                logging.info("3. Run 'python scripts/setup_config.py --validate' to test")
                logging.info("4. Start monitoring with 'uv run python -m vimeo_monitor.monitor'")
        else:
            logging.error("Configuration setup encountered errors")
            sys.exit(1)

    except Exception as e:
        logging.exception("Configuration setup failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
