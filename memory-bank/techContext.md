# Technical Context

## Technology Stack

- **Language**: Python 3.12+
- **Package Management**: `uv` (Python package installer and resolver)
- **Deployment Environment**: Raspberry Pi 5 with Raspberry Pi OS Desktop (X11)
- **Media Playback**:
  - Using `ffplay` for image display
  - Using `cvlc` (VLC command line) for HLS stream playback
- **API Integration**: Vimeo API (requires authentication token)
- **Process Management**: `systemd` for auto-starting service

## Dependencies

From the pyproject.toml file:

### Core Dependencies

- dotenv >= 0.9.9
- click >= 8.1.7
- (Implied) vimeo-client - for Vimeo API integration

### Development Dependencies

- pytest >= 8.4.0
- pre-commit >= 4.2.0
- tox-uv >= 1.26.0
- basedpyright >= 1.29.2
- ruff >= 0.11.12

## System Requirements

- Raspberry Pi 5 (recommended)
- Raspberry Pi OS Desktop with X11 environment
- HDMI display connected
- Internet connection for Vimeo API access
- VLC media player installed (`cvlc`)
- FFmpeg installed (`ffplay`)
- Python 3.12.2 or higher installed

## Architecture

The application follows a simple polling architecture:

1. Continuously polls Vimeo API at regular intervals
2. Checks stream availability
3. Plays stream or displays fallback image based on API response
4. Implements watchdog to detect and recover from stalled playback

## Configuration

The application uses environment variables loaded from a `.env` file for configuration:

- API credentials (token, key, secret)
- Stream ID to monitor
- Logging configuration
- Paths to fallback images
- Display options

## Systemd Integration

The application is designed to start automatically via a systemd service unit, which:

- Runs on boot after network is available
- Automatically restarts on failure
- Sets appropriate X11 display environment variables
- Loads configuration from the environment file

## Security Considerations

- API credentials stored in `.env` file (not in code repository)
- No direct user input/interaction in normal operation
- Runs with limited user privileges (pi user)

## Limitations

- Requires persistent X11 session
- No remote management interface (SSH access required)
- Single-purpose application (video kiosk only)
