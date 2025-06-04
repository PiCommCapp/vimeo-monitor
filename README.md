# Vimeo Stream Monitor

A robust Python application for monitoring Vimeo live streams with automatic failover, health monitoring, network status tracking, and cross-platform system service deployment.

## 🚀 Key Features

- **🎥 Automated Stream Monitoring**: Continuously monitors Vimeo live stream status with intelligent failover
- **🌐 Network Health Monitoring**: Real-time network connectivity tracking with fallback strategies
- **🔐 System Service Installation**: Cross-platform service deployment with security hardening
- **🖥️ Smart Status Display**: GUI and terminal-based overlays with real-time health indicators
- **🔄 Auto-Recovery**: Graceful handling of network issues, API failures, and process crashes
- **📋 Comprehensive Logging**: Automatic log rotation with detailed diagnostics and analysis
- **🛡️ Production Ready**: Enterprise-grade security, resource limits, and monitoring
- **🔧 Easy Management**: Complete lifecycle management via simple `make` commands

## 🏗️ Architecture

The application uses a **modular architecture** with clean separation of concerns:

- **ConfigManager**: Centralized configuration with multi-format support (ENV/YAML/TOML)
- **HealthMonitor**: API health tracking, failure state management, and network integration
- **NetworkMonitor**: Multi-protocol connectivity monitoring with adaptive fallback strategies
- **VimeoAPIClient**: Dedicated API interaction layer with comprehensive error handling
- **StreamManager**: Process lifecycle and media playbook management
- **MonitorApp**: Main orchestrator using dependency injection pattern

📖 **[Complete Architecture Documentation](docs/architecture.md)**

## 🌟 Recent Updates

### ✅ **System Service Installation (TASK-010)**

- Cross-platform service installation (Linux systemd, macOS launchd)
- Enterprise-grade security hardening with dedicated service user
- One-command setup and deployment (`make setup-service`)
- Complete lifecycle management and automated uninstall

### ✅ **Network Monitoring & Fallback (TASK-009)**

- Real-time network connectivity monitoring (TCP, HTTP, HTTPS, ICMP)
- Intelligent fallback strategies with adaptive monitoring intervals
- Priority-based target selection during network degradation
- Advanced endpoint fallback with alternative hosts

### ✅ **Enhanced Configuration & Logging**

- Multi-format configuration support (YAML, TOML, ENV)
- Automatic log rotation with compression and analysis tools
- Live configuration reload and backup management

## 🛠️ Quick Start

### Prerequisites

**System Requirements:**

- **Linux**: Ubuntu 16.04+, CentOS 7+, Debian 8+ (with systemd)
- **macOS**: macOS 10.10+ (with launchd)
- **Python**: 3.11+
- **Dependencies**: ffmpeg (for media playback)

**For Production (Raspberry Pi):**

- Raspberry Pi OS Desktop (NOT Lite - requires GUI)
- X11 desktop environment for video display
- See [Raspberry Pi Deployment Guide](docs/raspberry-pi-deployment.md)

### Installation Options

#### Option 1: Complete Setup with Service (Recommended)

```bash
# Clone and install everything including system service
git clone https://github.com/dcorso21/vimeo-monitor.git
cd vimeo-monitor
make setup-service
```

This installs:

- ✅ Application and dependencies
- ✅ System service with auto-start at boot
- ✅ Log rotation configuration
- ✅ Security hardening and user isolation

#### Option 2: Development Setup

```bash
# Clone and set up for development
git clone https://github.com/dcorso21/vimeo-monitor.git
cd vimeo-monitor
make setup
```

#### Option 3: Manual Installation

```bash
# Step-by-step installation
git clone https://github.com/dcorso21/vimeo-monitor.git
cd vimeo-monitor

# Install dependencies
make install

# Configure application
cp .env.example .env
nano .env  # Add your Vimeo API credentials

# Optional: Install as system service
sudo make install-service
```

### Essential Configuration

Create/edit `.env` file with your Vimeo API credentials:

```bash
# Copy example configuration
cp .env.example .env

# Edit with your settings
nano .env
```

**Required Settings:**

```env
# Vimeo API credentials (REQUIRED)
VIMEO_ACCESS_TOKEN="your_vimeo_access_token"
VIMEO_VIDEO_ID="your_video_id"

# Media paths (create these directories and add images)
HOLDING_IMAGE_PATH="./media/holding.jpg"
API_FAIL_IMAGE_PATH="./media/failure.jpg"

# Basic configuration
LOG_LEVEL="INFO"
CHECK_INTERVAL=30
```

**Network Monitoring (Optional):**

```env
# Network status overlay
DISPLAY_NETWORK_STATUS=true
OVERLAY_POSITION=top-right
OVERLAY_UPDATE_INTERVAL=2

# Network monitoring settings
ENABLE_NETWORK_MONITORING=true
NETWORK_CHECK_INTERVAL=30
```

### Quick Test

Test the application before production deployment:

```bash
# Test basic functionality
uv run -m vimeo_monitor.monitor

# Should show status like:
# 🎥 Status: Mode=STREAM | API=✅ HEALTHY | Stream=🟢 ACTIVE | Network=🟢 HEALTHY | Failures=0.0% | Uptime=5s
```

## 📋 Available Commands

### Installation & Setup

```bash
make setup                 # Complete development setup
make setup-service         # Complete setup + system service
make install               # Install dependencies only
make install-uv            # Install uv package manager
make status               # Check system status
```

### Service Management

```bash
make install-service      # Install as system service
make uninstall-service    # Remove system service
make service-start        # Start the service
make service-stop         # Stop the service
make service-restart      # Restart the service
make service-status       # Check service status
make service-logs         # View live service logs
```

### Development & Testing

```bash
make test                 # Run all tests
make test-network         # Run network monitoring tests
make lint                 # Run code linting
make format               # Format code
make check                # Run linting + tests
make clean                # Clean build artifacts
```

### Log Management

```bash
make analyze-logs         # Analyze log files
make rotate-logs          # Manually rotate logs
make clean-logs           # Clean old log files
make compress-logs        # Compress logs to save space
make clean-old-logs       # Remove logs older than 30 days
```

### Documentation

```bash
make docs                 # Build documentation
make serve-docs           # Serve docs locally
make help                 # Show all available commands
```

## 🖥️ Usage

### Development Mode

Run manually for development and testing:

```bash
# Run with terminal status display
uv run -m vimeo_monitor.monitor

# View logs in real-time
tail -f logs/vimeo_monitor.log
```

### Production Service Mode

For production deployment (Raspberry Pi, server):

```bash
# Install as system service
sudo make install-service

# Service will auto-start at boot
# Manage with standard commands:
make service-status       # Check if running
make service-logs         # View live logs
make service-restart      # Restart if needed
```

### Service Management

**Linux (systemd):**

```bash
sudo systemctl status vimeo-monitor
sudo systemctl start vimeo-monitor
sudo systemctl stop vimeo-monitor
sudo journalctl -u vimeo-monitor -f
```

**macOS (launchd):**

```bash
sudo launchctl list | grep vimeomonitor
sudo launchctl load /Library/LaunchDaemons/com.vimeomonitor.service.plist
sudo launchctl unload /Library/LaunchDaemons/com.vimeomonitor.service.plist
tail -f /opt/vimeo-monitor/logs/service.log
```

## 🌐 Network Status Display

The application provides real-time visual feedback through multiple display modes:

### GUI Mode (Production/Raspberry Pi)

- Professional overlay window with color-coded health indicators
- Real-time API status (✅ Healthy / ❌ Failing)
- Stream status (🟢 Active / 🟡 Standby / 🔴 Failure)
- Network connectivity (🟢 Healthy / 🟡 Degraded / 🔴 Failing)
- Performance metrics and uptime tracking

### Terminal Mode (Development/SSH)

- Status updates in application logs with emoji indicators
- Same comprehensive metrics as GUI mode
- Automatic fallback when GUI unavailable

### Configuration

```env
DISPLAY_NETWORK_STATUS=true      # Enable overlay
OVERLAY_POSITION=top-right       # top-left, top-right, bottom-left, bottom-right
OVERLAY_OPACITY=0.8              # 0.0 (transparent) to 1.0 (opaque)
OVERLAY_UPDATE_INTERVAL=2        # Update frequency in seconds
OVERLAY_AUTO_HIDE=false          # Hide when healthy
```

## 🔧 Advanced Features

### Network Monitoring & Fallback

The application includes sophisticated network monitoring with intelligent fallback strategies:

- **Multi-Protocol Monitoring**: TCP, HTTP, HTTPS, ICMP connectivity tests
- **Adaptive Intervals**: Monitoring frequency adjusts based on network health
- **Priority-Based Testing**: Critical targets only during network failure
- **Endpoint Fallback**: Alternative hosts for each monitoring target
- **Smart Recovery**: Gradual return to normal monitoring after recovery

### Service Security Features

Production deployments include enterprise-grade security:

- **User Isolation**: Dedicated `vimeo-monitor` user with no login privileges
- **File System Protection**: Read-only system access, limited write permissions
- **Network Restrictions**: Only necessary network protocols allowed
- **Resource Limits**: CPU, memory, and file descriptor limits
- **System Call Filtering**: Restricted to essential operations only

### Log Management

Comprehensive logging with automatic management:

- **Automatic Rotation**: Daily rotation with configurable size limits
- **Compression**: Automatic gzip compression of old logs
- **Analysis Tools**: Built-in log analysis and statistics
- **Retention Policy**: Configurable retention periods

## 📁 Project Structure

```
vimeo-monitor/
├── docs/                           # Documentation
│   ├── service_installation.md     # Service setup guide
│   ├── network_fallback_strategies.md # Network monitoring docs
│   ├── IMPLEMENTATION_SUMMARY.md   # Technical implementation details
│   └── architecture.md             # System architecture
├── scripts/                        # Installation scripts
│   ├── install-service.sh          # System service installation
│   ├── uninstall-service.sh        # Service removal
│   └── config_migrate.py           # Configuration migration
├── services/                       # System service files
│   ├── vimeo-monitor.service       # Systemd service configuration
│   ├── logrotation.conf            # Log rotation configuration
│   └── log_management.py           # Log management utilities
├── vimeo_monitor/                  # Main application code
│   ├── monitor.py                  # Main application with orchestration
│   ├── config.py                   # Configuration management
│   ├── health.py                   # Health monitoring and API failure handling
│   ├── network_monitor.py          # Network connectivity monitoring
│   ├── overlay.py                  # Real-time status display system
│   ├── client.py                   # Vimeo API client
│   └── stream.py                   # Stream management and playback
├── memory-bank/                    # Development planning and documentation
├── .env.example                    # Example configuration file
├── pyproject.toml                  # Project metadata and dependencies
├── Makefile                        # Development and deployment automation
└── README.md                       # This documentation
```

## 🚧 System Requirements

### Development Environment

- **OS**: macOS, Linux, or Windows (with WSL)
- **Python**: 3.11+
- **Package Manager**: uv (auto-installed)
- **Display**: Terminal-based status display

### Production Environment (Raspberry Pi)

- **Hardware**: Raspberry Pi 4/5 with 4GB+ RAM
- **OS**: Raspberry Pi OS Desktop (Bookworm recommended)
- **Display**: HDMI monitor for video output
- **Network**: Ethernet or WiFi connectivity
- **GUI**: X11 desktop environment (required for video display)

### System Dependencies

**Linux/Raspberry Pi:**

```bash
sudo apt update && sudo apt install -y \
    python3-pip python3-venv python3-tk \
    ffmpeg curl make build-essential \
    python3-tkinter xauth x11-apps
```

**macOS:**

```bash
# Install ffmpeg via Homebrew
brew install ffmpeg

# Python and other dependencies handled automatically
```

## 🔍 Troubleshooting

### Common Installation Issues

**Missing tkinter (Raspberry Pi):**

```bash
sudo apt install python3-tk python3-tkinter
```

**Missing ffmpeg:**

```bash
# Linux/Raspberry Pi
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

**Service won't start:**

```bash
# Check status and logs
make service-status
make service-logs

# Verify configuration
sudo cat /opt/vimeo-monitor/.env

# Test manual execution
sudo -u vimeo-monitor /opt/vimeo-monitor/.venv/bin/python -m vimeo_monitor.monitor
```

### Network Issues

**Connectivity problems:**

```bash
# Test network connectivity
ping api.vimeo.com
curl -I https://api.vimeo.com

# Check DNS resolution
nslookup api.vimeo.com

# Run network monitoring tests
make test-network
```

**Overlay not appearing:**

```bash
# Verify GUI environment
python3 -c "import tkinter; print('✅ tkinter available')"

# Check configuration
grep DISPLAY_NETWORK_STATUS .env

# Test X11 (if using SSH)
echo $DISPLAY
```

### Diagnostic Commands

```bash
# System status
make status

# Test installation
uv run -m vimeo_monitor.monitor

# Check logs
tail -f logs/vimeo_monitor.log

# Analyze logs
make analyze-logs

# Network monitoring test
make test-network
```

## 📚 Documentation

- **[Service Installation Guide](docs/service_installation.md)** - Complete service setup
- **[Network Fallback Strategies](docs/network_fallback_strategies.md)** - Network monitoring details
- **[Implementation Summary](docs/IMPLEMENTATION_SUMMARY.md)** - Technical implementation
- **[Architecture Documentation](docs/architecture.md)** - System design overview

## 🛣️ Development Roadmap

### ✅ Completed Features

- **Network Monitoring**: Real-time connectivity tracking with fallback strategies
- **System Service**: Cross-platform installation with security hardening
- **Configuration Management**: Multi-format support with validation
- **Log Management**: Automatic rotation, compression, and analysis
- **Status Display**: GUI and terminal-based real-time overlays

### 🚧 Upcoming Features

- **Terminal UI (TUI)**: Interactive configuration and monitoring dashboard
- **Performance Optimization**: Intelligent caching and resource management
- **Advanced Monitoring**: Historical data tracking and alerting
- **API Extensions**: Multi-stream support and plugin architecture
- **Cloud Deployment**: Docker containers and cloud platform support

## 🤝 Contributing

Contributions are welcome! This project follows a documentation-driven development approach:

1. **Fork** the repository
2. **Create** your feature branch (`git checkout -b feature/amazing-feature`)
3. **Document** your changes thoroughly
4. **Test** your implementation (`make check`)
5. **Commit** your changes (`git commit -m 'Add amazing feature'`)
6. **Push** to the branch (`git push origin feature/amazing-feature`)
7. **Open** a Pull Request

### Development Setup

```bash
# Set up development environment
git clone https://github.com/dcorso21/vimeo-monitor.git
cd vimeo-monitor
make setup

# Run tests and checks
make check
make test-network
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- **[Vimeo API](https://developer.vimeo.com/)** - Livestreaming capabilities
- **[uv Package Manager](https://github.com/astral-sh/uv)** - Fast Python package management
- **[FFmpeg](https://ffmpeg.org/)** - Media playback and processing
- **[Cursor Memory Bank](https://github.com/vanzan01/cursor-memory-bank)** - Documentation-driven development framework

---

## Support

For issues, questions, or feature requests:

1. **Check Logs**: Start with application and service logs
2. **Review Documentation**: Check the comprehensive guides in `docs/`
3. **Test Components**: Use `make test` and `make test-network`
4. **Create Issue**: Open a GitHub issue with detailed information

**Quick Help:**

```bash
make help                 # Show all available commands
make status              # Check system status
make service-logs        # View live service logs (if installed)
tail -f logs/vimeo_monitor.log  # View application logs
```
