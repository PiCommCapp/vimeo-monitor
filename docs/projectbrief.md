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

- Continuously polls the Vimeo API using `VIMEO_ACCESS_TOKEN` and `VIMEO_VIDEO_ID`
- When a valid livestream is found, plays it in full-screen mode with audio
- If no stream is active, displays the defined `HOLDING_IMAGE`
- If API is unreachable or behaving erratically (e.g., frequent state changes), shows a separate `API_FAIL_IMAGE`
- Automatically transitions between stream and holding image based on availability
- Monitors internal health to detect stalled video player or blank screen conditions, and reinitialises as needed
- Optionally overlays network connectivity status on screen

## Configuration (`.env` example)

```env
VIMEO_TOKEN="secrettoken"
VIMEO_KEY="secretkey"
VIMEO_SECRET="secretsecret"
VIMEO_STREAM_ID=streamid
LOG_LEVEL="INFO"
LOG_FILE=./logs/vimeo_monitor.logs

CHECK_INTERVAL=30  # in seconds

HOLDING_IMAGE_PATH=/home/pi/kiosk/holding.jpg
API_FAIL_IMAGE_PATH=/home/pi/kiosk/failure.jpg

DISPLAY_NETWORK_STATUS=true  # Toggleable on-screen overlay
```

## Technical Architecture

- **Language**: Python 3.x
- **Runtime**: `uv` runner (`uv run -m vimeo_monitor.monitor`)
- **Environment**: Raspberry Pi OS Desktop (X11)
- **Playback Backend**: Currently using `ffplay` or `mpv`
- **UI Layer**: X11 fullscreen window for images and video

## Auto Launch (Systemd Service)

A systemd service will handle auto-launch:

```
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
  - Counts rapid success/fail switches and locks into failover mode
  - Displays `API_FAIL_IMAGE_PATH` holding image
  - Continues polling API in the background
  - Returns to normal flow once API stabilises
- **Network Drop**: Network status displayed (if enabled), retry attempts continue in background

## Future Enhancements

- [ ] Log Rotation: Implement `logrotate` or internal rotation mechanism
- [ ] Remote Config Sync: Optionally pull `.env` from secure central server
- [ ] GUI Settings Panel (via Tk or PyQT)
- [ ] HDMI CEC integration for screen control
- [ ] MQTT or WebSocket interface for live diagnostics or control

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

TBD — proposed MIT or GPLv3
