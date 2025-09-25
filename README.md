# Vimeo Monitor

[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-23%20passing-brightgreen.svg)](tests/)
[![Code Quality](https://img.shields.io/badge/code%20quality-A%2B-brightgreen.svg)](#code-quality)
[![Documentation](https://img.shields.io/badge/docs-MkDocs-blue.svg)](https://pcommcapp.github.io/vimeo-monitor/)

A robust, production-ready system for monitoring Vimeo live streams and displaying them full-screen on Raspberry Pi or Linux systems. Perfect for digital signage, live event displays, and automated stream monitoring.

## 🎯 What This Does

**Vimeo Monitor** automatically detects when your Vimeo live stream goes online and displays it full-screen. When the stream is offline, it shows a custom holding image. If something goes wrong, it displays an error image and automatically restarts.

**Perfect for:**
- 🖥️ Digital signage displays
- 🎪 Live event monitoring
- 📺 Kiosk systems
- 🏢 Office displays
- 🎮 Gaming stream monitoring

## ✨ Key Features

- **🔄 Smart Stream Detection**: Automatically monitors your Vimeo stream every 30 seconds
- **📺 Seamless Display**: Full-screen video with VLC when live, custom images when offline
- **🛡️ Bulletproof Reliability**: Auto-restarts on crashes, handles network issues gracefully
- **📊 Optional Health Monitoring**: Prometheus metrics for system monitoring
- **⚙️ Easy Configuration**: Simple `.env` file setup
- **🔧 Production Ready**: Comprehensive logging, error handling, and recovery

## 🚀 Get Started in 5 Minutes

### 1. Install Dependencies
```bash
# On Ubuntu/Debian/Raspberry Pi OS
sudo apt update
sudo apt install vlc ffmpeg git python3 python3-pip

# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Clone and Setup
```bash
git clone https://github.com/PiCommCapp/vimeo-monitor.git
cd vimeo-monitor
uv sync
```

### 3. Configure Your Stream
```bash
# Copy the configuration template
cp .env.sample .env

# Edit with your Vimeo credentials
nano .env
```

**Required settings in `.env`:**
```bash
VIMEO_ACCESS_TOKEN=your_vimeo_access_token_here
VIMEO_CLIENT_ID=your_vimeo_client_id_here
VIMEO_CLIENT_SECRET=your_vimeo_client_secret_here
VIMEO_STREAM_ID=your_stream_id_here
```

### 4. Add Your Images
```bash
# Create media directory
mkdir -p media

# Add your images (PNG format recommended)
cp your_holding_image.png media/holding.png    # Shown when stream is offline
cp your_error_image.png media/failure.png      # Shown when there's an error
```

### 5. Run It!
```bash
# Start monitoring
uv run python -m vimeo_monitor
```

**That's it!** Your system will now automatically display your Vimeo stream when it's live.

## 📚 Complete Documentation

- **[📖 Full Documentation](https://pcommcapp.github.io/vimeo-monitor/)** - Complete user guide
- **[🛠️ Installation Guide](https://pcommcapp.github.io/vimeo-monitor/installation/)** - Detailed setup instructions
- **[🔧 Configuration](https://pcommcapp.github.io/vimeo-monitor/configuration/)** - All available settings
- **[🐛 Troubleshooting](https://pcommcapp.github.io/vimeo-monitor/troubleshooting/)** - Common issues and solutions
- **[📊 Health Monitoring](https://pcommcapp.github.io/vimeo-monitor/health-monitoring/)** - Optional metrics and monitoring

## 🎮 Usage Examples

### Basic Monitoring
```bash
# Simple start
uv run python -m vimeo_monitor
```

### With Health Monitoring
```bash
# Enable metrics collection
HEALTH_MONITORING_ENABLED=true uv run python -m vimeo_monitor

# Access metrics at http://localhost:8080/metrics
```

### Custom Configuration
```bash
# Use different config file
ENV_FILE=production.env uv run python -m vimeo_monitor

# Debug mode
LOG_LEVEL=DEBUG uv run python -m vimeo_monitor
```

## 🔧 System Requirements

### Minimum Requirements
- **OS**: Linux (Ubuntu 20.04+, Raspberry Pi OS)
- **Python**: 3.12+
- **RAM**: 512MB
- **Storage**: 100MB
- **Network**: Stable internet connection

### Recommended for Production
- **OS**: Ubuntu 22.04+ or Raspberry Pi OS
- **RAM**: 1GB+
- **Storage**: 500MB+
- **CPU**: 2+ cores
- **Network**: Wired connection preferred

## 🛠️ Configuration Options

### Essential Settings
```bash
# Vimeo API (required)
VIMEO_ACCESS_TOKEN=your_token
VIMEO_CLIENT_ID=your_client_id
VIMEO_CLIENT_SECRET=your_secret
VIMEO_STREAM_ID=your_stream_id

# Stream monitoring
STREAM_CHECK_INTERVAL=30          # Check every 30 seconds
```

### Optional Settings
```bash
# Logging
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR
LOG_FILE=logs/vimeo_monitor.log

# Process management
PROCESS_MAX_RESTARTS=10           # Auto-restart limit
PROCESS_RESTART_DELAY=5           # Delay between restarts

# Health monitoring (optional)
HEALTH_MONITORING_ENABLED=false   # Enable metrics collection
HEALTH_METRICS_PORT=8080          # Metrics server port
```

## 🚨 Troubleshooting

### Common Issues

**"Stream not found"**
- Check your `VIMEO_STREAM_ID` is correct
- Verify the stream exists and is accessible
- Test with: `curl -H "Authorization: bearer YOUR_TOKEN" https://api.vimeo.com/me`

**"VLC not found"**
- Install VLC: `sudo apt install vlc`
- Verify: `which cvlc`

**"No video display"**
- Check display is active: `xrandr`
- Test with static image: `ffplay -fs media/holding.png`

**Need more help?** Check our [Troubleshooting Guide](https://pcommcapp.github.io/vimeo-monitor/troubleshooting/) for detailed solutions.

## 🧪 Development & Testing

### Run Tests
```bash
# All tests
uv run pytest tests/ -v

# With coverage
uv run pytest tests/ --cov=src --cov-report=html

# Specific test file
uv run pytest tests/test_monitor.py -v
```

### Code Quality
```bash
# Format code
make format

# Lint code
make lint

# Run all checks
make ci-validate
```

### Development Setup
```bash
# Install development dependencies
uv sync --dev

# Start documentation server
make serve

# Build documentation
make build
```

## 🚦 CI/CD & Quality

This project maintains high quality standards with:

- **Automated Testing**: 23 passing tests with comprehensive coverage
- **Code Quality**: Automated linting, formatting, and type checking
- **Documentation**: Auto-deployed to GitHub Pages
- **Release Automation**: Automated package building and deployment

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork** the repository
2. **Clone** your fork: `git clone https://github.com/YOUR_USERNAME/vimeo-monitor.git`
3. **Create** a feature branch: `git checkout -b feature/amazing-feature`
4. **Make** your changes and test them
5. **Commit** with a clear message: `git commit -m 'Add amazing feature'`
6. **Push** to your branch: `git push origin feature/amazing-feature`
7. **Open** a Pull Request

See our [Contributing Guide](https://pcommcapp.github.io/vimeo-monitor/contributing/) for detailed information.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Vimeo API](https://developer.vimeo.com/) for stream access
- [VLC](https://www.videolan.org/) for video playback
- [FFmpeg](https://ffmpeg.org/) for media processing
- [MkDocs](https://www.mkdocs.org/) for documentation

## 📞 Support & Community

- 📖 **[Full Documentation](https://pcommcapp.github.io/vimeo-monitor/)** - Complete guides
- 🐛 **[Report Issues](https://github.com/PiCommCapp/vimeo-monitor/issues)** - Bug reports and feature requests
- 💬 **[Discussions](https://github.com/PiCommCapp/vimeo-monitor/discussions)** - Community support
- 📧 **Email Support** - For urgent issues

---

**Status**: ✅ Production Ready | **Last Updated**: January 2025 | **Version**: 1.0.0