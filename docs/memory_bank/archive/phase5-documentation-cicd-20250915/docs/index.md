# Vimeo Monitor

A system that monitors Vimeo live streams and displays them full-screen on a Raspberry Pi.

## What It Does

- Connects to Vimeo API to check if your stream is live
- Shows a holding image when stream is offline
- Displays full-screen video when stream is live
- Automatically switches between modes as needed
- Restarts automatically if something goes wrong

## Requirements

- Raspberry Pi (or Linux computer)
- Python 3.12 or newer
- VLC media player
- FFmpeg
- Vimeo API credentials

## Quick Start

1. [Install the system](installation.md)
2. [Configure your Vimeo credentials](installation.md#3-configuration)
3. Run the monitor
4. [Troubleshoot any issues](troubleshooting.md)

## Getting Help

- **Installation problems?** → [Installation Guide](installation.md)
- **Something not working?** → [Troubleshooting Guide](troubleshooting.md)
- **Need to understand what it does?** → You're reading it!

## Files You Need

- `.env` file with your Vimeo API credentials
- `media/holding.png` - image shown when stream is offline
- `media/failure.png` - image shown when there's an error