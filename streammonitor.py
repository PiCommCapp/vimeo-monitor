#!/usr/bin/env python3

import os
import time
import subprocess
import logging
from vimeo import VimeoClient
from requests.exceptions import RequestException

# Configure logging
LOG_FILE = '/home/admin/code/stream_monitor.log'  # Adjust this path as needed
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()  # This will continue logging to stdout
    ]
)

# Define the path to your static PNG image
STATIC_IMAGE_PATH = '/home/admin/content/OffAirCard.png'

# Select stream (change this value if needed)
STREAM_SELECTION = 1

# Stream IDs from Vimeo
STREAMS = {
    1: "4797083",
    2: "4797121",
    3: "4898539",
    4: "4797153",
    5: "4797202",
    6: "4797207"
}

# Vimeo API client setup
client = VimeoClient(
    token="7663b2aa4b567f2328f63d39040ca323",
    key="5648ce3018f4faee5cf4fadf9fabdc2127f1118e",
    secret="CaGlGOZpbytHfzewapGuJ0801pf4vpbwMsCctPUJ6T955DDhA5xyn7SUX1SdkXloCUE4MIRCFlgqLCekV5UrF7uc+fWXmwFgvXOnnk+ConYZHHgnZ/z9Y6tNxGE9bBuc",
)

# Global variables for process management
keep_looping = True
current_process = None
current_mode = None

logging.info("Starting Vimeo stream monitor...")

while keep_looping:
    try:
        stream_id = STREAMS.get(STREAM_SELECTION)
        if not stream_id:
            logging.error("No valid stream ID found for selection: %s", STREAM_SELECTION)
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
                ffplay_command = [
#                    "ffplay",
#                    "-fs",
#                    "-framedrop",
#                    "-x", "854",
#                    "-y", "480",
#                    "-max_delay", "10000000",
#                    "-rtbufsize", "50M",
#                    "-volume", "100",
#                    "-probesize", "32",
#                    "-analyzeduration", "0",
#                    "-fflags", "nobuffer",
#                    "-flags", "low_delay",
#                    "-strict", "experimental",
#                    "-tune", "zerolatency",
#                    "-preset", "ultrafast",
#                    "-vst", "2",
#                    "-ast", "1",
#                    video_url
#                ]
		     "cvlc",
		     "-f",
		     video_url
		 ]
                logging.info("Executing ffplay command for stream: %s", " ".join(ffplay_command))
                current_process = subprocess.Popen(ffplay_command)
            else:
                logging.warning("Stream not active. Displaying static image.")
                image_command = [
                    "ffplay",
                    "-fs",
                    "-loop", "1",  # loop the image indefinitely
                    STATIC_IMAGE_PATH
                ]
                logging.info("Executing ffplay command for static image: %s", " ".join(image_command))
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