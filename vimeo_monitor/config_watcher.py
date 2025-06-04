#!/usr/bin/env python3

"""Configuration file watcher for live reload functionality."""

import logging
import threading
import time
from pathlib import Path
from typing import Protocol

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


class ConfigChangeCallback(Protocol):
    """Protocol for configuration change callbacks."""

    def __call__(self, config_path: str) -> bool:
        """Handle configuration change.

        Args:
            config_path: Path to changed configuration file

        Returns:
            True if configuration was successfully reloaded, False otherwise
        """
        ...


class ConfigFileHandler(FileSystemEventHandler):
    """File system event handler for configuration files."""

    def __init__(self, watched_files: set[str], callback: ConfigChangeCallback) -> None:
        """Initialize the configuration file handler.

        Args:
            watched_files: Set of file paths to watch
            callback: Function to call when configuration changes
        """
        super().__init__()
        self.watched_files = watched_files
        self.callback = callback
        self.last_change_time: dict[str, float] = {}
        self.debounce_delay = 1.0  # Wait 1 second before processing changes

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events."""
        if event.is_directory:
            return

        file_path = str(Path(event.src_path).resolve())

        # Check if this is a file we're watching
        if file_path not in self.watched_files:
            return

        # Debounce rapid file changes (editors may write multiple times)
        current_time = time.time()
        if file_path in self.last_change_time:
            if current_time - self.last_change_time[file_path] < self.debounce_delay:
                return

        self.last_change_time[file_path] = current_time

        logging.info("Configuration file changed: %s", file_path)

        # Call the reload callback
        try:
            success = self.callback(file_path)
            if success:
                logging.info("Configuration successfully reloaded from: %s", file_path)
            else:
                logging.error("Failed to reload configuration from: %s", file_path)
        except Exception as e:
            logging.exception("Error reloading configuration from %s: %s", file_path, e)


class ConfigWatcher:
    """Watches configuration files for changes and triggers reloads."""

    def __init__(self, callback: ConfigChangeCallback) -> None:
        """Initialize the configuration watcher.

        Args:
            callback: Function to call when configuration changes
        """
        self.callback = callback
        self.observer: Observer | None = None
        self.watched_files: set[str] = set()
        self.watched_directories: set[str] = set()
        self.handler: ConfigFileHandler | None = None
        self._lock = threading.Lock()
        self._running = False

    def add_file(self, file_path: str) -> None:
        """Add a file to be watched for changes.

        Args:
            file_path: Path to configuration file to watch
        """
        with self._lock:
            resolved_path = str(Path(file_path).resolve())
            self.watched_files.add(resolved_path)

            # Also watch the parent directory
            parent_dir = str(Path(file_path).parent.resolve())
            self.watched_directories.add(parent_dir)

            logging.debug("Added file to watch list: %s", resolved_path)

            # If we're already running, restart the observer to include new files
            if self._running:
                self._restart_observer()

    def remove_file(self, file_path: str) -> None:
        """Remove a file from being watched.

        Args:
            file_path: Path to configuration file to stop watching
        """
        with self._lock:
            resolved_path = str(Path(file_path).resolve())
            self.watched_files.discard(resolved_path)

            logging.debug("Removed file from watch list: %s", resolved_path)

            # If we're running, restart observer
            if self._running:
                self._restart_observer()

    def start(self) -> None:
        """Start watching for configuration file changes."""
        with self._lock:
            if self._running:
                logging.warning("ConfigWatcher already running")
                return

            if not self.watched_files:
                logging.warning("No configuration files to watch")
                return

            self._start_observer()
            self._running = True
            logging.info("Configuration watcher started")

    def stop(self) -> None:
        """Stop watching for configuration file changes."""
        with self._lock:
            if not self._running:
                return

            self._stop_observer()
            self._running = False
            logging.info("Configuration watcher stopped")

    def _start_observer(self) -> None:
        """Start the file system observer."""
        self.observer = Observer()
        self.handler = ConfigFileHandler(self.watched_files, self.callback)

        # Watch all parent directories
        for directory in self.watched_directories:
            if Path(directory).exists():
                self.observer.schedule(self.handler, directory, recursive=False)
                logging.debug("Watching directory: %s", directory)

        self.observer.start()

    def _stop_observer(self) -> None:
        """Stop the file system observer."""
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=5.0)
            if self.observer.is_alive():
                logging.warning("Observer did not stop gracefully")
            self.observer = None

        self.handler = None

    def _restart_observer(self) -> None:
        """Restart the file system observer."""
        logging.debug("Restarting configuration watcher")
        self._stop_observer()
        if self.watched_files:
            self._start_observer()
        else:
            self._running = False

    def is_running(self) -> bool:
        """Check if the watcher is currently running.

        Returns:
            True if watcher is running, False otherwise
        """
        with self._lock:
            return self._running

    def get_watched_files(self) -> set[str]:
        """Get the set of currently watched files.

        Returns:
            Set of watched file paths
        """
        with self._lock:
            return self.watched_files.copy()


class ConfigBackupManager:
    """Manages configuration backups and versioning."""

    def __init__(self, backup_dir: str = "./config_backups") -> None:
        """Initialize the backup manager.

        Args:
            backup_dir: Directory to store configuration backups
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, config_path: str, suffix: str = "") -> str:
        """Create a backup of a configuration file.

        Args:
            config_path: Path to configuration file to backup
            suffix: Optional suffix for backup filename

        Returns:
            Path to created backup file
        """
        source_path = Path(config_path)
        if not source_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        # Generate backup filename with timestamp
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_name = f"{source_path.stem}_{timestamp}"
        if suffix:
            backup_name += f"_{suffix}"
        backup_name += source_path.suffix

        backup_path = self.backup_dir / backup_name

        # Copy the file
        import shutil

        shutil.copy2(source_path, backup_path)

        logging.info("Created configuration backup: %s", backup_path)
        return str(backup_path)

    def list_backups(self, config_name: str | None = None) -> list[str]:
        """List available configuration backups.

        Args:
            config_name: Optional filter by configuration file name

        Returns:
            List of backup file paths, sorted by creation time (newest first)
        """
        backups = []

        for backup_file in self.backup_dir.iterdir():
            if backup_file.is_file():
                if config_name is None or backup_file.name.startswith(config_name):
                    backups.append(str(backup_file))

        # Sort by modification time (newest first)
        backups.sort(key=lambda x: Path(x).stat().st_mtime, reverse=True)

        return backups

    def restore_backup(self, backup_path: str, target_path: str) -> None:
        """Restore a configuration from backup.

        Args:
            backup_path: Path to backup file
            target_path: Path where to restore the configuration
        """
        backup_file = Path(backup_path)
        target_file = Path(target_path)

        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        # Create backup of current file before restoring
        if target_file.exists():
            self.create_backup(str(target_file), "pre_restore")

        # Copy backup to target location
        import shutil

        shutil.copy2(backup_file, target_file)

        logging.info("Restored configuration from backup %s to %s", backup_path, target_path)

    def cleanup_old_backups(self, max_backups: int = 10) -> None:
        """Clean up old backup files, keeping only the most recent ones.

        Args:
            max_backups: Maximum number of backup files to keep per configuration
        """
        # Group backups by configuration name
        backup_groups: dict[str, list[Path]] = {}

        for backup_file in self.backup_dir.iterdir():
            if backup_file.is_file():
                # Extract config name from backup filename (before first underscore)
                config_name = backup_file.name.split("_")[0]
                if config_name not in backup_groups:
                    backup_groups[config_name] = []
                backup_groups[config_name].append(backup_file)

        # Clean up each group
        for config_name, backups in backup_groups.items():
            # Sort by modification time (newest first)
            backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # Remove old backups
            for old_backup in backups[max_backups:]:
                try:
                    old_backup.unlink()
                    logging.debug("Removed old backup: %s", old_backup)
                except OSError as e:
                    logging.warning("Failed to remove old backup %s: %s", old_backup, e)
