#!/usr/bin/env python3

"""Stream and media playback management with process lifecycle handling."""

import logging
import subprocess
from pathlib import Path
from typing import Any

from vimeo_monitor.config import ConfigManager
from vimeo_monitor.health import HealthMonitor


class StreamMode:
    """Stream mode constants."""

    STREAM = "stream"
    IMAGE = "image"
    API_FAILURE = "api_failure"


class StreamManager:
    """Manages media playback processes and mode switching."""

    def __init__(self, config: ConfigManager, health_monitor: HealthMonitor) -> None:
        """Initialize stream manager.

        Args:
            config: Configuration manager instance
            health_monitor: Health monitor instance
        """
        self.config = config
        self.health_monitor = health_monitor

        # Process management
        self.current_process: subprocess.Popen[bytes] | None = None
        self.current_mode: str | None = None

        logging.debug("Stream manager initialized")

    def determine_mode(self, response_data: dict[str, Any] | None) -> str:
        """Determine which mode to run based on API response and failure state.

        Args:
            response_data: API response data

        Returns:
            Mode string (stream, image, or api_failure)
        """
        if self.health_monitor.api_failure_mode:
            return StreamMode.API_FAILURE
        elif response_data and "m3u8_playback_url" in response_data:
            logging.debug("Found m3u8_playback_url in response")
            return StreamMode.STREAM
        else:
            logging.debug("No m3u8_playback_url found in response. Full response: %s", response_data)
            return StreamMode.IMAGE

    def kill_current_process(self) -> None:
        """Kill the current media player process."""
        if self.current_process and self.current_process.poll() is None:
            logging.info("Killing current media player process (PID: %s)", self.current_process.pid)
            try:
                self.current_process.terminate()
                # Give process time to terminate gracefully
                try:
                    self.current_process.wait(timeout=5)
                    logging.debug("Process terminated gracefully")
                except subprocess.TimeoutExpired:
                    logging.warning("Process did not terminate gracefully, killing forcefully")
                    self.current_process.kill()
                    self.current_process.wait()
            except Exception as e:
                logging.exception("Error killing process: %s", e)
            finally:
                self.current_process = None

    def start_stream_playback(self, video_url: str) -> None:
        """Start streaming video playback.

        Args:
            video_url: URL of the video stream to play
        """
        logging.info("Stream active. URL: %s", video_url)

        # Use ffplay for video playback
        play_command = [
            "ffplay",
            "-fs",  # fullscreen
            "-autoexit",  # exit when playback finishes
            "-loglevel",
            "quiet",  # reduce noise
            video_url,
        ]

        logging.info("Executing stream command: %s", " ".join(play_command))

        try:
            self.current_process = subprocess.Popen(play_command)
            logging.debug("Stream process started with PID: %s", self.current_process.pid)
        except FileNotFoundError:
            logging.exception("ffplay not found. Please install ffmpeg to enable video playback.")
        except Exception as e:
            logging.exception("Failed to start stream playback: %s", e)

    def start_image_display(self, image_path: str, image_type: str = "holding") -> None:
        """Start image display.

        Args:
            image_path: Path to the image file
            image_type: Type of image being displayed (for logging)
        """
        if not image_path or not Path(image_path).exists():
            logging.error("Image file not found or not configured: %s", image_path)
            return

        logging.info("Displaying %s image: %s", image_type, image_path)

        # Use ffplay for image display
        image_command = [
            "ffplay",
            "-fs",  # fullscreen
            "-loop",
            "1",  # loop the image indefinitely
            "-loglevel",
            "quiet",  # reduce noise
            image_path,
        ]

        logging.info("Executing image command: %s", " ".join(image_command))

        try:
            self.current_process = subprocess.Popen(image_command)
            logging.debug("Image process started with PID: %s", self.current_process.pid)
        except FileNotFoundError:
            logging.exception("ffplay not found. Please install ffmpeg to enable image display.")
        except Exception as e:
            logging.exception("Failed to start image display: %s", e)

    def handle_mode_change(self, new_mode: str, response_data: dict[str, Any] | None) -> None:
        """Handle switching between different modes.

        Args:
            new_mode: The new mode to switch to
            response_data: API response data (needed for stream mode)
        """
        if new_mode == self.current_mode:
            logging.info("No change in mode (%s)", self.current_mode)
            return

        logging.info("Mode change: %s -> %s", self.current_mode, new_mode)

        # Kill existing process (if any)
        self.kill_current_process()

        # Start new process based on mode
        if new_mode == StreamMode.STREAM and response_data:
            video_url = response_data["m3u8_playback_url"]
            self.start_stream_playback(video_url)
        elif new_mode == StreamMode.API_FAILURE and self.config.api_fail_image_path:
            logging.warning("API instability detected. Displaying failure image.")
            self.start_image_display(self.config.api_fail_image_path, "failure")
        elif new_mode == StreamMode.IMAGE and self.config.holding_image_path:
            logging.warning("Stream not active. Displaying static image.")
            self.start_image_display(self.config.holding_image_path, "holding")
        else:
            logging.warning("Cannot handle mode '%s' - missing configuration or image files", new_mode)

        self.current_mode = new_mode

    def check_process_health(self) -> None:
        """Check if the current process is still running and reset if needed."""
        # If the media player process has ended unexpectedly, reset mode so it will be relaunched
        if self.current_process and self.current_process.poll() is not None:
            exit_code = self.current_process.returncode
            logging.info("Media player process ended (exit code: %s). Resetting mode.", exit_code)
            self.current_process = None
            self.current_mode = None

    def get_process_info(self) -> dict[str, Any]:
        """Get information about the current process.

        Returns:
            Process information dictionary
        """
        info = {
            "current_mode": self.current_mode,
            "has_process": self.current_process is not None,
            "process_running": False,
            "process_pid": None,
        }

        if self.current_process:
            info["process_pid"] = self.current_process.pid
            info["process_running"] = self.current_process.poll() is None

        return info

    def validate_media_paths(self) -> dict[str, bool]:
        """Validate configured media file paths.

        Returns:
            Dictionary of path validation results
        """
        return {
            "holding_image_exists": (
                bool(self.config.holding_image_path) and Path(self.config.holding_image_path).exists()
            ),
            "api_fail_image_exists": (
                bool(self.config.api_fail_image_path) and Path(self.config.api_fail_image_path).exists()
            ),
        }

    def shutdown(self) -> None:
        """Gracefully shutdown the stream manager."""
        logging.info("Shutting down stream manager...")
        self.kill_current_process()
        logging.debug("Stream manager shutdown complete")
