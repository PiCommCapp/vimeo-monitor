# Vimeo Monitor

A system to monitor Vimeo live stream events using the Vimeo API to securely stream video to a Raspberry Pi and display at full screen.

## Current Status

**System works but needs refactoring for reliability and maintainability.**

## How It Works

1. Uses Vimeo API credentials to retrieve m3u8 stream links
2. Probes API to determine if stream is live
   - If not live: displays holding card image
   - If live: displays full-screen video stream with audio
3. Monitors stream continuously, switching between modes as needed
4. Auto-restarts on stream loss

## Current Issues

- **Reliability**: Requires daily restarts (unstable)
- **Security**: API credentials hardcoded in source
- **Configuration**: Hardcoded paths and settings
- **Error Handling**: Limited error recovery
- **Code Quality**: Single monolithic script

## Refactor Plan

### Phase 1: Basic Improvements

- [ ] Move credentials to environment variables
- [ ] Extract configuration to separate file
- [ ] Improve error handling and logging
- [ ] Fix hardcoded paths

### Phase 2: Code Structure

- [ ] Break monolithic script into modules
- [ ] Add proper configuration management
- [ ] Implement better process management
- [ ] Add health checks and auto-recovery

### Phase 3: Reliability

- [ ] Add comprehensive error handling
- [ ] Implement proper logging rotation
- [ ] Add monitoring and alerting
- [ ] Create proper installation/setup scripts

## Quick Start

1. Install dependencies: `uv sync`
2. Set up environment variables (see `.env.sample`)
3. Run: `uv run streammonitor.py`

## Auto-Start Setup

Copy desktop files to autostart:

```bash
cp install/streamreturn.desktop ~/.config/autostart/
cp install/xrandr.desktop ~/.config/autostart/
```

## Dependencies

- Python 3.12+
- VLC media player (`cvlc`)
- FFmpeg (`ffplay`)
- Vimeo API credentials
