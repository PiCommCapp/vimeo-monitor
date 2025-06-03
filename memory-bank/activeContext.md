# Active Context

## Project Summary

`vimeo-monitor` is a Python-based video kiosk application designed to run on a Raspberry Pi 5. It continuously monitors a Vimeo livestream and displays it on a connected HDMI display. When the stream is not available, it shows a predefined holding image. The system is designed to be resilient and self-healing, automatically recovering from errors and API instability.

## Current Implementation Status

The core application is functional with the following components:

- Python-based polling mechanism to check Vimeo API status
- State machine to handle transitions between stream and image modes
- Process management for media players
- Logging system for diagnostic information
- Error handling for API and network failures
- Systemd service for automatic startup

## Key Technical Characteristics

- **Language & Runtime**: Python 3.12+ with `uv` package management
- **Media Players**:
  - `cvlc` for HLS video stream playback
  - `ffplay` for fallback image display
- **Configuration**: Environment variables via `.env` file
- **Deployment**: Systemd service on Raspberry Pi OS

## Current Functionality

The application can:

- Poll the Vimeo API to check stream status
- Play HLS livestreams in full-screen mode
- Display fallback images when streams are unavailable
- Automatically recover from process failures
- Log activity and errors
- Start automatically on system boot

## Pending Enhancements

Based on the project brief, several enhancements are planned:

- Log rotation mechanism
- Remote configuration synchronization
- GUI settings panel
- HDMI CEC integration for display control
- Remote diagnostics via MQTT or WebSockets

## Immediate Focus Areas

The primary focus areas for immediate development are:

1. Robust error handling for network and API failures
2. Improved logging and diagnostics
3. Testing in various failure scenarios
4. Documentation for deployment and configuration

## Environmental Constraints

The application operates within these constraints:

- Must run on Raspberry Pi hardware
- Requires X11 desktop environment
- Needs persistent network connection for streaming
- Requires appropriate media players installed
- Must operate with minimal user intervention
