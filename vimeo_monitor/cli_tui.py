#!/usr/bin/env python3

"""Command-line entry point for Vimeo Monitor TUI."""

import argparse
import logging
import sys
import time
from pathlib import Path


def setup_path() -> None:
    """Add the vimeo_monitor package to the Python path if needed."""
    # Try to find the vimeo_monitor installation
    possible_paths = [
        Path("/opt/vimeo-monitor"),  # Service installation path
        Path.cwd(),  # Current directory
        Path.home() / "vimeo-monitor",  # User home directory
    ]

    for path in possible_paths:
        if (path / "vimeo_monitor").exists():
            sys.path.insert(0, str(path))
            break
    else:
        # If not found, assume it's in the current Python environment
        pass


def main() -> None:
    """Main entry point for the TUI."""
    parser = argparse.ArgumentParser(
        description="Vimeo Monitor Terminal User Interface",
        epilog="Use arrow keys to navigate, TAB to switch between widgets, and keyboard shortcuts shown in the footer.",
    )
    parser.add_argument("--working-dir", type=str, help="Working directory for the monitor (default: auto-detect)")
    parser.add_argument("--config-file", type=str, help="Configuration file path (default: auto-detect)")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="WARNING",
        help="Log level for TUI (default: WARNING)",
    )
    parser.add_argument("--simple", action="store_true", help="Force use of simple TUI (curses-based)")
    parser.add_argument("--version", action="version", version="Vimeo Monitor TUI v1.0.0")

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()), format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Setup Python path
    setup_path()

    # Change working directory if specified
    if args.working_dir:
        import os

        os.chdir(args.working_dir)

    try:
        # Try advanced TUI first unless simple mode is forced
        if not args.simple:
            try:
                from vimeo_monitor.tui import run_tui

                print("🚀 Starting Vimeo Monitor TUI...")
                print("📋 Keyboard shortcuts:")
                print("  • q: Quit")
                print("  • r: Refresh data")
                print("  • s: Status tab")
                print("  • c: Configuration tab")
                print("  • l: Logs tab")
                print("  • m: Metrics view")
                print()
                print("Use TAB to navigate between widgets, arrows for selection.")
                print("Press any key to continue...")

                # Run the advanced TUI
                run_tui()
                return  # Success, exit

            except ImportError as textual_error:
                print(f"⚠️  Advanced TUI not available: {textual_error}")
                print("🔄 Falling back to simple TUI...")
                print()

        # Fall back to simple TUI or use it directly if forced
        from vimeo_monitor.simple_tui import run_simple_tui

        print("🚀 Starting Vimeo Monitor Simple TUI...")
        print("📋 Keyboard shortcuts:")
        print("  • q: Quit")
        print("  • r: Refresh data")
        print("  • TAB/←/→: Switch tabs")
        print()
        print("Starting in 2 seconds...")
        time.sleep(2)

        run_simple_tui()

    except ImportError as e:
        print(f"❌ Error: Could not import vimeo_monitor components: {e}")
        print("📍 Make sure you're running this from the correct directory or the service is installed.")
        print("🔧 Try: cd /opt/vimeo-monitor && vimeo-tui")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 TUI stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error running TUI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
