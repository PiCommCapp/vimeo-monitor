#!/usr/bin/env python3

"""
Log Management Utility for Vimeo Monitor

This script provides advanced log management features including:
- Manual log rotation
- Log compression
- Log analysis and statistics
- Log cleanup
- Health monitoring of log rotation
"""

import argparse
import gzip
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

DEFAULT_LOG_DIR = "./logs"
DEFAULT_LOG_FILE = "vimeo_monitor.logs"


def get_log_files(log_dir: str) -> list[Path]:
    """Get all log files in the specified directory."""
    log_path = Path(log_dir)
    if not log_path.exists():
        return []

    # Find all log files (current and rotated)
    patterns = ["*.log", "*.log.*", "*.logs", "*.logs.*"]
    log_files = []

    for pattern in patterns:
        log_files.extend(log_path.glob(pattern))

    return sorted(log_files)


def get_log_stats(log_files: list[Path]) -> dict[str, any]:
    """Get statistics about log files."""
    total_size = 0
    file_count = len(log_files)
    compressed_count = 0
    oldest_file = None
    newest_file = None

    for log_file in log_files:
        if log_file.exists():
            stat = log_file.stat()
            total_size += stat.st_size

            if log_file.suffix == ".gz":
                compressed_count += 1

            file_time = datetime.fromtimestamp(stat.st_mtime)
            if oldest_file is None or file_time < oldest_file:
                oldest_file = file_time
            if newest_file is None or file_time > newest_file:
                newest_file = file_time

    return {
        "total_size": total_size,
        "total_size_mb": total_size / (1024 * 1024),
        "file_count": file_count,
        "compressed_count": compressed_count,
        "uncompressed_count": file_count - compressed_count,
        "oldest_file": oldest_file,
        "newest_file": newest_file,
    }


def compress_log_file(log_file: Path) -> bool:
    """Compress a log file using gzip."""
    if log_file.suffix == ".gz":
        print(f"⚠️  File {log_file} is already compressed")
        return True

    try:
        compressed_file = log_file.with_suffix(log_file.suffix + ".gz")

        with open(log_file, "rb") as f_in:
            with gzip.open(compressed_file, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        # Preserve timestamps
        stat = log_file.stat()
        os.utime(compressed_file, (stat.st_atime, stat.st_mtime))

        # Remove original file
        log_file.unlink()

        print(f"✅ Compressed {log_file} -> {compressed_file}")
        return True

    except Exception as e:
        print(f"❌ Failed to compress {log_file}: {e}")
        return False


def rotate_log_file(log_file: Path, max_size: int, backup_count: int) -> bool:
    """Manually rotate a log file."""
    if not log_file.exists():
        print(f"⚠️  Log file {log_file} does not exist")
        return False

    file_size = log_file.stat().st_size
    if file_size < max_size:
        print(f"⚠️  Log file {log_file} ({file_size} bytes) is smaller than max size ({max_size} bytes)")
        return False

    try:
        # Rotate existing backup files
        for i in range(backup_count - 1, 0, -1):
            old_backup = Path(f"{log_file}.{i}")
            new_backup = Path(f"{log_file}.{i + 1}")

            if old_backup.exists():
                if new_backup.exists():
                    new_backup.unlink()
                old_backup.rename(new_backup)

        # Move current log to .1
        backup_file = Path(f"{log_file}.1")
        if backup_file.exists():
            backup_file.unlink()
        log_file.rename(backup_file)

        # Create new empty log file
        log_file.touch()

        print(f"✅ Rotated {log_file} (was {file_size} bytes)")
        return True

    except Exception as e:
        print(f"❌ Failed to rotate {log_file}: {e}")
        return False


def clean_old_logs(log_dir: str, days_to_keep: int) -> tuple[int, int]:
    """Clean log files older than specified days."""
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    log_files = get_log_files(log_dir)

    removed_count = 0
    total_size_freed = 0

    for log_file in log_files:
        if log_file.exists():
            file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
            if file_time < cutoff_date:
                file_size = log_file.stat().st_size
                try:
                    log_file.unlink()
                    removed_count += 1
                    total_size_freed += file_size
                    print(f"🗑️  Removed old log file: {log_file}")
                except Exception as e:
                    print(f"❌ Failed to remove {log_file}: {e}")

    return removed_count, total_size_freed


def analyze_logs(log_dir: str) -> None:
    """Analyze log files and provide detailed report."""
    log_files = get_log_files(log_dir)

    if not log_files:
        print(f"⚠️  No log files found in {log_dir}")
        return

    stats = get_log_stats(log_files)

    print(f"\n📊 Log Analysis Report for {log_dir}")
    print("=" * 50)
    print(f"📁 Total log files: {stats['file_count']}")
    print(f"📦 Compressed files: {stats['compressed_count']}")
    print(f"📄 Uncompressed files: {stats['uncompressed_count']}")
    print(f"💾 Total size: {stats['total_size_mb']:.2f} MB ({stats['total_size']} bytes)")

    if stats["oldest_file"]:
        print(f"🕐 Oldest log: {stats['oldest_file'].strftime('%Y-%m-%d %H:%M:%S')}")
    if stats["newest_file"]:
        print(f"🕐 Newest log: {stats['newest_file'].strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n📋 File Details:")
    for log_file in log_files:
        if log_file.exists():
            stat = log_file.stat()
            size_mb = stat.st_size / (1024 * 1024)
            modified = datetime.fromtimestamp(stat.st_mtime)
            compression_status = "🗜️" if log_file.suffix == ".gz" else "📄"
            print(f"  {compression_status} {log_file.name}: {size_mb:.2f} MB ({modified.strftime('%Y-%m-%d %H:%M')})")


def main():
    """Main function for log management CLI."""
    parser = argparse.ArgumentParser(description="Vimeo Monitor Log Management Utility")
    parser.add_argument("--log-dir", default=DEFAULT_LOG_DIR, help="Log directory path")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze log files")

    # Rotate command
    rotate_parser = subparsers.add_parser("rotate", help="Manually rotate log file")
    rotate_parser.add_argument("--file", default=DEFAULT_LOG_FILE, help="Log file to rotate")
    rotate_parser.add_argument("--max-size", type=int, default=10485760, help="Max size in bytes (10MB default)")
    rotate_parser.add_argument("--backup-count", type=int, default=5, help="Number of backup files")

    # Compress command
    compress_parser = subparsers.add_parser("compress", help="Compress log files")
    compress_parser.add_argument("--pattern", default="*.log.*", help="Pattern for files to compress")

    # Clean command
    clean_parser = subparsers.add_parser("clean", help="Clean old log files")
    clean_parser.add_argument("--days", type=int, default=30, help="Keep logs newer than this many days")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    log_dir = Path(args.log_dir)
    if not log_dir.exists():
        print(f"❌ Log directory {log_dir} does not exist")
        return

    if args.command == "analyze":
        analyze_logs(str(log_dir))

    elif args.command == "rotate":
        log_file = log_dir / args.file
        rotate_log_file(log_file, args.max_size, args.backup_count)

    elif args.command == "compress":
        log_files = list(log_dir.glob(args.pattern))
        if not log_files:
            print(f"⚠️  No files matching pattern {args.pattern}")
            return

        compressed_count = 0
        for log_file in log_files:
            if log_file.suffix != ".gz":
                if compress_log_file(log_file):
                    compressed_count += 1

        print(f"✅ Compressed {compressed_count} files")

    elif args.command == "clean":
        removed_count, size_freed = clean_old_logs(str(log_dir), args.days)
        size_freed_mb = size_freed / (1024 * 1024)
        print(f"✅ Cleaned {removed_count} old log files, freed {size_freed_mb:.2f} MB")


if __name__ == "__main__":
    main()
