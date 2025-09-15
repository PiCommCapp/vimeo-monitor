# Vimeo Monitor

[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-23%20passing-brightgreen.svg)](tests/)
[![Code Quality](https://img.shields.io/badge/code%20quality-A%2B-brightgreen.svg)](#code-quality)
[![Documentation](https://img.shields.io/badge/docs-MkDocs-blue.svg)](https://pcommcapp.github.io/vimeo-monitor/)

A robust system for monitoring Vimeo live streams and displaying them full-screen on Raspberry Pi or Linux systems. Features automated stream detection, error recovery, and comprehensive monitoring capabilities.

## ✨ Features

- **🔄 Automatic Stream Detection**: Monitors Vimeo API for live stream status
- **📺 Full-Screen Display**: Seamless video playback with VLC/FFmpeg
- **🛡️ Error Recovery**: Automatic restart and fallback mechanisms
- **📊 Health Monitoring**: Comprehensive logging and process management
- **⚙️ Easy Configuration**: Environment-based configuration system
- **🔧 Type Safety**: Full type annotations with mypy validation
- **🧪 Tested**: Comprehensive test suite with 23 passing tests

## 🚀 Quick Start

### Prerequisites

- Python 3.12 or newer
- VLC media player (`cvlc`)
- FFmpeg (`ffplay`)
- Vimeo API credentials

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/PiCommCapp/vimeo-monitor.git
   cd vimeo-monitor
   ```

2. **Install dependencies**
   ```bash
   # Install uv package manager (if not already installed)
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Install project dependencies
   uv sync
   ```

3. **Configure environment**
   ```bash
   # Copy environment template
   cp .env.sample .env
   
   # Edit with your Vimeo API credentials
   nano .env
   ```

4. **Run the monitor**
   ```bash
   uv run streammonitor.py
   ```

### Auto-Start Setup (Optional)

For automatic startup on Raspberry Pi:

```bash
cp install/streamreturn.desktop ~/.config/autostart/
cp install/xrandr.desktop ~/.config/autostart/
```

## 📚 Documentation

- **[📖 Full Documentation](https://pcommcapp.github.io/vimeo-monitor/)** - Complete user guide
- **[🛠️ Installation Guide](https://pcommcapp.github.io/vimeo-monitor/installation/)** - Detailed setup instructions
- **[🔧 Troubleshooting](https://pcommcapp.github.io/vimeo-monitor/troubleshooting/)** - Common issues and solutions

## 🏗️ Architecture

The system is built with a modular architecture for reliability and maintainability:

```
src/vimeo_monitor/
├── config.py          # Configuration management
├── logger.py          # Logging system with rotation
├── monitor.py         # Main monitoring logic
├── process_manager.py # Process lifecycle management
└── __init__.py        # Package initialization
```

### Key Components

- **Config**: Environment-based configuration with validation
- **Logger**: Rotating file logging with console output
- **Monitor**: Stream status checking and display management
- **Process Manager**: VLC/FFmpeg process lifecycle and auto-restart

## 🧪 Testing

The project includes comprehensive testing with 23 test cases:

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_config.py -v
```

### Test Coverage

- ✅ Configuration validation and environment handling
- ✅ Process management and lifecycle
- ✅ Error handling and recovery mechanisms
- ✅ Stream monitoring and status detection

## 🔧 Development

### Code Quality

The project maintains high code quality standards:

```bash
# Run all quality checks
make ci-validate

# Format code
make format

# Fix linting issues
make lint-fix

# Type checking
uv run mypy src/
```

### Available Commands

- `make setup` - Initial project setup
- `make test` - Run tests
- `make lint` - Code linting
- `make format` - Code formatting
- `make serve` - Start documentation server
- `make build` - Build documentation
- `make ci-validate` - Full CI validation

## 🚦 CI/CD Pipeline

The project uses GitHub Actions for automated quality assurance:

- **PR Validation**: Automated testing, linting, formatting, and type checking
- **Release Automation**: Documentation deployment and package building
- **Quality Gates**: ruff, black, isort, mypy, pytest with coverage
- **Documentation**: Automated deployment to GitHub Pages

## 📋 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Vimeo API Credentials
VIMEO_TOKEN=your_token_here
VIMEO_KEY=your_key_here
VIMEO_SECRET=your_secret_here

# Stream Configuration
STREAM_SELECTION=1
STATIC_IMAGE_PATH=media/holding.png
ERROR_IMAGE_PATH=media/failure.png

# Logging Configuration
LOG_FILE=logs/stream_monitor.log
LOG_LEVEL=INFO
LOG_ROTATION_DAYS=7

# Process Configuration
CHECK_INTERVAL=10
MAX_RESTARTS=5
RESTART_DELAY=5
```

## 🛠️ Troubleshooting

Common issues and solutions:

- **Stream not displaying**: Check Vimeo API credentials and stream status
- **Process crashes**: Review logs in `logs/` directory
- **Configuration errors**: Validate `.env` file format and paths
- **Permission issues**: Ensure proper file permissions for media files

For detailed troubleshooting, see the [Troubleshooting Guide](https://pcommcapp.github.io/vimeo-monitor/troubleshooting/).

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
uv sync --dev

# Run pre-commit checks
make ci-validate

# Start documentation server
make serve
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Vimeo API](https://developer.vimeo.com/) for stream access
- [VLC](https://www.videolan.org/) for video playback
- [FFmpeg](https://ffmpeg.org/) for media processing
- [MkDocs](https://www.mkdocs.org/) for documentation

## 📞 Support

- 📖 [Documentation](https://pcommcapp.github.io/vimeo-monitor/)
- 🐛 [Issue Tracker](https://github.com/PiCommCapp/vimeo-monitor/issues)
- 💬 [Discussions](https://github.com/PiCommCapp/vimeo-monitor/discussions)

---

**Status**: ✅ Production Ready | **Last Updated**: September 2024