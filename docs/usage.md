# Basic Usage

Learn how to use the Vimeo Monitor system effectively.

## 🚀 Starting the System

### Basic Startup
```bash
# Start the monitor
uv run python -m vimeo_monitor
```

### With Health Monitoring
```bash
# Enable health monitoring
HEALTH_MONITORING_ENABLED=true uv run python -m vimeo_monitor
```

### With Custom Configuration
```bash
# Use custom environment file
ENV_FILE=production.env uv run python -m vimeo_monitor
```

## 📺 Display Modes

### Live Stream Mode
When your Vimeo stream is live:
- **Full-screen video playback** using VLC
- **Audio enabled** for stream audio
- **Automatic quality adjustment** based on stream
- **Real-time monitoring** of stream status

### Offline Mode
When your Vimeo stream is offline:
- **Holding image display** (from `media/holding.png`)
- **Continuous monitoring** for stream status changes
- **Automatic switching** to live mode when stream goes live

### Error Mode
When system encounters errors:
- **Failure image display** (from `media/failure.png`)
- **Error logging** with detailed information
- **Automatic recovery** attempts
- **Process restart** if needed

## ⚙️ Configuration Management

### Environment Variables
The system uses environment variables for all configuration:

```bash
# Core settings
VIMEO_ACCESS_TOKEN=your_token
VIMEO_STREAM_ID=your_stream_id
STREAM_CHECK_INTERVAL=30

# Optional settings
LOG_LEVEL=INFO
HEALTH_MONITORING_ENABLED=false
```

### Configuration Files
- **`.env`**: Main configuration file
- **`.env.sample`**: Template with all available options
- **`logs/`**: Log files and configuration logs

## 📊 Monitoring and Logs

### Log Files
- **`logs/vimeo_monitor.log`**: Main application log
- **`logs/health_monitor.log`**: Health monitoring log (if enabled)
- **Log rotation**: Automatic log rotation with size limits

### Log Levels
- **DEBUG**: Detailed debugging information
- **INFO**: General system information
- **WARNING**: Warning messages
- **ERROR**: Error conditions
- **CRITICAL**: Critical system errors

### Health Monitoring
If health monitoring is enabled:
- **Metrics endpoint**: `http://localhost:8080/metrics`
- **System metrics**: CPU, memory, temperature
- **Network metrics**: Connectivity, latency, speed
- **Stream metrics**: Availability, quality, bitrate

## 🔄 System Behavior

### Stream Monitoring
- **Check interval**: Configurable (default: 30 seconds)
- **API requests**: Automatic Vimeo API calls
- **Status detection**: Live/offline stream detection
- **Error handling**: Retry mechanisms for API failures

### Process Management
- **Auto-restart**: Automatic restart on failures
- **Health checks**: Regular process health monitoring
- **Graceful shutdown**: Proper cleanup on exit
- **Signal handling**: Responds to system signals

### Error Recovery
- **Retry logic**: Exponential backoff for failures
- **Fallback mechanisms**: Alternative error handling
- **Process recovery**: Automatic process restart
- **State management**: Maintains system state across restarts

## 🎛️ Control and Management

### Starting the System
```bash
# Basic start
uv run python -m vimeo_monitor

# With specific log level
LOG_LEVEL=DEBUG uv run python -m vimeo_monitor

# With health monitoring
HEALTH_MONITORING_ENABLED=true uv run python -m vimeo_monitor
```

### Stopping the System
- **Ctrl+C**: Graceful shutdown
- **SIGTERM**: Graceful shutdown
- **SIGKILL**: Force termination (not recommended)

### Restarting the System
```bash
# Stop and restart
# Press Ctrl+C to stop, then restart with:
uv run python -m vimeo_monitor
```

## 📈 Performance Optimization

### System Resources
- **CPU usage**: Optimized for Raspberry Pi
- **Memory usage**: Efficient memory management
- **Network usage**: Minimal API calls
- **Storage usage**: Log rotation and cleanup

### Monitoring Intervals
- **Stream checks**: Configurable interval (default: 30s)
- **Health checks**: Configurable interval (default: 60s)
- **Log rotation**: Automatic based on size limits

### Resource Management
- **Process limits**: Configurable restart limits
- **Memory limits**: Automatic cleanup and garbage collection
- **Network limits**: Timeout and retry configurations

## 🔧 Troubleshooting

### Common Issues

#### Stream Not Detected
- Check Vimeo API credentials
- Verify stream ID is correct
- Check network connectivity
- Review API rate limits

#### Display Issues
- Verify VLC installation
- Check display permissions
- Confirm media files exist
- Review display configuration

#### Performance Issues
- Monitor system resources
- Check log files for errors
- Adjust monitoring intervals
- Review configuration settings

### Getting Help
- **Logs**: Check `logs/vimeo_monitor.log`
- **Health metrics**: Visit `http://localhost:8080/metrics`
- **Configuration**: Review `.env` file settings
- **Documentation**: Check troubleshooting guide

## 📚 Related Documentation

- **[Quick Start](quick-start.md)** - Step-by-step setup
- **[Configuration](configuration.md)** - Complete configuration reference
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions
- **[Health Monitoring](health-monitoring.md)** - Monitoring and metrics
- **[API Reference](api-reference.md)** - Technical API details
