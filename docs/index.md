# Vimeo Monitor

[![Python](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-23%20passing-brightgreen.svg)](tests/)
[![Code Quality](https://img.shields.io/badge/code%20quality-A%2B-brightgreen.svg)](#code-quality)
[![Documentation](https://img.shields.io/badge/docs-MkDocs-blue.svg)](https://pcommcapp.github.io/vimeo-monitor/)

A robust, production-ready system for monitoring Vimeo live streams and displaying them full-screen on Raspberry Pi or Linux systems. Features automated stream detection, comprehensive error recovery, health monitoring, and professional-grade reliability.

## ✨ Key Features

### 🔄 **Automatic Stream Detection**
- Monitors Vimeo API for live stream status changes
- Seamless switching between live and offline states
- Real-time stream availability checking

### 📺 **Full-Screen Display**
- High-quality video playback with VLC/FFmpeg
- Custom holding images when streams are offline
- Error state visualization with failure images

### 🛡️ **Enterprise-Grade Reliability**
- Automatic restart and recovery mechanisms
- Comprehensive error handling with retry logic
- Process health monitoring and auto-recovery
- Graceful shutdown and signal handling

### 📊 **Health Monitoring** (Optional)
- Prometheus metrics collection
- FastAPI server for metrics endpoint
- System resource monitoring (CPU, memory, temperature)
- Network connectivity and performance monitoring
- Stream quality and availability metrics

### ⚙️ **Professional Configuration**
- Environment-based configuration system
- Comprehensive validation and error checking
- Security best practices with credential management
- Flexible deployment options

### 🔧 **Developer-Friendly**
- Full type annotations with mypy validation
- Comprehensive test suite (23 passing tests)
- Modular, maintainable architecture
- Professional documentation and guides

## 🚀 Quick Start

### Prerequisites
- Python 3.12 or newer
- VLC media player (`cvlc`)
- FFmpeg (`ffplay`)
- Vimeo API credentials

### Installation
```bash
# Clone the repository
git clone https://github.com/PiCommCapp/vimeo-monitor.git
cd vimeo-monitor

# Install dependencies
uv sync

# Configure environment
cp .env.sample .env
# Edit .env with your Vimeo API credentials
```

### Basic Usage
```bash
# Run the monitor
uv run python -m vimeo_monitor

# With health monitoring (optional)
HEALTH_MONITORING_ENABLED=true uv run python -m vimeo_monitor
```

## 📚 Documentation

### Getting Started
- **[Installation Guide](installation.md)** - Complete setup instructions
- **[Configuration](configuration.md)** - Environment variables and settings
- **[Quick Start](quick-start.md)** - Step-by-step setup guide

### User Guide
- **[Basic Usage](usage.md)** - How to use the system
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions
- **[Health Monitoring](health-monitoring.md)** - Monitoring and metrics

### Development
- **[API Reference](api-reference.md)** - Complete API documentation
- **[Contributing](contributing.md)** - How to contribute to the project
- **[Development Setup](development.md)** - Setting up development environment

### Project Information
- **[Architecture](architecture.md)** - System architecture overview
- **[Changelog](changelog.md)** - Version history and changes
- **[License](license.md)** - MIT License

## 🏗️ Architecture

The Vimeo Monitor uses a modular, production-ready architecture:

- **Core Monitoring**: Vimeo API integration with automatic stream detection
- **Process Management**: Robust subprocess handling with health monitoring
- **Error Recovery**: Comprehensive retry mechanisms and auto-restart
- **Health Monitoring**: Optional Prometheus metrics and FastAPI server
- **Configuration**: Environment-based settings with validation
- **Logging**: Rotating logs with comprehensive error tracking

## 🔧 System Requirements

### Minimum Requirements
- **OS**: Linux (tested on Raspberry Pi OS, Ubuntu)
- **Python**: 3.12 or newer
- **Memory**: 512MB RAM
- **Storage**: 100MB free space

### Recommended Requirements
- **OS**: Raspberry Pi OS or Ubuntu 22.04+
- **Python**: 3.12+
- **Memory**: 1GB RAM
- **Storage**: 500MB free space
- **Network**: Stable internet connection

### Dependencies
- **VLC**: `cvlc` for video playback
- **FFmpeg**: `ffplay` for stream analysis
- **Python Packages**: See `pyproject.toml` for complete list

## 🎯 Use Cases

### Live Streaming Displays
- Digital signage for live events
- Public displays showing live streams
- Kiosk systems with live content

### Monitoring and Alerting
- Stream availability monitoring
- Performance metrics collection
- Automated alerting on stream issues


## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](contributing.md) for details on:

- Setting up a development environment
- Code style and standards
- Testing requirements
- Pull request process

## 📄 License

This project is licensed under the MIT License - see the [License](license.md) file for details.

## 🆘 Support

- **Documentation**: Browse our comprehensive guides
- **Issues**: Report bugs or request features on GitHub
- **Discussions**: Join community discussions
- **Troubleshooting**: Check our troubleshooting guide

---

**Ready to get started?** Check out our [Installation Guide](installation.md) or [Quick Start](quick-start.md) for step-by-step setup instructions.