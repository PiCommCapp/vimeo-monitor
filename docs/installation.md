# Installation Guide

Complete installation instructions for the Vimeo Monitor system.

## Prerequisites

### System Requirements
- **OS**: Linux (tested on Raspberry Pi OS, Ubuntu 22.04+)
- **Python**: 3.12 or newer
- **Memory**: 512MB RAM minimum, 1GB recommended
- **Storage**: 100MB free space minimum, 500MB recommended
- **Network**: Stable internet connection

### Required Software
- **VLC Media Player**: For video playback
- **FFmpeg**: For stream analysis and media processing
- **Git**: For cloning the repository

## Installation Steps

### Step 1: Install System Dependencies

#### Ubuntu/Debian/Raspberry Pi OS
```bash
# Update package lists
sudo apt update

# Install required packages
sudo apt install vlc ffmpeg git python3 python3-pip

# Verify installations
which vlc
which cvlc
which ffplay
which ffprobe
```

#### Other Linux Distributions
```bash
# For CentOS/RHEL/Fedora
sudo yum install vlc ffmpeg git python3 python3-pip

# For Arch Linux
sudo pacman -S vlc ffmpeg git python python-pip
```

### Step 2: Install Python Package Manager

```bash
# Install uv (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Reload shell or source profile
source ~/.bashrc

# Verify installation
uv --version
```

### Step 3: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/PiCommCapp/vimeo-monitor.git
cd vimeo-monitor

# Verify repository structure
ls -la
```

### Step 4: Install Python Dependencies

```bash
# Install all dependencies
uv sync

# Verify installation
uv run python --version
uv run python -c "import vimeo_monitor; print('Installation successful')"
```

### Step 5: Configure Environment

```bash
# Copy environment template
cp .env.sample .env

# Edit configuration
nano .env
```

#### Required Configuration
```bash
# Vimeo API Credentials (required)
VIMEO_ACCESS_TOKEN=your_vimeo_access_token_here
VIMEO_CLIENT_ID=your_vimeo_client_id_here
VIMEO_CLIENT_SECRET=your_vimeo_client_secret_here

# Stream Configuration (required)
VIMEO_STREAM_ID=your_stream_id_here
STREAM_CHECK_INTERVAL=30
```

#### Optional Configuration
```bash
# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/vimeo_monitor.log

# Process Management
PROCESS_RESTART_DELAY=5
PROCESS_MAX_RESTARTS=10

# Health Monitoring (optional)
HEALTH_MONITORING_ENABLED=false
HEALTH_METRICS_PORT=8080
HEALTH_METRICS_HOST=0.0.0.0
```

### Step 6: Prepare Media Files

```bash
# Create media directory
mkdir -p media

# Add required images
# - holding.png: Shown when stream is offline
# - failure.png: Shown when there's an error

# Example: Copy your images
cp your_holding_image.png media/holding.png
cp your_failure_image.png media/failure.png

# Verify media files
ls -la media/
```

### Step 7: Test Installation

```bash
# Test configuration validation
uv run python -c "from src.vimeo_monitor.config import Config; print('Configuration valid')"

# Test basic functionality
uv run python -c "from src.vimeo_monitor.monitor import Monitor; print('Monitor module loaded')"

# Run a quick test
uv run python -m vimeo_monitor --help
```

## Auto-Start Setup (Optional)

### Desktop Environment (Raspberry Pi OS)
```bash
# Copy desktop files to autostart
cp install/streamreturn.desktop ~/.config/autostart/
cp install/xrandr.desktop ~/.config/autostart/

# Verify autostart files
ls -la ~/.config/autostart/
```

### Systemd Service (Advanced)
```bash
# Create systemd service file
sudo nano /etc/systemd/system/vimeo-monitor.service

# Add service configuration
[Unit]
Description=Vimeo Monitor
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/vimeo-monitor
ExecStart=/home/pi/vimeo-monitor/.venv/bin/python -m vimeo_monitor
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable vimeo-monitor
sudo systemctl start vimeo-monitor
```

## Verification

### Check Installation
```bash
# Verify all components
uv run python -c "
from src.vimeo_monitor.config import Config
from src.vimeo_monitor.monitor import Monitor
from src.vimeo_monitor.process_manager import ProcessManager
print('All modules loaded successfully')
"

# Check configuration
uv run python -c "
from src.vimeo_monitor.config import Config
config = Config()
print(f'Stream ID: {config.vimeo_stream_id}')
print(f'Check Interval: {config.stream_check_interval}s')
"
```

### Test Stream Detection
```bash
# Test Vimeo API connection
uv run python -c "
from src.vimeo_monitor.monitor import Monitor
from src.vimeo_monitor.config import Config
config = Config()
monitor = Monitor(config)
status = monitor.check_stream_status()
print(f'Stream status: {status}')
"
```

### Test Video Playback
```bash
# Test VLC installation
cvlc --version

# Test FFmpeg installation
ffplay --version

# Test with static image
ffplay -fs -loop 1 media/holding.png
```

## Troubleshooting

### Common Installation Issues

#### Python Version Issues
```bash
# Check Python version
python3 --version

# If Python 3.12+ not available, install it
sudo apt install python3.12 python3.12-venv python3.12-dev
```

#### VLC Installation Issues
```bash
# Check VLC installation
which vlc
which cvlc

# If missing, reinstall
sudo apt remove vlc
sudo apt update
sudo apt install vlc

# Verify command line tools
cvlc --version
```

#### FFmpeg Installation Issues
```bash
# Check FFmpeg installation
which ffmpeg
which ffplay
which ffprobe

# If missing, reinstall
sudo apt remove ffmpeg
sudo apt update
sudo apt install ffmpeg

# Verify installation
ffmpeg -version
```

#### Permission Issues
```bash
# Fix file permissions
chmod 755 logs/
chmod 644 media/*.png
chmod 600 .env

# Fix ownership
chown -R $USER:$USER .
```

### Getting Help

- Check the [Troubleshooting Guide](troubleshooting.md) for detailed solutions
- Review the [Configuration Guide](configuration.md) for all available options
- Check system logs: `tail -f logs/vimeo_monitor.log`

## Next Steps

Once installation is complete:

1. **Configure System**: Set up your Vimeo API credentials
2. **Test Functionality**: Run the system and verify it works
3. **Set Up Monitoring**: Enable health monitoring if desired
4. **Automate Startup**: Configure auto-start for production use

## Related Documentation

- **[Quick Start](quick-start.md)** - Step-by-step setup guide
- **[Configuration](configuration.md)** - Complete configuration reference
- **[Basic Usage](usage.md)** - How to use the system
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions
- **[Health Monitoring](health-monitoring.md)** - Monitoring and metrics