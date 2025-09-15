#!/usr/bin/env python3
"""
Process management module for Vimeo Monitor.

This module handles the lifecycle of VLC/FFmpeg subprocesses for displaying
live streams and static images.
"""

import subprocess
import time
from typing import Optional, List
from .config import Config
from .logger import Logger, LoggingContext


class ProcessManager:
    """Manages VLC/FFmpeg subprocesses for stream display."""
    
    def __init__(self, config: Config, logger: Logger):
        """Initialize process manager with configuration and logger."""
        self.config = config
        self.logger = logger
        self.process_logger = LoggingContext(logger, "PROCESS")
        self.current_process: Optional[subprocess.Popen] = None
        self.current_mode: Optional[str] = None
    
    def start_stream_process(self, video_url: str) -> None:
        """Start VLC process for live stream."""
        if self.current_mode == "stream":
            self.process_logger.debug("Stream process already running")
            return
        
        self._stop_current_process()
        
        command = ["cvlc", "-f", video_url]
        self.process_logger.info(f"Starting stream process: {' '.join(command)}")
        
        try:
            self.current_process = subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.current_mode = "stream"
            self.process_logger.info("Stream process started successfully")
        except Exception as e:
            self.process_logger.error(f"Failed to start stream process: {e}")
            raise
    
    def start_image_process(self, image_path: str) -> None:
        """Start FFmpeg process for static image."""
        if self.current_mode == "image":
            self.process_logger.debug("Image process already running")
            return
        
        self._stop_current_process()
        
        command = ["ffplay", "-fs", "-loop", "1", image_path]
        self.process_logger.info(f"Starting image process: {' '.join(command)}")
        
        try:
            self.current_process = subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.current_mode = "image"
            self.process_logger.info("Image process started successfully")
        except Exception as e:
            self.process_logger.error(f"Failed to start image process: {e}")
            raise
    
    def start_error_process(self, error_image_path: str) -> None:
        """Start FFmpeg process for error image."""
        if self.current_mode == "error":
            self.process_logger.debug("Error process already running")
            return
        
        self._stop_current_process()
        
        command = ["ffplay", "-fs", "-loop", "1", error_image_path]
        self.process_logger.warning(f"Starting error process: {' '.join(command)}")
        
        try:
            self.current_process = subprocess.Popen(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.current_mode = "error"
            self.process_logger.warning("Error process started successfully")
        except Exception as e:
            self.process_logger.error(f"Failed to start error process: {e}")
            raise
    
    def _stop_current_process(self) -> None:
        """Stop current process if running."""
        if self.current_process and self.current_process.poll() is None:
            self.process_logger.info("Stopping current process")
            self.current_process.terminate()
            
            # Wait for graceful termination
            try:
                self.current_process.wait(timeout=5)
                self.process_logger.debug("Process terminated gracefully")
            except subprocess.TimeoutExpired:
                self.process_logger.warning("Process didn't terminate, killing")
                self.current_process.kill()
                self.current_process.wait()
                self.process_logger.debug("Process killed")
        
        self.current_process = None
        self.current_mode = None
    
    def is_process_running(self) -> bool:
        """Check if current process is running."""
        if self.current_process is None:
            return False
        
        return self.current_process.poll() is None
    
    def get_process_status(self) -> dict:
        """Get current process status information."""
        return {
            "mode": self.current_mode,
            "running": self.is_process_running(),
            "pid": self.current_process.pid if self.current_process else None,
            "return_code": self.current_process.returncode if self.current_process else None
        }
    
    def restart_process(self) -> None:
        """Restart the current process if it has stopped unexpectedly."""
        if not self.is_process_running() and self.current_mode:
            self.process_logger.warning(f"Process stopped unexpectedly, restarting {self.current_mode} mode")
            
            if self.current_mode == "stream":
                # We need the video URL to restart - this will be handled by the monitor
                self.process_logger.error("Cannot restart stream process without video URL")
            elif self.current_mode == "image":
                self.start_image_process(self.config.static_image_path)
    
    def cleanup(self) -> None:
        """Clean up on shutdown."""
        self.process_logger.info("Cleaning up process manager")
        self._stop_current_process()
        self.process_logger.info("Process manager cleanup complete")
    
    def health_check(self) -> bool:
        """Perform health check on current process."""
        if self.current_process is None:
            return True  # No process is considered healthy
        
        if not self.is_process_running():
            self.process_logger.warning("Health check failed: process not running")
            return False
        
        return True
