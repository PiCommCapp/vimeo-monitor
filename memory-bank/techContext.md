# Technical Context - Vimeo Monitor Project

## Technology Stack

### Core Technologies
- **Language**: Python 3.x
- **Runtime**: uv runner
- **Platform**: Raspberry Pi 5 (ARM64)
- **OS**: Raspberry Pi OS Desktop (Debian-based)
- **Display**: X11 with auto-login

### Media Technologies
- **Streaming**: HLS (HTTP Live Streaming)
- **Player**: cvlc (VLC command-line), ffplay, mpv
- **Validation**: ffprobe for stream health
- **Format**: m3u8 playlist files

### API & Networking
- **API**: Vimeo REST API
- **Authentication**: OAuth 2.0 with access tokens
- **Protocol**: HTTPS
- **Data Format**: JSON

### System Integration
- **Autostart**: .desktop files in ~/.config/autostart/
- **Service Management**: User-level autostart (not systemd)
- **Environment**: X11 session management
- **Audio**: HDMI audio output

## Development Environment

### Local Development
- **Editor**: VS Code with Python extensions
- **Version Control**: Git
- **Package Management**: uv for Python dependencies
- **Environment**: .env file for configuration

### Testing & Validation
- **Stream Testing**: Local HLS stream validation
- **API Testing**: Vimeo API endpoint testing
- **Hardware Testing**: Raspberry Pi 5 deployment
- **Integration Testing**: Full system workflow testing

## Deployment Considerations

### Hardware Requirements
- **Device**: Raspberry Pi 5 (4GB+ RAM recommended)
- **Storage**: 16GB+ microSD card
- **Network**: Ethernet or WiFi connectivity
- **Display**: HDMI monitor with audio support

### Environment Setup
- **OS Installation**: Raspberry Pi OS Desktop
- **Auto-login**: Configured for headless operation
- **Network**: Static IP or DHCP configuration
- **Updates**: Git-based deployment with reboot

### Security Considerations
- **API Credentials**: Secure .env file storage
- **Network Security**: Local network isolation
- **Access Control**: SSH-only management access
- **Credential Rotation**: Regular token updates
