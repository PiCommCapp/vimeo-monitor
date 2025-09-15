# Installation Guide

## Prerequisites

Make sure you have these installed:
- Python 3.12 or newer
- VLC media player (`cvlc` command)
- FFmpeg (`ffplay` command)

### Install VLC and FFmpeg

```bash
sudo apt update
sudo apt install vlc ffmpeg
```

## Installation Steps

### 1. Get the Code

```bash
git clone <your-repo-url>
cd vimeo-monitor
```

### 2. Install Dependencies

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync
```

### 3. Configuration

Create a `.env` file in the project root:

```bash
cp .env.sample .env
```

Edit `.env` with your Vimeo API credentials:

```bash
VIMEO_TOKEN=your_token_here
VIMEO_KEY=your_key_here
VIMEO_SECRET=your_secret_here
STATIC_IMAGE_PATH=media/holding.png
ERROR_IMAGE_PATH=media/failure.png
```

### 4. Add Required Images

Make sure these image files exist:
- `media/holding.png` - shown when stream is offline
- `media/failure.png` - shown when there's an error

### 5. Test the Installation

```bash
# Run a quick test
uv run streammonitor.py
```

If it starts without errors, you're ready to go!

## Auto-Start Setup (Optional)

To start automatically when the Pi boots:

```bash
# Copy desktop files to autostart
cp install/streamreturn.desktop ~/.config/autostart/
cp install/xrandr.desktop ~/.config/autostart/
```

## Running the Monitor

```bash
# Start the monitor
uv run streammonitor.py

# Or use the Makefile
make run
```

## What Happens Next

1. The system checks your Vimeo stream every few seconds
2. If stream is offline: shows `holding.png`
3. If stream is live: shows full-screen video
4. If there's an error: shows `failure.png`
5. Automatically restarts if something goes wrong

## Next Steps

- [Troubleshooting Guide](troubleshooting.md) - if something goes wrong
- [Home](index.md) - back to overview
