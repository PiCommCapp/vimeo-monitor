# vimeo-monitor

A robust, self-healing video kiosk application for Raspberry Pi that displays Vimeo livestreams with intelligent fallback mechanisms.

## Overview

`vimeo-monitor` is designed to reliably display Vimeo livestreams on a Raspberry Pi with minimal supervision. It automatically handles API failures, network instability, and playback issues while providing clear visual feedback about the current system state.

![State Machine](docs/images/state-machine.png)

## Features

- **Reliable Livestream Display**: Auto-plays HLS streams from Vimeo with audio
- **Intelligent Fallbacks**:
  - Shows a holding image when no stream is available
  - Displays a dedicated failure image when the API is unstable
  - Implements exponential backoff for reconnection attempts
- **Self-Healing**: Automatically recovers from failures without manual intervention
- **Detailed Diagnostics**: Specific error handling and comprehensive logging
- **Easy Deployment**: Simple installation and configuration process
- **Low Maintenance**: Designed for "set and forget" operation

## Installation

### Prerequisites

- Raspberry Pi 5 (or 4 with sufficient RAM)
- Raspberry Pi OS Desktop (with X11)
- Python 3.9+
- Network connectivity

### Basic Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/vimeo-monitor.git
   cd vimeo-monitor
   ```

2. Create a virtual environment and install dependencies:

   ```bash
   make install
   # or manually:
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

3. Create your configuration:

   ```bash
   cp .env.sample .env
   # Edit .env with your Vimeo API credentials and configuration
   ```

4. Test the application:

   ```bash
   uv run -m vimeo_monitor.monitor
   ```

### Production Deployment

For production deployment on a Raspberry Pi, set up the application to run automatically on boot:

1. Copy the systemd service file:

   ```bash
   sudo cp services/vimeo-monitor.service /etc/systemd/system/
   ```

2. Edit the service file to match your installation path:

   ```bash
   sudo nano /etc/systemd/system/vimeo-monitor.service
   ```

3. Enable and start the service:

   ```bash
   sudo systemctl enable vimeo-monitor
   sudo systemctl start vimeo-monitor
   ```

## Configuration

Create a `.env` file in the project root with the following parameters:

```env
# Vimeo API credentials
VIMEO_TOKEN="your_vimeo_token"
VIMEO_KEY="your_vimeo_key"
VIMEO_SECRET="your_vimeo_secret"
VIMEO_STREAM_ID="your_stream_id"

# General settings
LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=./logs/vimeo_monitor.logs
CHECK_INTERVAL=30  # Polling interval in seconds

# Image paths
HOLDING_IMAGE_PATH=/path/to/holding.jpg
API_FAIL_IMAGE_PATH=/path/to/failure.jpg

# API failure handling
API_FAILURE_THRESHOLD=3  # Consecutive failures before entering failure mode
API_STABILITY_THRESHOLD=5  # Consecutive successes before exiting failure mode
API_MIN_RETRY_INTERVAL=10  # Minimum retry interval in seconds
API_MAX_RETRY_INTERVAL=300  # Maximum retry interval in seconds
API_ENABLE_BACKOFF=true  # Enable exponential backoff for retry intervals

# Display options
DISPLAY_NETWORK_STATUS=true  # Show network status overlay
```

## Usage

### Manual Operation

To run the application manually:

```bash
source .venv/bin/activate
uv run -m vimeo_monitor.monitor
```

### Checking Status

To check the status of the service:

```bash
sudo systemctl status vimeo-monitor
```

### Viewing Logs

To view the application logs:

```bash
tail -f logs/vimeo_monitor.logs
# or for systemd:
sudo journalctl -fu vimeo-monitor
```

### Updating

To update to the latest version:

```bash
cd /path/to/vimeo-monitor
git pull
sudo systemctl restart vimeo-monitor
```

## Development

### Development Setup

1. Set up the development environment:

   ```bash
   make install
   pre-commit install
   ```

2. Run tests:

   ```bash
   make test
   ```

### Project Structure

```bash
vimeo-monitor/
├── docs/                    # Documentation
├── memory-bank/             # Design documents and planning
├── services/                # Systemd service files
├── vimeo_monitor/           # Main application code
│   ├── __init__.py
│   ├── monitor.py           # Main application logic
│   └── utils/               # Utility functions
├── .env.sample              # Example configuration
├── pyproject.toml           # Project metadata and dependencies
└── README.md                # This file
```

### Roadmap

Current development priorities:

- [In Progress] **Improve API Failure Handling**: Enhanced error detection, cooldown mechanism, and specific error handling
- **Add Network Status Display**: On-screen network status indicator with stream health monitoring
- **Implement Log Rotation**: Prevent disk space issues with configurable log rotation
- **Create TUI Settings Panel**: Terminal-based configuration interface using Whiptail for SSH access
- **Implement Prometheus Metrics**: HTTP `/metrics` endpoint for monitoring system health and performance
- **Refactor Code Structure**: Improved modularity with object-oriented design
- **Enhance Configuration Management**: Centralized configuration with validation and hot-reload support

## Troubleshooting

### Common Issues

- **Black Screen**: Check if the display is properly connected and X11 is running
- **No Stream**: Verify your Vimeo credentials and stream ID
- **API Failures**: Check network connectivity and Vimeo API status

### Diagnostic Commands

```bash
# Check if the process is running
ps aux | grep vimeo_monitor

# Check display configuration
echo $DISPLAY

# Test network connectivity
ping api.vimeo.com
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Vimeo API](https://developer.vimeo.com/) for the livestreaming capabilities
- [Cursor Memory Bank](https://github.com/vanzan01/cursor-memory-bank) - A modular, documentation-driven framework used in development
- [FFplay](https://ffmpeg.org/ffplay.html) for media playback
