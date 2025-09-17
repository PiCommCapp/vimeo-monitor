#!/usr/bin/env python3

import os
import time
import subprocess
import logging
from dotenv import load_dotenv
from vimeo import VimeoClient

# Load environment variables
load_dotenv()

# Vimeo API client setup
client = VimeoClient(
    token=os.getenv("VIMEO_TOKEN"),
    key=os.getenv("VIMEO_KEY"),
    secret=os.getenv("VIMEO_SECRET"),
)

# Test API URL
test_url = "https://api.vimeo.com/me/live_events/4797083/m3u8_playback"

# Retrieve stream URL
response = client.get(test_url)

# Print Stream URL
print("Stream URL:")
print(response.json())

# FFprobe command
stream_data = subprocess.run(["ffprobe", "-v", "info", "-print_format", "json", "-show_format", "-show_streams", "-timeout", "5000000", response.json(m3u8_playback_url)])

# Print FFprobe result
print("FFprobe result:")
print(stream_data)