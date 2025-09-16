# API Reference

Complete reference for the Vimeo Monitor API and configuration.

## 📚 Core Modules

### Config Module
Configuration management and environment variable handling.

#### `Config` Class
Main configuration class that loads and validates environment variables.

```python
from src.vimeo_monitor.config import Config

config = Config()
```

**Properties:**
- `vimeo_access_token`: Vimeo API access token
- `vimeo_client_id`: Vimeo API client ID
- `vimeo_client_secret`: Vimeo API client secret
- `vimeo_stream_id`: Vimeo stream ID to monitor
- `stream_check_interval`: Interval for stream status checks (seconds)
- `log_level`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `log_file`: Path to log file
- `health_monitoring_enabled`: Enable health monitoring
- `health_metrics_port`: Port for health metrics server
- `health_metrics_host`: Host for health metrics server

### Monitor Module
Core monitoring functionality for Vimeo streams.

#### `Monitor` Class
Main monitoring class that handles Vimeo API interactions.

```python
from src.vimeo_monitor.monitor import Monitor

monitor = Monitor(config)
```

**Methods:**
- `check_stream_status()`: Check if stream is currently live
- `get_stream_url()`: Get stream URL if available
- `start_monitoring()`: Start continuous monitoring
- `stop_monitoring()`: Stop monitoring

### Process Manager Module
Process management and subprocess handling.

#### `ProcessManager` Class
Manages VLC and FFmpeg processes.

```python
from src.vimeo_monitor.process_manager import ProcessManager

process_manager = ProcessManager(config)
```

**Methods:**
- `start_video_process(stream_url)`: Start video playback process
- `start_holding_process()`: Start holding image display
- `start_failure_process()`: Start failure image display
- `stop_current_process()`: Stop current process
- `is_process_running()`: Check if process is running
- `get_process_status()`: Get current process status

## 🔧 Health Monitoring API

### Health Module
Optional health monitoring with Prometheus metrics.

#### `HealthModule` Class
Main health monitoring coordinator.

```python
from src.vimeo_monitor.health_module import HealthModule

health_module = HealthModule(config)
```

**Methods:**
- `start()`: Start health monitoring
- `stop()`: Stop health monitoring
- `get_metrics()`: Get current metrics
- `is_enabled()`: Check if health monitoring is enabled

### Metrics Collector
Prometheus metrics collection and formatting.

#### `MetricsCollector` Class
Collects and formats metrics for Prometheus.

```python
from src.vimeo_monitor.health.metrics_collector import MetricsCollector

collector = MetricsCollector()
```

**Methods:**
- `collect_metrics()`: Collect all metrics
- `format_metrics()`: Format metrics for Prometheus
- `get_metric_value(name)`: Get specific metric value

### System Monitor
Hardware and system resource monitoring.

#### `SystemMonitor` Class
Monitors system resources using psutil.

```python
from src.vimeo_monitor.health.system_monitor import SystemMonitor

system_monitor = SystemMonitor()
```

**Methods:**
- `get_cpu_usage()`: Get CPU usage percentage
- `get_memory_usage()`: Get memory usage percentage
- `get_temperature()`: Get system temperature
- `get_disk_usage()`: Get disk usage information

### Network Monitor
Network connectivity and performance monitoring.

#### `NetworkMonitor` Class
Monitors network connectivity and performance.

```python
from src.vimeo_monitor.health.network_monitor import NetworkMonitor

network_monitor = NetworkMonitor(config)
```

**Methods:**
- `check_connectivity()`: Check network connectivity
- `get_latency(host)`: Get latency to specific host
- `run_speedtest()`: Run speed test
- `get_network_status()`: Get overall network status

### Stream Monitor
Stream quality and availability monitoring.

#### `StreamMonitor` Class
Monitors stream quality using FFprobe.

```python
from src.vimeo_monitor.health.stream_monitor import StreamMonitor

stream_monitor = StreamMonitor(config)
```

**Methods:**
- `analyze_stream(stream_url)`: Analyze stream quality
- `get_stream_info()`: Get stream information
- `check_stream_availability()`: Check if stream is available
- `get_stream_metrics()`: Get stream metrics

## 📊 Prometheus Metrics

### Available Metrics

#### Script Health Metrics
- `vimeo_monitor_script_health`: Overall script health status
- `vimeo_monitor_api_requests_total`: Total API requests made
- `vimeo_monitor_stream_uptime_seconds`: Stream uptime in seconds

#### Hardware Metrics
- `vimeo_monitor_cpu_usage_percent`: CPU usage percentage
- `vimeo_monitor_memory_usage_percent`: Memory usage percentage
- `vimeo_monitor_temperature_celsius`: System temperature

#### Network Metrics
- `vimeo_monitor_network_connectivity`: Network connectivity status
- `vimeo_monitor_network_latency_ms`: Network latency in milliseconds
- `vimeo_monitor_network_speed_mbps`: Network speed in Mbps

#### Stream Metrics
- `vimeo_monitor_stream_availability`: Stream availability status
- `vimeo_monitor_stream_bitrate_kbps`: Stream bitrate in kbps
- `vimeo_monitor_stream_resolution`: Stream resolution

### Metrics Endpoint
Access metrics at: `http://localhost:8080/metrics`

## 🔧 Configuration API

### Environment Variables
All configuration is handled through environment variables.

#### Required Variables
```bash
VIMEO_ACCESS_TOKEN=your_token
VIMEO_CLIENT_ID=your_client_id
VIMEO_CLIENT_SECRET=your_client_secret
VIMEO_STREAM_ID=your_stream_id
```

#### Optional Variables
```bash
STREAM_CHECK_INTERVAL=30
LOG_LEVEL=INFO
LOG_FILE=logs/vimeo_monitor.log
HEALTH_MONITORING_ENABLED=false
HEALTH_METRICS_PORT=8080
HEALTH_METRICS_HOST=0.0.0.0
```

### Configuration Validation
The system automatically validates configuration on startup:

- **Required variables**: Must be present and non-empty
- **Numeric values**: Must be valid numbers within reasonable ranges
- **File paths**: Must be accessible and writable
- **Network settings**: Must be valid IP addresses or hostnames

## 🚀 Usage Examples

### Basic Monitoring
```python
from src.vimeo_monitor.config import Config
from src.vimeo_monitor.monitor import Monitor

# Load configuration
config = Config()

# Create monitor
monitor = Monitor(config)

# Start monitoring
monitor.start_monitoring()
```

### With Health Monitoring
```python
from src.vimeo_monitor.config import Config
from src.vimeo_monitor.monitor import Monitor
from src.vimeo_monitor.health_module import HealthModule

# Load configuration
config = Config()

# Create monitor
monitor = Monitor(config)

# Create health module
health_module = HealthModule(config)

# Start health monitoring
if health_module.is_enabled():
    health_module.start()

# Start monitoring
monitor.start_monitoring()
```

### Custom Configuration
```python
import os
from src.vimeo_monitor.config import Config

# Set custom environment variables
os.environ['VIMEO_ACCESS_TOKEN'] = 'your_token'
os.environ['VIMEO_STREAM_ID'] = 'your_stream_id'
os.environ['HEALTH_MONITORING_ENABLED'] = 'true'

# Load configuration
config = Config()

# Use configuration
print(f"Stream ID: {config.vimeo_stream_id}")
print(f"Health monitoring: {config.health_monitoring_enabled}")
```

## 📚 Related Documentation

- **[Configuration](configuration.md)** - Complete configuration reference
- **[Usage](usage.md)** - How to use the system
- **[Health Monitoring](health-monitoring.md)** - Health monitoring guide
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions
