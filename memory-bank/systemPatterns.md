# System Patterns - Vimeo Monitor Project

## Architecture Patterns

### Core System Architecture
- **Modular Design**: Separate components for API, playback, monitoring, and display
- **State Machine**: API state management with fallback modes
- **Fault Tolerance**: Self-healing mechanisms for player and API failures
- **Headless Operation**: No GUI, fully autonomous operation

### Design Principles
- **Robustness**: Handle API instability and network issues gracefully
- **Recovery**: Automatic restart and recovery mechanisms
- **Monitoring**: Comprehensive logging and metrics collection
- **Simplicity**: Minimal dependencies, focused functionality

## Implementation Patterns

### Error Handling
- **Exponential Backoff**: For API retry attempts
- **Graceful Degradation**: Fallback to static images when streams fail
- **Process Monitoring**: Watchdog for player health
- **State Persistence**: Track mode changes and failure counts

### Resource Management
- **Process Control**: Subprocess management for media players
- **Memory Management**: Efficient handling of video streams
- **File I/O**: Static image loading and caching
- **Network Management**: API polling with timeout handling

## Technology Patterns

### Media Playback
- **Player Selection**: cvlc preferred, fallback to ffplay/mpv
- **Stream Validation**: ffprobe for stream health checks
- **Fullscreen Display**: X11 window management
- **Audio Handling**: HDMI audio output

### API Integration
- **REST API**: Vimeo API integration
- **Authentication**: Token-based security
- **Polling Strategy**: Configurable intervals
- **Response Handling**: JSON parsing and validation

### Monitoring & Observability
- **Metrics Collection**: Prometheus-compatible endpoint
- **Logging Strategy**: File-based with optional stdout
- **Health Checks**: Internal system health monitoring
- **Performance Tracking**: Uptime and restart metrics
