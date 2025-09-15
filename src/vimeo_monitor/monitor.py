#!/usr/bin/env python3
"""
Monitoring module for Vimeo Monitor.

This module handles Vimeo API monitoring and stream status detection.
"""

import time
from typing import Tuple, Optional
from enum import Enum
from vimeo import VimeoClient
from requests.exceptions import RequestException

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
        
        # Initialize Vimeo client
        try:
            self.api_client = VimeoClient(**config.get_vimeo_client_config())
            self.monitor_logger.info("Vimeo client initialized successfully")
        except Exception as e:
            self.monitor_logger.error(f"Failed to initialize Vimeo client: {e}")
            raise
        
        # Get stream ID
        self.stream_id = config.get_stream_id()
        self.monitor_logger.info(f"Monitoring stream {config.stream_selection} (ID: {self.stream_id})")
    
    def check_stream_status(self) -> Tuple[StreamStatus, Optional[str]]:
        """Check if stream is live with retry logic."""
        for attempt in range(self.config.max_retries):
            try:
                stream_url = f"https://api.vimeo.com/me/live_events/{self.stream_id}/m3u8_playback"
                response = self.api_client.get(stream_url)
                response_data = response.json()
                
                self.monitor_logger.debug(f"Vimeo API Response: {response_data}")
                
                if "m3u8_playback_url" in response_data:
                    video_url = response_data["m3u8_playback_url"]
                    self.monitor_logger.debug("Found m3u8_playback_url in response")
                    return StreamStatus.LIVE, video_url
                else:
                    self.monitor_logger.debug("No m3u8_playback_url found in response")
                    return StreamStatus.OFFLINE, None
                    
            except RequestException as e:
                self.monitor_logger.error(f"API request failed (attempt {attempt + 1}/{self.config.max_retries}): {e}")
                if attempt < self.config.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    self.monitor_logger.debug(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    self.monitor_logger.error("All API retry attempts failed")
                    return StreamStatus.ERROR, None
            except Exception as e:
                self.monitor_logger.error(f"Unexpected error during API request: {e}")
                return StreamStatus.ERROR, None
        
        return StreamStatus.ERROR, None
    
    def update_display(self, status: StreamStatus, video_url: Optional[str] = None) -> None:
        """Update display based on stream status."""
        try:
            if status == StreamStatus.LIVE and video_url:
                self.monitor_logger.info(f"Stream active. URL: {video_url}")
                self.process_manager.start_stream_process(video_url)
            elif status == StreamStatus.OFFLINE:
                self.monitor_logger.warning("Stream not active. Displaying static image.")
                self.process_manager.start_image_process(self.config.static_image_path)
            elif status == StreamStatus.ERROR:
                self.monitor_logger.error("Stream status error. Maintaining current display.")
            else:
                self.monitor_logger.error(f"Unknown stream status: {status}")
        except Exception as e:
            self.monitor_logger.error(f"Failed to update display: {e}")
            raise
    
    def run_monitoring_cycle(self) -> None:
        """Run one monitoring cycle."""
        try:
            status, video_url = self.check_stream_status()
            self.update_display(status, video_url)
        except Exception as e:
            self.monitor_logger.error(f"Error in monitoring cycle: {e}")
            # Don't raise - let the main loop handle retries
    
    def get_status_info(self) -> dict:
        """Get current monitoring status information."""
        return {
            "stream_id": self.stream_id,
            "stream_selection": self.config.stream_selection,
            "process_status": self.process_manager.get_process_status(),
            "api_configured": bool(self.api_client)
        }
