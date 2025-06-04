# Vimeo Monitor Architecture

## Overview

The Vimeo Monitor application has been refactored into a clean, modular architecture with clear separation of concerns and dependency injection. This document describes the architecture, components, and their interactions.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        MonitorApp                               │
│                   (Main Orchestrator)                          │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ ConfigMgr   │  │ HealthMon   │  │ VimeoClient │            │
│  │             │  │             │  │             │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│         │                 │                 │                  │
│         └─────────────────┼─────────────────┘                  │
│                           │                                    │
│                  ┌─────────────┐                               │
│                  │ StreamMgr   │                               │
│                  │             │                               │
│                  └─────────────┘                               │
└─────────────────────────────────────────────────────────────────┘
│
├── NetworkStatusOverlay (Optional GUI/Terminal)
└── External Process Management (ffplay)
```

## Components

### 1. ConfigManager (`vimeo_monitor/config.py`)

**Purpose**: Centralized configuration management with validation and type conversion.

**Responsibilities**:

- Load environment variables from `.env` files
- Validate required configuration
- Provide type-safe property access to configuration values
- Support for different data types (str, int, float, bool)
- Descriptive error messages for missing configuration

**Key Features**:

- Property-based access: `config.check_interval`
- Type conversion: `CHECK_INTERVAL=30` → `int(30)`
- Boolean parsing: `"true"/"false"/"1"/"0"` → `bool`
- Path validation for image files
- Configuration summary for logging

**Example Usage**:

```python
config = ConfigManager(".env")
print(f"Stream ID: {config.vimeo_stream_id}")
print(f"Check interval: {config.check_interval} seconds")
print(f"API backoff enabled: {config.api_enable_backoff}")
```

### 2. HealthMonitor (`vimeo_monitor/health.py`)

**Purpose**: Track API health, failure states, and provide comprehensive health reporting.

**Responsibilities**:

- Track consecutive API failures and successes
- Manage API failure mode state
- Calculate exponential backoff intervals
- Provide comprehensive health metrics
- Generate health status reports

**Key Features**:

- Failure threshold detection
- Stability threshold for recovery
- Response time tracking
- Failure rate calculation
- Detailed health status reporting

**Example Usage**:

```python
health = HealthMonitor(config)
health.handle_api_failure("timeout", "Request timed out")
health.handle_api_success(0.25)  # 250ms response time

status = health.get_health_status()
print(f"Failure rate: {status['failure_rate_percent']}%")
```

### 3. VimeoAPIClient (`vimeo_monitor/client.py`)

**Purpose**: Handle all Vimeo API interactions with comprehensive error handling.

**Responsibilities**:

- Make HTTP requests to Vimeo API
- Handle HTTP status codes and errors
- Parse and validate API responses
- Extract stream URLs and status
- Integrate with HealthMonitor for failure tracking

**Key Features**:

- Comprehensive HTTP error handling (401, 403, 404, 429, 5xx)
- Response validation and parsing
- Stream activity detection
- Response time measurement
- Clear error categorization

**Example Usage**:

```python
client = VimeoAPIClient(config, health_monitor)
response_data = client.get_stream_data()

if client.is_stream_active(response_data):
    url = client.get_stream_url(response_data)
    print(f"Stream URL: {url}")
```

### 4. StreamManager (`vimeo_monitor/stream.py`)

**Purpose**: Manage media playback processes and mode switching.

**Responsibilities**:

- Determine appropriate mode (stream/image/api_failure)
- Start and stop media playback processes
- Handle mode transitions
- Monitor process health
- Validate media file paths

**Key Features**:

- Mode determination logic
- Graceful process termination
- Process health monitoring
- Media path validation
- Enhanced process logging

**Example Usage**:

```python
stream = StreamManager(config, health_monitor)
mode = stream.determine_mode(api_response)
stream.handle_mode_change(mode, api_response)
stream.check_process_health()
```

### 5. MonitorApp (`vimeo_monitor/monitor.py`)

**Purpose**: Main orchestrator that coordinates all components using dependency injection.

**Responsibilities**:

- Initialize all components with proper dependencies
- Orchestrate the main monitoring loop
- Handle application startup and shutdown
- Manage the network status overlay
- Provide external control interface

**Key Features**:

- Dependency injection pattern
- Structured startup/shutdown
- Exception handling and recovery
- Component health validation
- External control interface

**Example Usage**:

```python
app = MonitorApp(".env")
app.start()  # Runs until interrupted
```

## Data Flow

### 1. Application Startup

```
MonitorApp.__init__()
├── ConfigManager(env_file) → Load and validate configuration
├── HealthMonitor(config) → Initialize health tracking
├── VimeoAPIClient(config, health) → Setup API client
├── StreamManager(config, health) → Initialize process manager
└── NetworkStatusOverlay(...) → Optional status display
```

### 2. Main Loop

```
MonitorApp._run_monitoring_loop()
├── VimeoAPIClient.get_stream_data() → API request
│   ├── Success → HealthMonitor.handle_api_success()
│   └── Failure → HealthMonitor.handle_api_failure()
├── StreamManager.determine_mode(response) → Mode decision
├── StreamManager.handle_mode_change() → Process management
├── StreamManager.check_process_health() → Process monitoring
└── Wait for next iteration
```

### 3. Error Handling Flow

```
API Error
├── VimeoAPIClient categorizes error type
├── HealthMonitor tracks failure
├── If threshold exceeded → Enter failure mode
├── StreamManager switches to failure image
└── Exponential backoff for next retry
```

## Configuration

### Environment Variables

The application uses the following environment variables (see `.env.sample` for full list):

**Required**:

- `VIMEO_TOKEN`: API authentication token
- `VIMEO_KEY`: API key
- `VIMEO_SECRET`: API secret
- `VIMEO_STREAM_ID`: Stream identifier

**Optional**:

- `CHECK_INTERVAL`: Seconds between checks (default: 30)
- `API_FAILURE_THRESHOLD`: Failures before failure mode (default: 3)
- `DISPLAY_NETWORK_STATUS`: Enable overlay (default: true)
- And many more...

### Configuration Loading

1. ConfigManager loads from specified `.env` file
2. Environment variables are parsed with type conversion
3. Required variables are validated
4. Optional file paths are checked
5. Configuration summary is generated for logging

## Error Handling

### Levels of Error Handling

1. **Configuration Level**: Missing required environment variables
2. **API Level**: Network errors, HTTP errors, response validation
3. **Process Level**: Media player failures, process crashes
4. **Application Level**: Unexpected exceptions, graceful shutdown

### Error Recovery

- **API Failures**: Exponential backoff, failure mode, alternative images
- **Process Failures**: Automatic restart, mode reset
- **Configuration Errors**: Immediate exit with descriptive messages
- **Unexpected Errors**: Logged with full traceback, continue operation

## Testing

### Unit Testing

Each component can be tested independently:

```python
# Test ConfigManager
config = ConfigManager("test.env")
assert config.check_interval == 30

# Test HealthMonitor
health = HealthMonitor(config)
health.handle_api_failure("timeout", "Test error")
assert health.api_failure_count == 1

# Test VimeoAPIClient
client = VimeoAPIClient(config, health)
assert client.validate_configuration() == True
```

### Integration Testing

Full application flow can be tested:

```python
app = MonitorApp("test.env")
assert app.config is not None
assert app.health_monitor is not None
app.stop()
```

## Future Extensions

### 1. Enhanced Configuration Management (TASK-008)

- YAML/TOML support
- Live configuration reload
- Configuration validation schemas
- Environment-specific configurations

### 2. Terminal User Interface (TASK-004)

- Real-time status dashboard
- Interactive configuration
- Command interface
- Integration with existing components

### 3. Additional Monitoring

- Performance metrics
- Resource usage tracking
- Historical data storage
- Alerting systems

## Migration from Legacy Code

The refactoring maintains complete backward compatibility:

### Before (Monolithic)

```python
# Everything in one file
def main():
    setup_logging()
    validate_configuration()
    # ... 500+ lines of mixed concerns
```

### After (Modular)

```python
# Clean separation of concerns
def main():
    app = MonitorApp()
    app.start()
```

### Benefits

1. **Maintainability**: Each component has a single responsibility
2. **Testability**: Components can be tested in isolation
3. **Extensibility**: New features can be added without modifying existing code
4. **Reliability**: Better error handling and recovery
5. **Documentation**: Self-documenting code structure

## Deployment

The refactored application deploys identically to the original:

```bash
# Same command-line interface
uv run python -m vimeo_monitor.monitor

# Same configuration files
cp .env.sample .env
# Edit .env with your settings

# Same dependencies
uv install
```

No changes required to existing deployment scripts or documentation.
