# Quick Start

Get the Vimeo Monitor up and running in minutes with this step-by-step guide.

## 🚀 Prerequisites

Before you begin, ensure you have:

- **Python 3.12+** installed on your system
- **VLC media player** (`cvlc` command available)
- **FFmpeg** (`ffplay` command available)
- **Vimeo API credentials** (Access Token, Client ID, Client Secret)
- **Vimeo Stream ID** for the stream you want to monitor

## 📋 Step-by-Step Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/PiCommCapp/vimeo-monitor.git
cd vimeo-monitor
```

### Step 2: Install Dependencies

```bash
# Install uv package manager (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync
```

### Step 3: Configure Environment

```bash
# Copy the environment template
cp .env.sample .env

# Edit the .env file with your credentials
nano .env
```

Add your Vimeo credentials to the `.env` file:

```bash
# Required Vimeo API credentials
VIMEO_ACCESS_TOKEN=your_vimeo_access_token_here
VIMEO_CLIENT_ID=your_vimeo_client_id_here
VIMEO_CLIENT_SECRET=your_vimeo_client_secret_here

# Required stream configuration
VIMEO_STREAM_ID=your_stream_id_here
```

### Step 4: Prepare Media Files

Create the required media files:

```bash
# Create media directory
mkdir -p media

# Add your holding image (shown when stream is offline)
cp your_holding_image.png media/holding.png

# Add your failure image (shown when there's an error)
cp your_failure_image.png media/failure.png
```

### Step 5: Test the Configuration

```bash
# Test configuration without starting the system
uv run python -c "from src.vimeo_monitor.config import Config; print('Configuration valid')"
```

### Step 6: Run the Monitor

```bash
# Start the monitor
uv run python -m vimeo_monitor
```

## 🔧 Optional: Enable Health Monitoring

To enable health monitoring with Prometheus metrics:

```bash
# Edit .env file
nano .env

# Add health monitoring configuration
HEALTH_MONITORING_ENABLED=true
HEALTH_METRICS_PORT=8080
HEALTH_METRICS_HOST=0.0.0.0

# Restart the monitor
uv run python -m vimeo_monitor
```

Access metrics at: `http://localhost:8080/metrics`

## ✅ Verification

### Check System Status

1. **Stream Detection**: The system should detect your Vimeo stream status
2. **Display**: Video should play when stream is live, holding image when offline
3. **Logs**: Check `logs/vimeo_monitor.log` for system status
4. **Health Metrics**: If enabled, visit `http://localhost:8080/metrics`

### Expected Behavior

- **Live Stream**: Full-screen video playback
- **Offline Stream**: Holding image display
- **Error State**: Failure image display
- **Auto-Recovery**: System restarts automatically on failures

## 🐛 Troubleshooting

### Common Issues

#### "VIMEO_ACCESS_TOKEN not found"
- Ensure your `.env` file contains valid Vimeo credentials
- Check file permissions: `chmod 600 .env`

#### "Stream not found"
- Verify your `VIMEO_STREAM_ID` is correct
- Check that the stream exists and is accessible

#### "VLC not found"
- Install VLC: `sudo apt install vlc` (Ubuntu/Debian)
- Ensure `cvlc` command is available: `which cvlc`

#### "FFmpeg not found"
- Install FFmpeg: `sudo apt install ffmpeg` (Ubuntu/Debian)
- Ensure `ffplay` command is available: `which ffplay`

### Getting Help

- Check the [Troubleshooting Guide](troubleshooting.md) for detailed solutions
- Review the [Configuration Guide](configuration.md) for all available options
- Check system logs: `tail -f logs/vimeo_monitor.log`

## 🎯 Next Steps

Once your system is running:

1. **Monitor Performance**: Check logs and health metrics
2. **Customize Configuration**: Adjust settings in `.env` file
3. **Set Up Automation**: Consider running as a service
4. **Explore Features**: Learn about [Health Monitoring](health-monitoring.md)

## 📚 Related Documentation

- **[Installation Guide](installation.md)** - Detailed installation instructions
- **[Configuration](configuration.md)** - Complete configuration reference
- **[Basic Usage](usage.md)** - How to use the system
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions
- **[Health Monitoring](health-monitoring.md)** - Monitoring and metrics
