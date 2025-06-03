#!/usr/bin/env python3

import os
import time
import subprocess
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from vimeo import VimeoClient  # type: ignore[import-untyped]
from requests.exceptions import RequestException

# Load environment variables from .env file
load_dotenv()

# Global variables for API failure tracking
api_failure_count = 0
api_success_count = 0
api_failure_mode = False
last_api_error: Optional[str] = None
api_retry_interval = int(os.getenv("API_MIN_RETRY_INTERVAL", "10"))

# Constants from environment
API_FAILURE_THRESHOLD = int(os.getenv("API_FAILURE_THRESHOLD", "3"))
API_STABILITY_THRESHOLD = int(os.getenv("API_STABILITY_THRESHOLD", "5"))
API_MIN_RETRY_INTERVAL = int(os.getenv("API_MIN_RETRY_INTERVAL", "10"))
API_MAX_RETRY_INTERVAL = int(os.getenv("API_MAX_RETRY_INTERVAL", "300"))
API_ENABLE_BACKOFF = os.getenv("API_ENABLE_BACKOFF", "true").lower() == "true"

# Vimeo API configuration
VIMEO_TOKEN = os.getenv("VIMEO_TOKEN")
VIMEO_KEY = os.getenv("VIMEO_KEY")
VIMEO_SECRET = os.getenv("VIMEO_SECRET")
VIMEO_STREAM_ID = os.getenv("VIMEO_STREAM_ID")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "30"))

# Image paths
HOLDING_IMAGE_PATH = os.getenv("HOLDING_IMAGE_PATH")
API_FAIL_IMAGE_PATH = os.getenv("API_FAIL_IMAGE_PATH")

# Vimeo API client setup (original authentication method)
client = VimeoClient(
    token=VIMEO_TOKEN,
    key=VIMEO_KEY,
    secret=VIMEO_SECRET,
)

# Global variables for process management
keep_looping = True
current_process: Optional[subprocess.Popen[bytes]] = None
current_mode: Optional[str] = None


def setup_logging() -> None:
    """Configure logging with proper error handling."""
    log_file = os.getenv("LOG_FILE", "./logs/vimeo_monitor.logs")
    log_level = os.getenv("LOG_LEVEL", "INFO")

    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure logging with proper handler types
    handlers: list[logging.Handler] = [logging.StreamHandler()]

    # Only add file handler if LOG_FILE is specified
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


def validate_configuration() -> bool:
    """Validate required configuration is present."""
    required_vars = {
        "VIMEO_TOKEN": VIMEO_TOKEN,
        "VIMEO_KEY": VIMEO_KEY,
        "VIMEO_SECRET": VIMEO_SECRET,
        "VIMEO_STREAM_ID": VIMEO_STREAM_ID,
    }

    missing_vars = [var for var, value in required_vars.items() if not value]

    if missing_vars:
        logging.error("Missing required environment variables: %s", ", ".join(missing_vars))
        return False

    # Validate image paths if specified
    if HOLDING_IMAGE_PATH and not Path(HOLDING_IMAGE_PATH).exists():
        logging.warning("HOLDING_IMAGE_PATH specified but file does not exist: %s", HOLDING_IMAGE_PATH)

    if API_FAIL_IMAGE_PATH and not Path(API_FAIL_IMAGE_PATH).exists():
        logging.warning("API_FAIL_IMAGE_PATH specified but file does not exist: %s", API_FAIL_IMAGE_PATH)

    return True


def calculate_backoff(current_interval: int) -> int:
    """Calculate the next retry interval using exponential backoff."""
    if not API_ENABLE_BACKOFF:
        return API_MIN_RETRY_INTERVAL

    # Double the current interval
    next_interval = current_interval * 2

    # Cap at maximum
    return min(next_interval, API_MAX_RETRY_INTERVAL)


def handle_api_failure(error_type: str, error_message: str) -> None:
    """Handle API failures and track consecutive failures."""
    global api_failure_count, api_success_count, api_failure_mode, last_api_error

    # Reset success counter and increment failure counter
    api_success_count = 0
    api_failure_count += 1
    last_api_error = error_type

    logging.error("API failure (%s): %s. Consecutive failures: %d",
                 error_type, error_message, api_failure_count)

    # Check if we should enter failure mode
    if api_failure_count >= API_FAILURE_THRESHOLD:
        if not api_failure_mode:
            logging.warning("Entering API failure mode after %d consecutive failures",
                           api_failure_count)
            api_failure_mode = True


def handle_api_success() -> None:
    """Handle successful API responses and track consecutive successes."""
    global api_failure_count, api_success_count, api_failure_mode, api_retry_interval

    # Reset failure counter and increment success counter
    api_failure_count = 0
    api_success_count += 1

    # If we're in failure mode, check if we should exit
    if api_failure_mode and api_success_count >= API_STABILITY_THRESHOLD:
        logging.info("Exiting API failure mode after %d consecutive successes",
                   api_success_count)
        api_failure_mode = False
        api_retry_interval = API_MIN_RETRY_INTERVAL  # Reset backoff timer


def get_vimeo_stream_data() -> Optional[Dict[str, Any]]:
    """Fetch stream data from Vimeo API using original authentication method."""
    if not VIMEO_STREAM_ID:
        logging.error("No valid stream ID found for selection: %s", VIMEO_STREAM_ID)
        return None

    # Build the Vimeo API request URL (original method)
    stream_url = f"https://api.vimeo.com/me/live_events/{VIMEO_STREAM_ID}/m3u8_playback"

    try:
        # Request JSON data using VimeoClient (original method)
        response = client.get(stream_url)  # type: ignore[misc]
        response_data = response.json()

        # Add debug logging for the API response
        logging.debug("Vimeo API Response: %s", response_data)

        handle_api_success()
        return response_data

    except RequestException as e:
        handle_api_failure("network", str(e))
        logging.debug("Full error details:", exc_info=True)
    except Exception as e:
        handle_api_failure("unknown", str(e))
        logging.exception("Unexpected error:")

    return None


def kill_current_process() -> None:
    """Kill the current media player process."""
    global current_process

    if current_process and current_process.poll() is None:
        logging.info("Killing current media player process")
        try:
            current_process.terminate()
            # Give process time to terminate gracefully
            try:
                current_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                current_process.kill()
                current_process.wait()
        except Exception as e:
            logging.error("Error killing process: %s", e)
        finally:
            current_process = None


def start_stream_playback(video_url: str) -> None:
    """Start streaming video playback."""
    global current_process

    logging.info("Stream active. URL: %s", video_url)

    # Use ffplay as in original (keeping original player choice)
    play_command = [
        "ffplay",
        "-fs",           # fullscreen
        "-autoexit",     # exit when playback finishes
        "-loglevel", "quiet",  # reduce noise
        video_url
    ]

    logging.info("Executing stream command: %s", " ".join(play_command))

    try:
        current_process = subprocess.Popen(play_command)
    except Exception as e:
        logging.error("Failed to start stream playback: %s", e)


def start_image_display(image_path: str, image_type: str = "holding") -> None:
    """Start image display."""
    global current_process

    if not image_path or not Path(image_path).exists():
        logging.error("Image file not found or not configured: %s", image_path)
        return

    logging.info("Displaying %s image: %s", image_type, image_path)

    # Use ffplay as in original script
    image_command = [
        "ffplay",
        "-fs",           # fullscreen
        "-loop", "1",    # loop the image indefinitely
        "-loglevel", "quiet",  # reduce noise
        image_path
    ]

    logging.info("Executing image command: %s", " ".join(image_command))

    try:
        current_process = subprocess.Popen(image_command)
    except Exception as e:
        logging.error("Failed to start image display: %s", e)


def determine_mode(response_data: Optional[Dict[str, Any]]) -> str:
    """Determine which mode to run based on API response and failure state."""
    if api_failure_mode:
        return "api_failure"
    elif response_data and "m3u8_playback_url" in response_data:
        logging.debug("Found m3u8_playback_url in response")
        return "stream"
    else:
        logging.debug("No m3u8_playback_url found in response. Full response: %s", response_data)
        return "image"


def handle_mode_change(new_mode: str, response_data: Optional[Dict[str, Any]]) -> None:
    """Handle switching between different modes."""
    global current_mode

    if new_mode == current_mode:
        logging.info("No change in mode (%s)", current_mode)
        return

    logging.info("Mode change: %s -> %s", current_mode, new_mode)

    # Kill existing process (if any)
    kill_current_process()

    # Start new process based on mode
    if new_mode == "stream" and response_data:
        video_url = response_data["m3u8_playback_url"]
        start_stream_playback(video_url)
    elif new_mode == "api_failure" and API_FAIL_IMAGE_PATH:
        logging.warning("API instability detected. Displaying failure image.")
        start_image_display(API_FAIL_IMAGE_PATH, "failure")
    elif new_mode == "image" and HOLDING_IMAGE_PATH:
        logging.warning("Stream not active. Displaying static image.")
        start_image_display(HOLDING_IMAGE_PATH, "holding")
    else:
        logging.warning("Cannot handle mode '%s' - missing configuration or image files", new_mode)

    current_mode = new_mode


def check_process_health() -> None:
    """Check if the current process is still running and reset if needed."""
    global current_process, current_mode

    # If the media player process has ended unexpectedly, reset mode so it will be relaunched in the next loop
    if current_process and current_process.poll() is not None:
        logging.info("Media player process ended unexpectedly. Resetting mode.")
        current_process = None
        current_mode = None


def main() -> None:
    """Main application loop."""
    global keep_looping, api_retry_interval

    setup_logging()

    if not validate_configuration():
        logging.error("Configuration validation failed. Exiting.")
        sys.exit(1)

    logging.info("Starting Vimeo stream monitor...")
    logging.info("Configuration: Stream ID: %s, Check interval: %ds",
                VIMEO_STREAM_ID, CHECK_INTERVAL)

    try:
        while keep_looping:
            try:
                # Get stream data from API
                response_data = get_vimeo_stream_data()

                # Determine mode based on response and failure state
                new_mode = determine_mode(response_data)

                # Handle mode changes
                handle_mode_change(new_mode, response_data)

                # Check if current process is still healthy
                check_process_health()

                # Wait before next check
                if api_failure_mode:
                    logging.info("In API failure mode. Waiting %d seconds before retry...", api_retry_interval)
                    time.sleep(api_retry_interval)
                    api_retry_interval = calculate_backoff(api_retry_interval)
                else:
                    time.sleep(CHECK_INTERVAL)

            except KeyboardInterrupt:
                logging.info("Received interrupt signal. Shutting down...")
                keep_looping = False
            except Exception as e:
                logging.error("Unexpected error in main loop: %s", e)
                logging.exception("Full traceback:")
                time.sleep(CHECK_INTERVAL)

    finally:
        # Clean shutdown
        kill_current_process()
        logging.info("Vimeo stream monitor stopped.")


if __name__ == "__main__":
    main()