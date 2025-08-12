# vimeo-monitor — Project Brief

## Overview

`vimeo-monitor` is a self-launching Python-based video kiosk designed to run on a Raspberry Pi 5 under a desktop X11 environment. It polls the Vimeo API to retrieve and play a secure HLS livestream using a local HDMI display with audio. When the stream is unavailable or the API is unstable, a defined holding image or failure slide is shown instead. The application is designed to be robust, fault-tolerant, and "self-healing" to recover from errors or API instability without user intervention.

## Key Features

- 🎥 Auto-play HLS stream retrieved securely from Vimeo API
- 🖼 Displays a defined holding image when stream is offline
- 🚫 Displays a failure image if the Vimeo API is unstable
- 🔄 Continual monitoring of stream/API state with automatic switching
- 🧠 Self-healing: Restarts the player or display state if stalled
- 📶 Optional on-screen network status display (toggleable)
- 📡 HDMI video and audio output
- 🔐 Secure `.env`-based credential and configuration management
- 🚀 Launches automatically via `systemd` service on boot
- 🔄 Simple update path via `git pull` + reboot
- 🖥 Operates in a windowing environment (X11) on Raspberry Pi 5

## Runtime Behaviour

- Continuously polls the Vimeo API using `VIMEO_ACCESS_TOKEN` `VIMEO_ACCESS_KEY` `VIMEO_ACCESS_SECRET` and `VIMEO_VIDEO_ID`
- When a valid livestream is found, plays it in full-screen mode with audio
- If no stream is active, displays the defined `HOLDING_IMAGE`
- If API is unreachable or behaving erratically (e.g., frequent state changes), shows a separate `API_FAIL_IMAGE`
- Automatically transitions between stream and holding image based on availability
- Monitors internal health to detect stalled video player or blank screen conditions, and reinitialises as needed
- Optionally overlays network connectivity status on screen

## Working Script, Basic, to be Improved

```py
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
```

## Technical Architecture

- **Language**: Python 3.x
- **Runtime**: `uv` runner (`uv run -m vimeo_monitor.monitor`)
- **Environment**: Raspberry Pi OS Desktop (X11)
- **Playback Backend**: Currently using `ffplay` or `mpv`
- **UI Layer**: X11 fullscreen window for images and video

## Auto Launch (Systemd Service)

A systemd service will handle auto-launch:

```bash
[Unit]
Description=Vimeo Monitor Kiosk
After=network-online.target

[Service]
ExecStart=/usr/bin/uv run -m vimeo_monitor.monitor
WorkingDirectory=/home/pi/vimeo-monitor
EnvironmentFile=/home/pi/vimeo-monitor/.env
Restart=always
RestartSec=5
User=pi
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/pi/.Xauthority

[Install]
WantedBy=graphical.target
```

> Systemd unit can be generated from a Jinja2 template if customisation is needed per deployment.

## Fault Handling Logic

- **Player Stalls**: Watchdog checks for stale or non-responsive player and restarts playback
- **API Failures**:
  - Tracks consecutive failures using configurable threshold
  - Implements exponential backoff for reconnection attempts
  - Displays dedicated `API_FAIL_IMAGE_PATH` when in failure mode
  - Provides detailed error logging with specific exception handling
  - Requires a configurable number of consecutive successful responses before exiting failure mode
  - Returns to normal flow once API stabilizes
- **Network Drop**: Network status displayed (if enabled), retry attempts continue in background

## API Failure State Machine

The application implements a three-state machine for handling different operational conditions:

```bash
                    Error Count ≥ Threshold
                    ┌────────────────────┐
                    │                    │
                    ▼                    │
┌──────────┐     ┌───────────┐     ┌────────────┐
│  Stream  │────▶│ No Stream │────▶│ API Failure │
│   Mode   │◀────│    Mode   │◀────│    Mode     │
└──────────┘     └───────────┘     └────────────┘
                    ▲                    │
                    │                    │
                    └────────────────────┘
                    Success Count ≥ Threshold
```

## Future Enhancements

- [ ] Log Rotation: Implement `logrotate` or internal rotation mechanism
- [ ] Remote Config Sync: Optionally pull `.env` from secure central server
- [ ] GUI Settings Panel (via Tk or PyQT)
- [ ] HDMI CEC integration for screen control
- [ ] Prometheus Metrics: HTTP `/metrics` endpoint for monitoring system health
- [ ] Dynamic status display on failure image
- [ ] Error type-specific recovery strategies
- [ ] Admin notifications for critical errors

## Update Procedure

```sh
cd /home/pi/vimeo-monitor
git pull
sudo reboot
```

## Management

- Primarily accessed via SSH
- Runs in X11 desktop session on boot
- Admin override (e.g. `CTRL+C` or service stop) for exit

## Licence

MIT License
