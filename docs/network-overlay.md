# Network Status Overlay Documentation

## Overview

The Vimeo Monitor Network Status Overlay provides real-time visual feedback about the application's network connectivity, API health, and stream status directly on your screen. This lightweight overlay system runs independently of the main video stream and provides instant visibility into system health.

## Features

### Real-Time Status Display

- **API Connection Status**: Visual indicators for healthy/failing/recovering states
- **Stream Status**: Current mode (active/inactive/buffering/failure)
- **Network Health**: Connection status and stability metrics
- **Performance Metrics**: Failure rates, request counts, response times
- **Uptime Tracking**: Application runtime and last successful connection times

### Visual Indicators

- 🟢 **Green**: Healthy operation
- 🟡 **Yellow**: Warning states (standby, degraded performance)
- 🔴 **Red**: Critical issues (API failures, connection problems)
- ✅ **Checkmarks**: Successful operations
- ❌ **X marks**: Failed operations

## Configuration

### Environment Variables

Add these variables to your `.env` file to configure the overlay:

```env
# Enable/Disable Overlay
DISPLAY_NETWORK_STATUS=true          # true/false

# Positioning
OVERLAY_POSITION=top-right           # top-left, top-right, bottom-left, bottom-right

# Visual Properties
OVERLAY_OPACITY=0.8                  # 0.0 (transparent) to 1.0 (opaque)

# Update Frequency
OVERLAY_UPDATE_INTERVAL=2            # Update interval in seconds

# Auto-Hide Feature
OVERLAY_AUTO_HIDE=false              # Hide overlay when stream is healthy
```

### Positioning Options

- **top-left**: Upper left corner of screen
- **top-right**: Upper right corner of screen (default)
- **bottom-left**: Lower left corner of screen
- **bottom-right**: Lower right corner of screen

## Status Information

### Mode Display

Shows the current operating mode:

- **stream**: Video stream is active and playing
- **image**: Displaying static holding image
- **api_failure**: API connection failed, showing failure image

### API Status

Displays API connection health:

- **✅ Healthy (X)**: API functioning normally with X consecutive successes
- **❌ Failing (X)**: API experiencing failures with X consecutive failures

### Stream Status

Current stream state:

- **🟢 Active**: Stream is live and playing
- **🟡 Standby**: Showing holding image, waiting for stream
- **🔴 API Failure**: API connection issues preventing stream

### Failure Information

Shows failure statistics:

- **Failure Rate**: Percentage of failed requests
- **Total Requests**: Total API requests since startup

### Timing Information

- **Last Success**: Time since last successful API call
- **Uptime**: Total application runtime

## Usage Examples

### Basic Usage

Simply set `DISPLAY_NETWORK_STATUS=true` in your `.env` file. The overlay will automatically start when you run the monitor:

```bash
uv run -m vimeo_monitor.monitor
```

### Custom Positioning

Position overlay in bottom-left corner:

```env
DISPLAY_NETWORK_STATUS=true
OVERLAY_POSITION=bottom-left
```

### Minimal Overlay

Create a subtle overlay that auto-hides when healthy:

```env
DISPLAY_NETWORK_STATUS=true
OVERLAY_OPACITY=0.6
OVERLAY_AUTO_HIDE=true
```

### High-Frequency Monitoring

For real-time monitoring during troubleshooting:

```env
DISPLAY_NETWORK_STATUS=true
OVERLAY_UPDATE_INTERVAL=1
OVERLAY_AUTO_HIDE=false
```

## Integration with Main Application

### Automatic Lifecycle Management

The overlay automatically:

- Starts when the monitor application starts
- Updates in real-time based on API health
- Responds to mode changes (stream/image/failure)
- Stops gracefully when the application shuts down

### Thread Safety

- Runs in separate thread to avoid blocking main application
- Uses thread-safe communication with main monitor process
- Graceful error handling prevents overlay issues from affecting stream

### Resource Usage

- Minimal CPU usage (typically <1%)
- Low memory footprint (~10-20MB)
- No impact on video stream performance

## Troubleshooting

### Overlay Not Appearing

1. **Check Configuration**:

   ```bash
   grep DISPLAY_NETWORK_STATUS .env
   ```

   Ensure it's set to `true`.

2. **Verify GUI Support**:
   The overlay requires a graphical environment. Check if tkinter is available:

   ```bash
   python3 -c "import tkinter; print('tkinter available')"
   ```

3. **Check Log Messages**:
   Look for overlay initialization messages in the logs:

   ```
   Network status overlay initialized: enabled=True, position=top-right
   Network status overlay started
   ```

### Overlay Not Updating

1. **Check Update Interval**:
   Very high values (>30 seconds) may make updates seem slow.

2. **Verify API Status**:
   If the main application isn't running properly, the overlay won't have data to display.

3. **Check for Errors**:
   Look for overlay-specific errors in the logs:

   ```
   Error updating overlay: ...
   Error in overlay thread: ...
   ```

### Position Issues

1. **Multiple Monitors**:
   The overlay positions based on the primary monitor. For multi-monitor setups, it may appear on the wrong screen.

2. **High DPI Displays**:
   On high-DPI displays, the overlay may appear smaller than expected.

### Performance Issues

1. **Reduce Update Frequency**:

   ```env
   OVERLAY_UPDATE_INTERVAL=5  # Update every 5 seconds instead of 2
   ```

2. **Enable Auto-Hide**:

   ```env
   OVERLAY_AUTO_HIDE=true  # Hide when system is healthy
   ```

## Advanced Configuration

### Development/Debugging Mode

For development or detailed monitoring:

```env
DISPLAY_NETWORK_STATUS=true
OVERLAY_POSITION=top-left
OVERLAY_OPACITY=0.9
OVERLAY_UPDATE_INTERVAL=1
OVERLAY_AUTO_HIDE=false
LOG_LEVEL=DEBUG
```

### Production Mode

For production with minimal visual impact:

```env
DISPLAY_NETWORK_STATUS=true
OVERLAY_POSITION=bottom-right
OVERLAY_OPACITY=0.7
OVERLAY_UPDATE_INTERVAL=3
OVERLAY_AUTO_HIDE=true
```

### Monitoring Station Setup

For dedicated monitoring displays:

```env
DISPLAY_NETWORK_STATUS=true
OVERLAY_POSITION=top-right
OVERLAY_OPACITY=1.0
OVERLAY_UPDATE_INTERVAL=1
OVERLAY_AUTO_HIDE=false
```

## Integration with Logging

The overlay system integrates with the main application's logging system:

- Startup and shutdown events are logged
- Configuration changes are logged
- Errors are logged with appropriate detail levels
- Performance metrics can be tracked through log analysis

## Security Considerations

- The overlay displays no sensitive information (API keys, tokens, etc.)
- All displayed data is aggregated status information
- No user input is accepted through the overlay interface
- The overlay cannot be used to control the main application

## Future Enhancements

Potential future features include:

- Click-to-hide functionality
- Customizable display fields
- Color theme options
- Integration with system notifications
- Historical trend displays
- Export status to external monitoring systems
