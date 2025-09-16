#!/usr/bin/env python3
"""
Monitoring module for Vimeo Monitor.

This module handles Vimeo API monitoring and stream status detection.
"""

import time
from enum import Enum
from typing import Optional

from requests.exceptions import ConnectionError, RequestException, Timeout
from vimeo import VimeoClient

from .config import Config
from .logger import Logger, LoggingContext
from .process_manager import ProcessManager


class StreamStatus(Enum):
    """Enumeration of possible stream statuses."""

    LIVE = "live"
    OFFLINE = "offline"
    ERROR = "error"


class Monitor:
    """Monitors Vimeo API for stream status changes."""

    def __init__(self, config: Config, logger: Logger, process_manager: ProcessManager):
        """Initialize monitor with configuration, logger, and process manager."""
        self.config = config
        self.logger = logger
        self.monitor_logger = LoggingContext(logger, "MONITOR")
        self.process_manager = process_manager

        # Error tracking
        self.consecutive_errors = 0
        self.last_successful_check = time.time()
        self.error_threshold = 5  # Show error image after 5 consecutive failures

        # Stream restart tracking
        self.last_stream_url = None

        # Initialize Vimeo client
        try:
            self.api_client = VimeoClient(**config.get_vimeo_client_config())
            self.monitor_logger.info("Vimeo client initialized successfully")
        except Exception as e:
            self.monitor_logger.error(f"Failed to initialize Vimeo client: {e}")
            raise

        # Get stream ID
        self.stream_id = config.get_stream_id()
        self.monitor_logger.info(
            f"Monitoring stream {config.stream_selection} (ID: {self.stream_id})"
        )

    def check_stream_status(self) -> tuple[StreamStatus, str | None]:
        """Check if stream is live with comprehensive error handling and retry logic."""
        for attempt in range(self.config.max_retries):
            try:
                stream_url = f"https://api.vimeo.com/me/live_events/{self.stream_id}/m3u8_playback"
                response = self.api_client.get(stream_url)
                response_data = response.json()

                self.monitor_logger.debug(f"Vimeo API Response: {response_data}")

                # Reset error counter on successful API call
                self.consecutive_errors = 0
                self.last_successful_check = time.time()

                if "m3u8_playback_url" in response_data:
                    video_url = response_data["m3u8_playback_url"]
                    self.last_stream_url = video_url  # Store for potential restart
                    self.monitor_logger.debug("Found m3u8_playback_url in response")
                    return StreamStatus.LIVE, video_url
                else:
                    self.monitor_logger.debug("No m3u8_playback_url found in response")
                    return StreamStatus.OFFLINE, None

            except ConnectionError as e:
                self.consecutive_errors += 1
                self.monitor_logger.error(
                    f"Connection error (attempt {attempt + 1}/{self.config.max_retries}): {e}"
                )
                if attempt < self.config.max_retries - 1:
                    wait_time = 2**attempt  # Exponential backoff
                    self.monitor_logger.debug(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    self.monitor_logger.error("All connection retry attempts failed")
                    return StreamStatus.ERROR, None

            except Timeout as e:
                self.consecutive_errors += 1
                self.monitor_logger.error(
                    f"Timeout error (attempt {attempt + 1}/{self.config.max_retries}): {e}"
                )
                if attempt < self.config.max_retries - 1:
                    wait_time = 2**attempt
                    self.monitor_logger.debug(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    self.monitor_logger.error("All timeout retry attempts failed")
                    return StreamStatus.ERROR, None

            except RequestException as e:
                self.consecutive_errors += 1
                self.monitor_logger.error(
                    f"API request failed (attempt {attempt + 1}/{self.config.max_retries}): {e}"
                )
                if attempt < self.config.max_retries - 1:
                    wait_time = 2**attempt
                    self.monitor_logger.debug(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    self.monitor_logger.error("All API retry attempts failed")
                    return StreamStatus.ERROR, None

            except Exception as e:
                self.consecutive_errors += 1
                self.monitor_logger.error(f"Unexpected error during API request: {e}")
                return StreamStatus.ERROR, None

        return StreamStatus.ERROR, None

    def update_display(
        self, status: StreamStatus, video_url: str | None = None
    ) -> None:
        """Update display based on stream status with error image support."""
        try:
            if status == StreamStatus.LIVE and video_url:
                self.monitor_logger.info(f"Stream active. URL: {video_url}")
                self.process_manager.start_stream_process(video_url)
            elif status == StreamStatus.OFFLINE:
                self.monitor_logger.warning(
                    "Stream not active. Displaying static image."
                )
                if self.config.static_image_path:
                    self.process_manager.start_image_process(
                        self.config.static_image_path
                    )
            elif status == StreamStatus.ERROR:
                # Show error image if we have too many consecutive errors
                if self.consecutive_errors >= self.error_threshold:
                    self.monitor_logger.error(
                        f"Too many consecutive errors ({self.consecutive_errors}). Displaying error image."
                    )
                    if self.config.error_image_path:
                        self.process_manager.start_error_process(
                            self.config.error_image_path
                        )
                else:
                    self.monitor_logger.warning(
                        f"Stream error (consecutive: {self.consecutive_errors}). Maintaining current display."
                    )
            else:
                self.monitor_logger.error(f"Unknown stream status: {status}")
        except Exception as e:
            self.monitor_logger.error(f"Failed to update display: {e}")
            # If display update fails, try to show error image
            try:
                if self.config.error_image_path:
                    self.process_manager.start_error_process(
                        self.config.error_image_path
                    )
            except Exception as error_e:
                self.monitor_logger.critical(f"Failed to show error image: {error_e}")
            raise

    def run_monitoring_cycle(self) -> None:
        """Run one monitoring cycle."""
        try:
            # Check if process needs restart
            if not self.process_manager.is_process_running():
                restart_success = self.process_manager.restart_process()
                if not restart_success:
                    self.monitor_logger.error(
                        "Process restart failed - showing error image"
                    )
                    if self.config.error_image_path:
                        self.process_manager.start_error_process(
                            self.config.error_image_path
                        )
                    return

            status, video_url = self.check_stream_status()
            self.update_display(status, video_url)
        except Exception as e:
            self.monitor_logger.error(f"Error in monitoring cycle: {e}")
            # Don't raise - let the main loop handle retries

    def get_status_info(self) -> dict:
        """Get current monitoring status information."""
        current_time = time.time()
        time_since_last_success = current_time - self.last_successful_check

        return {
            "stream_id": self.stream_id,
            "stream_selection": self.config.stream_selection,
            "process_status": self.process_manager.get_process_status(),
            "api_configured": bool(self.api_client),
            "consecutive_errors": self.consecutive_errors,
            "error_threshold": self.error_threshold,
            "last_successful_check": self.last_successful_check,
            "time_since_last_success": time_since_last_success,
            "is_healthy": self.consecutive_errors < self.error_threshold,
        }

    def is_healthy(self) -> bool:
        """Check if the monitoring system is healthy."""
        return self.consecutive_errors < self.error_threshold

    def restart_stream_if_needed(self) -> bool:
        """Restart stream process if needed and we have a valid URL."""
        if (
            self.process_manager.current_mode == "stream"
            and not self.process_manager.is_process_running()
            and self.last_stream_url
        ):

            self.monitor_logger.info(  # type: ignore[unreachable]
                f"Restarting stream process with URL: {self.last_stream_url}"
            )
            try:
                self.process_manager.start_stream_process(self.last_stream_url)
                return True
            except Exception as e:
                self.monitor_logger.error(f"Failed to restart stream process: {e}")
                return False

        return True
    
    def get_stream_url(self) -> Optional[str]:
        """Get the current stream URL.
        
        Returns:
            Current stream URL or None if not available
        """
        return self.last_stream_url