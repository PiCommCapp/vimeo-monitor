#!/usr/bin/env python3

import os
import time
import subprocess
import logging
from vimeo import VimeoClient
from requests.exceptions import RequestException

# Configure logging
LOG_FILE = os.getenv("LOG_FILE")
LOG_LEVEL = os.getenv("LOG_LEVEL")
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()  # This will continue logging to stdout
    ]
)

# Define the path to your static PNG image
STATIC_IMAGE_PATH = os.getenv("STATIC_IMAGE_PATH")

# Vimeo API client setup
client = VimeoClient(
    token=os.getenv("VIMEO_TOKEN"),
    key=os.getenv("VIMEO_KEY"),
    secret=os.getenv("VIMEO_SECRET"),
)

# Global variables for process management
keep_looping = True
current_process = None
current_mode = None

logging.info("Starting Vimeo stream monitor...")

while keep_looping:
    try:
        stream_id = os.getenv("VIMEO_STREAM_ID")
        if not stream_id:
            logging.error("No valid stream ID found for selection: %s", stream_id)
            break

        # Build the Vimeo API request URL
        stream_url = f"https://api.vimeo.com/me/live_events/{stream_id}/m3u8_playback"

        # Request JSON data
        response = client.get(stream_url)
        response_data = response.json()
        
        # Add debug logging for the API response
        logging.debug("Vimeo API Response: %s", response_data)

        # Determine which mode to run
        if "m3u8_playback_url" in response_data:
            new_mode = "stream"
            logging.debug("Found m3u8_playback_url in response")
        else:
            new_mode = "image"
            logging.debug("No m3u8_playback_url found in response. Full response: %s", response_data)

        # If the mode has changed, kill the existing ffplay process (if any)
        if new_mode != current_mode:
            if current_process and current_process.poll() is None:
                logging.info("Killing current ffplay process to switch mode.")
                current_process.kill()
                current_process = None

            if new_mode == "stream":
                video_url = response_data["m3u8_playback_url"]
                logging.info("Stream active. URL: %s", video_url)
                play_command = [
		     "cvlc",
		     "-f",
		     video_url
		 ]
                logging.info("Executing ffplay command for stream: %s", " ".join(play_command))
                current_process = subprocess.Popen(play_command)
            else:
                logging.warning("Stream not active. Displaying static image.")
                image_command = [
                    "ffplay",
                    "-fs",
                    "-loop", "1",  # loop the image indefinitely
                    STATIC_IMAGE_PATH
                ]
                logging.info("Executing play command for static image: %s", " ".join(image_command))
                current_process = subprocess.Popen(image_command)
            
            current_mode = new_mode
        else:
            logging.info("No change in mode (%s).", current_mode)
    except RequestException as e:
        logging.error("Network error: %s", str(e))
        logging.debug("Full error details:", exc_info=True)  # This will log the full traceback

    # Wait for 10 seconds before rechecking
    time.sleep(10)

    # If the ffplay process has ended unexpectedly, reset mode so it will be relaunched in the next loop
    if current_process and current_process.poll() is not None:
        logging.info("ffplay process ended. Resetting mode.")
        current_mode = None
        current_process = None

logging.info("Exiting stream monitor script.")