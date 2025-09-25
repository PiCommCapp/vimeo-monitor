#!/usr/bin/env python3

import json
import logging
import os
import subprocess
import sys

from dotenv import load_dotenv
from vimeo import VimeoClient

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    # Vimeo API client setup
    client = VimeoClient(
        token=os.getenv("VIMEO_TOKEN"),
        key=os.getenv("VIMEO_KEY"),
        secret=os.getenv("VIMEO_SECRET"),
    )

    # Test API URL
    test_url = "https://api.vimeo.com/me/live_events/4797083/m3u8_playback"

    # Retrieve stream URL
    logger.info(f"Fetching stream data from: {test_url}")
    response = client.get(test_url)

    if response.status_code != 200:
        logger.error(f"API request failed with status code: {response.status_code}")
        sys.exit(1)

    # Print Stream URL
    print("Stream URL:")
    stream_response = response.json()
    print(json.dumps(stream_response, indent=2))

    hls = stream_response.get("m3u8_playback_url")

    if not hls:
        logger.error("No m3u8_playback_url found in response")
        sys.exit(1)

    logger.info(f"Using HLS URL: {hls}")

    # FFprobe command
    logger.info("Running ffprobe analysis...")
    stream_data = subprocess.run([
        "ffprobe",
        "-v",
        "info",
        "-print_format", "json",
        "-show_streams",
        "-show_format",
        "-timeout",
        "5000000",
        hls
        ], capture_output=True, text=True, check=True)

    # Parse and print FFprobe result
    ffprobe_result = json.loads(stream_data.stdout)

    print("FFprobe result:")
    print(json.dumps(ffprobe_result, indent=2))

except subprocess.CalledProcessError as e:
    logger.error(f"FFprobe failed with return code {e.returncode}")
    logger.error(f"Error output: {e.stderr}")
    sys.exit(1)
except json.JSONDecodeError as e:
    logger.error(f"Failed to parse JSON response: {e}")
    sys.exit(1)
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    sys.exit(1)
