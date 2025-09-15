# Vimeo Monitor - Technical Context

## System Architecture

### Current Implementation
The Vimeo Monitor system has been refactored from a monolithic script into a modular, maintainable architecture with proper separation of concerns.

### Core Components

#### 1. Configuration Management (`config.py`)
- **Environment Variables**: Secure credential and configuration management
- **Path Resolution**: Automatic resolution of relative paths to project root
- **Validation**: Comprehensive configuration validation with helpful error messages
- **Security**: No hardcoded credentials in source code

#### 2. Logging System (`logger.py`)
- **Structured Logging**: Context-aware logging with module identification
- **File Rotation**: Automatic log rotation to prevent disk space issues
- **Multiple Handlers**: Console and file logging with configurable levels
- **Context Management**: LoggingContext for module-specific logging

#### 3. Process Management (`process_manager.py`)
- **VLC/FFmpeg Integration**: Manages external media processes
- **Health Monitoring**: Continuous process health checks
- **Auto-Recovery**: Automatic process restart on failures
- **State Management**: Tracks current process state and mode

#### 4. Monitoring System (`monitor.py`)
- **Vimeo API Integration**: Stream status detection and monitoring
- **Error Handling**: Comprehensive error handling with retry logic
- **Health Tracking**: System health monitoring and status reporting
- **Display Management**: Smart display switching based on stream status

### Stream Configuration

#### Stream Selection
```python
STREAM_SELECTION_MAP = {
    1: "4797083", 2: "4797084", 3: "4797085",
    4: "4797153", 5: "4797202", 6: "4797207"
}
```

#### Vimeo API Client Configuration
```python
# Vimeo API Client (Environment Variables)
client = VimeoClient(
    token="YOUR_VIMEO_TOKEN",
    key="YOUR_VIMEO_KEY",
    secret="YOUR_VIMEO_SECRET",
)
```

### Error Handling Strategy

#### Error Classification
- **ConnectionError**: Network connectivity issues
- **Timeout**: API request timeouts
- **RequestException**: General API errors
- **Process Errors**: VLC/FFmpeg process failures
- **Display Errors**: Display update failures

#### Retry Logic
- **Exponential Backoff**: 2^attempt seconds between retries
- **Configurable Retries**: MAX_RETRIES environment variable
- **Error Threshold**: Configurable threshold for showing error image
- **Graceful Degradation**: System continues running despite individual failures

#### Visual Error Feedback
- **Error Image**: Shows failure.png when system is unhealthy
- **State-Based Display**: Different images for different system states
- **Error Recovery**: Automatically returns to normal display when healthy

### Health Monitoring

#### Health Check Components
- **Uptime Tracking**: System uptime monitoring
- **Error Counting**: Consecutive error tracking
- **Success Tracking**: Time since last successful operation
- **Process Status**: VLC/FFmpeg process health
- **API Status**: Vimeo API connectivity

#### Health Reporting
- **Periodic Checks**: Health checks every 60 seconds
- **Status Logging**: Detailed health status logging
- **Warning System**: Warnings for unhealthy states
- **Recovery Tracking**: Automatic recovery detection

### Process Management

#### Process Types
- **Stream Process**: VLC for live stream playback
- **Image Process**: FFmpeg for static image display
- **Error Process**: FFmpeg for error image display

#### Process Lifecycle
1. **Start**: Initialize process with appropriate command
2. **Monitor**: Continuous health monitoring
3. **Recover**: Automatic restart on failures
4. **Stop**: Graceful shutdown on system exit

### Configuration Management

#### Environment Variables
```bash
# Vimeo API Credentials
VIMEO_TOKEN=your_vimeo_token
VIMEO_KEY=your_vimeo_key
VIMEO_SECRET=your_vimeo_secret

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
MAX_RETRIES=3
```

#### Path Resolution
- **Relative Paths**: Automatically resolved relative to project root
- **Absolute Paths**: Preserved as-is
- **Validation**: File existence validation for required paths

### Security Considerations

#### Credential Management
- **Environment Variables**: All credentials stored in environment variables
- **No Hardcoding**: No credentials in source code or documentation
- **Git Ignore**: .env files properly ignored by git
- **History Cleanup**: Sensitive information removed from git history

#### File Permissions
- **Log Files**: Appropriate permissions for log file access
- **Configuration**: Secure handling of configuration files
- **Process Security**: Safe process execution and management

### Performance Characteristics

#### Resource Usage
- **Memory**: Efficient memory usage with proper cleanup
- **CPU**: Minimal CPU overhead for monitoring
- **Disk**: Log rotation prevents disk space issues
- **Network**: Efficient API usage with retry logic

#### Scalability
- **Modular Design**: Easy to extend and modify
- **Configuration**: Flexible configuration for different environments
- **Error Handling**: Robust error handling for production use
- **Monitoring**: Comprehensive monitoring for system health

### Development Workflow

#### Build System
- **UV Package Manager**: Modern Python package management
- **Makefile**: Automated build and deployment tasks
- **Testing**: Comprehensive testing framework
- **Documentation**: Automated documentation generation

#### Quality Assurance
- **Code Quality**: Clean, maintainable code structure
- **Error Handling**: Comprehensive error handling and recovery
- **Testing**: Automated testing and validation
- **Documentation**: Comprehensive documentation and examples

### Deployment Considerations

#### Production Readiness
- **Error Recovery**: Automatic error recovery and system health
- **Monitoring**: Comprehensive system monitoring and alerting
- **Logging**: Structured logging for debugging and monitoring
- **Configuration**: Flexible configuration for different environments

#### Autostart Configuration
- **Desktop Files**: Proper autostart configuration for Linux
- **Service Management**: System service integration
- **Environment**: Proper environment variable handling
- **Recovery**: Automatic restart on system reboot

---

**Last Updated**: September 15, 2024  
**Status**: Phase 3 Complete - Production Ready Architecture  
**Security**: All sensitive information properly secured
