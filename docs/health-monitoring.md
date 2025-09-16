# Health Monitoring System

The Vimeo Monitor includes a comprehensive health monitoring system that provides Prometheus-compatible metrics for monitoring the health of the application, hardware, network, and stream. This document explains how to enable, configure, and use the health monitoring system.

## Overview

The health monitoring system provides the following features:

- **Script Health Monitoring**: Monitors the health of the Vimeo Monitor application, including API status, error counts, and stream status.
- **Hardware Health Monitoring**: Monitors CPU usage, memory usage, temperature, and disk space.
- **Network Health Monitoring**: Monitors network connectivity, latency, and speed.
- **Stream Health Monitoring**: Monitors stream availability, bitrate, resolution, and other stream-related metrics using FFprobe.

All metrics are exposed via a Prometheus-compatible `/metrics` endpoint that can be scraped by Prometheus or other monitoring systems.

## Installation

The health monitoring system is an optional feature of the Vimeo Monitor. To install it, you need to install the additional dependencies:

```bash
# Using uv (recommended)
uv sync --extra health

# Using pip
pip install -e ".[health]"
```

The health monitoring system requires the following dependencies:

- `fastapi`: Web framework for the metrics endpoint
- `uvicorn`: ASGI server for FastAPI
- `psutil`: System monitoring library
- `prometheus-client`: Prometheus client library
- `speedtest-cli`: Network speed testing library
- `requests`: HTTP client library

Additionally, the stream monitoring component requires `ffprobe` (part of FFmpeg) to be installed on the system:

```bash
sudo apt install ffmpeg
```

## Configuration

The health monitoring system is disabled by default. To enable it, set the following environment variable in your `.env` file:

```env
HEALTH_MONITORING_ENABLED=true
```

The following configuration options are available:

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `HEALTH_MONITORING_ENABLED` | Enable/disable health monitoring | `false` |
| `HEALTH_METRICS_PORT` | Port for the metrics endpoint | `8080` |
| `HEALTH_METRICS_HOST` | Host for the metrics endpoint | `0.0.0.0` |
| `HEALTH_HARDWARE_INTERVAL` | Interval for hardware metrics collection (seconds) | `10` |
| `HEALTH_NETWORK_INTERVAL` | Interval for network metrics collection (seconds) | `30` |
| `HEALTH_STREAM_INTERVAL` | Interval for stream metrics collection (seconds) | `60` |
| `HEALTH_HARDWARE_ENABLED` | Enable/disable hardware monitoring | `true` |
| `HEALTH_NETWORK_ENABLED` | Enable/disable network monitoring | `true` |
| `HEALTH_STREAM_ENABLED` | Enable/disable stream monitoring | `true` |
| `HEALTH_NETWORK_PING_HOSTS` | Comma-separated list of hosts to ping | `8.8.8.8,1.1.1.1,vimeo.com` |
| `HEALTH_NETWORK_SPEEDTEST_ENABLED` | Enable/disable speed testing | `true` |
| `HEALTH_NETWORK_SPEEDTEST_INTERVAL` | Interval for speed testing (seconds) | `300` |
| `HEALTH_STREAM_FFPROBE_TIMEOUT` | Timeout for FFprobe analysis (seconds) | `15` |

## Usage

Once the health monitoring system is enabled and the Vimeo Monitor is running, you can access the metrics endpoint at:

```
http://<your-ip>:8080/metrics
```

The metrics are in Prometheus format and can be scraped by Prometheus or other monitoring systems.

### Prometheus Configuration

To configure Prometheus to scrape metrics from the Vimeo Monitor, add the following to your `prometheus.yml` file:

```yaml
scrape_configs:
  - job_name: 'vimeo_monitor'
    scrape_interval: 15s
    static_configs:
      - targets: ['<your-ip>:8080']
```

Replace `<your-ip>` with the IP address of the machine running the Vimeo Monitor.

## Available Metrics

The health monitoring system provides the following metrics:

### Script Health Metrics

| Metric | Description |
|--------|-------------|
| `vimeo_monitor_script_health` | Health status of the Vimeo Monitor script (1=healthy, 0=unhealthy) |
| `vimeo_monitor_uptime_seconds` | Uptime of the Vimeo Monitor application in seconds |
| `vimeo_monitor_api_requests_total` | Total number of API requests made |
| `vimeo_monitor_api_errors_total` | Total number of API errors encountered |
| `vimeo_monitor_stream_status` | Current stream status (1=live, 0=offline, -1=error) |
| `vimeo_monitor_stream_uptime_seconds` | Stream uptime in seconds |
| `vimeo_monitor_consecutive_errors` | Number of consecutive errors encountered |
| `vimeo_monitor_time_since_last_success_seconds` | Time since last successful API check in seconds |

### Hardware Health Metrics

| Metric | Description |
|--------|-------------|
| `vimeo_monitor_cpu_usage_percent` | CPU usage in percent |
| `vimeo_monitor_cpu_temperature_celsius` | CPU temperature in Celsius (Raspberry Pi only) |
| `vimeo_monitor_cpu_load_1` | CPU load average (1 minute) |
| `vimeo_monitor_cpu_load_5` | CPU load average (5 minutes) |
| `vimeo_monitor_cpu_load_15` | CPU load average (15 minutes) |
| `vimeo_monitor_memory_usage_percent` | Memory usage in percent |
| `vimeo_monitor_memory_available_bytes` | Available memory in bytes |
| `vimeo_monitor_memory_total_bytes` | Total memory in bytes |
| `vimeo_monitor_disk_usage_percent` | Disk usage in percent (labeled by mountpoint) |
| `vimeo_monitor_disk_free_bytes` | Free disk space in bytes (labeled by mountpoint) |
| `vimeo_monitor_process_cpu_percent` | CPU usage of the Vimeo Monitor process in percent |
| `vimeo_monitor_process_memory_percent` | Memory usage of the Vimeo Monitor process in percent |

### Network Health Metrics

| Metric | Description |
|--------|-------------|
| `vimeo_monitor_network_connectivity` | Network connectivity status (1=connected, 0=disconnected) (labeled by host) |
| `vimeo_monitor_network_latency_ms` | Network latency in milliseconds (labeled by host) |
| `vimeo_monitor_network_download_mbps` | Network download speed in Mbps |
| `vimeo_monitor_network_upload_mbps` | Network upload speed in Mbps |
| `vimeo_monitor_network_ping_ms` | Network ping speed in milliseconds |
| `vimeo_monitor_network_dns_resolution_ms` | DNS resolution time in milliseconds (labeled by domain) |

### Stream Health Metrics

| Metric | Description |
|--------|-------------|
| `vimeo_monitor_stream_availability` | Stream availability (1=available, 0=unavailable) |
| `vimeo_monitor_stream_bitrate_kbps` | Stream bitrate in kbps |
| `vimeo_monitor_stream_width_pixels` | Stream width in pixels |
| `vimeo_monitor_stream_height_pixels` | Stream height in pixels |
| `vimeo_monitor_stream_framerate_fps` | Stream framerate in fps |
| `vimeo_monitor_stream_audio_channels` | Number of audio channels |
| `vimeo_monitor_stream_audio_sample_rate_hz` | Audio sample rate in Hz |
| `vimeo_monitor_stream_analysis_time_seconds` | Time taken to analyze stream in seconds |

## Troubleshooting

### Metrics Endpoint Not Available

If the metrics endpoint is not available, check the following:

1. Make sure health monitoring is enabled in your `.env` file: `HEALTH_MONITORING_ENABLED=true`
2. Make sure the health monitoring dependencies are installed: `uv sync --extra health`
3. Check the logs for any errors related to health monitoring: `tail -f logs/stream_monitor.log`
4. Make sure the port is not already in use by another application: `sudo lsof -i :8080`
5. Check if the application is running: `ps aux | grep streammonitor.py`

### Missing Hardware Metrics

If hardware metrics are missing, check the following:

1. Make sure hardware monitoring is enabled: `HEALTH_HARDWARE_ENABLED=true`
2. Make sure the `psutil` library is installed: `uv sync --extra health`
3. Check the logs for any errors related to hardware monitoring: `tail -f logs/stream_monitor.log`

### Missing Network Metrics

If network metrics are missing, check the following:

1. Make sure network monitoring is enabled: `HEALTH_NETWORK_ENABLED=true`
2. Make sure the `requests` library is installed: `uv sync --extra health`
3. Check the logs for any errors related to network monitoring: `tail -f logs/stream_monitor.log`
4. If speed test metrics are missing, make sure speed testing is enabled: `HEALTH_NETWORK_SPEEDTEST_ENABLED=true`
5. Make sure the `speedtest-cli` library is installed: `uv sync --extra health`

### Missing Stream Metrics

If stream metrics are missing, check the following:

1. Make sure stream monitoring is enabled: `HEALTH_STREAM_ENABLED=true`
2. Make sure `ffprobe` is installed: `sudo apt install ffmpeg`
3. Check the logs for any errors related to stream monitoring: `tail -f logs/stream_monitor.log`
4. Make sure the stream is active and accessible

## Performance Considerations

The health monitoring system is designed to have minimal impact on the performance of the Vimeo Monitor application. However, some metrics collection can be resource-intensive, especially on low-powered devices like the Raspberry Pi.

To minimize resource usage, consider the following:

1. Increase the collection intervals for resource-intensive metrics:
   ```env
   HEALTH_HARDWARE_INTERVAL=30
   HEALTH_NETWORK_INTERVAL=60
   HEALTH_STREAM_INTERVAL=120
   ```

2. Disable speed testing or increase the interval:
   ```env
   HEALTH_NETWORK_SPEEDTEST_ENABLED=false
   # or
   HEALTH_NETWORK_SPEEDTEST_INTERVAL=600
   ```

3. Disable monitoring components you don't need:
   ```env
   HEALTH_HARDWARE_ENABLED=false
   HEALTH_NETWORK_ENABLED=false
   HEALTH_STREAM_ENABLED=false
   ```

4. Reduce the number of ping hosts:
   ```env
   HEALTH_NETWORK_PING_HOSTS=8.8.8.8
   ```

5. Decrease the FFprobe timeout:
   ```env
   HEALTH_STREAM_FFPROBE_TIMEOUT=5
   ```
