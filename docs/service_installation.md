# Service Installation Guide

This guide explains how to install the Vimeo Monitor as a system service that starts automatically at boot.

## Overview

The Vimeo Monitor can be installed as a system service to run automatically in the background without requiring user interaction. This ensures continuous monitoring even after system reboots.

## Prerequisites

### System Requirements

- **Linux**: systemd-based distribution (Ubuntu 16.04+, CentOS 7+, Debian 8+)
- **macOS**: macOS 10.10+ with launchd
- **Root access**: Required for service installation

### Application Requirements

- Vimeo Monitor application must be properly configured
- Valid `.env` file with Vimeo API credentials
- All dependencies installed via `make install`

## Quick Installation

### Option 1: Complete Setup with Service

```bash
# Install application and service in one command
make setup-service
```

This command will:

1. Install uv package manager if needed
2. Create Python virtual environment
3. Install all dependencies
4. Install logrotate configuration
5. Install and enable the system service

### Option 2: Install Service Only

If you already have the application set up:

```bash
# Install only the service component
make install-service
```

## Manual Installation Process

### Step 1: Prepare the Application

```bash
# Ensure application is properly set up
make setup

# Verify configuration
make status
```

### Step 2: Install the Service

```bash
# Install as system service (requires sudo)
sudo make install-service
```

This will:

- Create a dedicated `vimeo-monitor` user and group
- Install the application to `/opt/vimeo-monitor`
- Set up proper file permissions and security
- Install the service configuration
- Enable automatic startup

### Step 3: Configure the Service

Edit the configuration file at `/opt/vimeo-monitor/.env`:

```bash
sudo nano /opt/vimeo-monitor/.env
```

Ensure the following are configured:

- `VIMEO_ACCESS_TOKEN`: Your Vimeo API access token
- `VIMEO_VIDEO_ID`: The video ID to monitor
- Other configuration settings as needed

### Step 4: Start the Service

```bash
# Start the service immediately
make service-start

# Check service status
make service-status
```

## Service Management

### Using Makefile Commands

```bash
# Check service status
make service-status

# Start the service
make service-start

# Stop the service
make service-stop

# Restart the service
make service-restart

# View service logs
make service-logs
```

### Direct System Commands

#### Linux (systemd)

```bash
# Service management
sudo systemctl start vimeo-monitor
sudo systemctl stop vimeo-monitor
sudo systemctl restart vimeo-monitor
sudo systemctl status vimeo-monitor

# Enable/disable automatic startup
sudo systemctl enable vimeo-monitor
sudo systemctl disable vimeo-monitor

# View logs
sudo journalctl -u vimeo-monitor -f
sudo journalctl -u vimeo-monitor --since "1 hour ago"
```

#### macOS (launchd)

```bash
# Service management
sudo launchctl load /Library/LaunchDaemons/com.vimeomonitor.service.plist
sudo launchctl unload /Library/LaunchDaemons/com.vimeomonitor.service.plist

# Check status
sudo launchctl list | grep vimeomonitor

# View logs
tail -f /opt/vimeo-monitor/logs/service.log
```

## Service Configuration

### Installation Locations

- **Application**: `/opt/vimeo-monitor/`
- **Configuration**: `/opt/vimeo-monitor/.env`
- **Logs**: `/opt/vimeo-monitor/logs/`
- **Backups**: `/opt/vimeo-monitor/config_backups/`
- **Service File (Linux)**: `/etc/systemd/system/vimeo-monitor.service`
- **Service File (macOS)**: `/Library/LaunchDaemons/com.vimeomonitor.service.plist`

### Service User

The service runs as a dedicated user:

- **User**: `vimeo-monitor`
- **Group**: `vimeo-monitor`
- **Home Directory**: `/opt/vimeo-monitor`
- **Shell**: `/bin/false` (no login)

### Security Features

The service includes several security hardening features:

- **File System Protection**: Read-only system files, limited write access
- **Network Restrictions**: Only necessary network protocols allowed
- **Process Isolation**: Private temporary directories, restricted privileges
- **Resource Limits**: Memory and file descriptor limits
- **System Call Filtering**: Only allowed system calls permitted

## Logging

### Log Locations

- **Service Logs (Linux)**: Available via `journalctl -u vimeo-monitor`
- **Service Logs (macOS)**: `/opt/vimeo-monitor/logs/service.log`
- **Application Logs**: `/opt/vimeo-monitor/logs/`

### Log Rotation

Automatic log rotation is configured via logrotate (installed with the service):

- **Rotation**: Daily
- **Retention**: 30 days
- **Compression**: Gzip after 1 day
- **Size Limit**: 100MB per log file

## Configuration Updates

### Updating Service Configuration

1. Stop the service:

   ```bash
   make service-stop
   ```

2. Edit configuration:

   ```bash
   sudo nano /opt/vimeo-monitor/.env
   ```

3. Restart the service:

   ```bash
   make service-start
   ```

### Updating Application Code

1. Stop the service:

   ```bash
   make service-stop
   ```

2. Update the installation:

   ```bash
   sudo make install-service
   ```

3. The service will restart automatically with the new code.

## Troubleshooting

### Service Won't Start

1. Check service status:

   ```bash
   make service-status
   ```

2. Check logs:

   ```bash
   make service-logs
   ```

3. Verify configuration:

   ```bash
   sudo cat /opt/vimeo-monitor/.env
   ```

4. Test manual execution:

   ```bash
   sudo -u vimeo-monitor /opt/vimeo-monitor/.venv/bin/python -m vimeo_monitor.monitor
   ```

### Configuration Issues

1. Verify `.env` file exists and is readable:

   ```bash
   sudo ls -la /opt/vimeo-monitor/.env
   ```

2. Check file permissions:

   ```bash
   sudo chown vimeo-monitor:vimeo-monitor /opt/vimeo-monitor/.env
   sudo chmod 640 /opt/vimeo-monitor/.env
   ```

3. Validate configuration syntax:

   ```bash
   sudo -u vimeo-monitor /opt/vimeo-monitor/.venv/bin/python -c "from vimeo_monitor.config import ConfigManager; ConfigManager()"
   ```

### Network Issues

1. Check network connectivity from service user:

   ```bash
   sudo -u vimeo-monitor ping -c 3 api.vimeo.com
   ```

2. Verify firewall settings allow outbound HTTPS connections

3. Check DNS resolution:

   ```bash
   sudo -u vimeo-monitor nslookup api.vimeo.com
   ```

### Permission Issues

1. Fix ownership of installation directory:

   ```bash
   sudo chown -R vimeo-monitor:vimeo-monitor /opt/vimeo-monitor
   ```

2. Ensure log directory is writable:

   ```bash
   sudo chmod 755 /opt/vimeo-monitor/logs
   ```

### Service Logs

Check system logs for service issues:

#### Linux

```bash
# Recent service logs
sudo journalctl -u vimeo-monitor --since "1 hour ago"

# Follow live logs
sudo journalctl -u vimeo-monitor -f

# Check for errors
sudo journalctl -u vimeo-monitor --since "1 hour ago" | grep -i error
```

#### macOS

```bash
# View recent logs
tail -100 /opt/vimeo-monitor/logs/service.log

# Follow live logs
tail -f /opt/vimeo-monitor/logs/service.log

# Check for errors
grep -i error /opt/vimeo-monitor/logs/service.log
```

## Uninstallation

### Complete Removal

```bash
# Uninstall the service and all components
make uninstall-service
```

This will:

- Stop and disable the service
- Remove the service configuration files
- Delete the installation directory
- Remove the service user and group
- Remove logrotate configuration
- Optionally backup logs before removal

### Service Only

To remove just the service but keep the application:

#### Linux

```bash
sudo systemctl stop vimeo-monitor
sudo systemctl disable vimeo-monitor
sudo rm /etc/systemd/system/vimeo-monitor.service
sudo systemctl daemon-reload
```

#### macOS

```bash
sudo launchctl unload /Library/LaunchDaemons/com.vimeomonitor.service.plist
sudo rm /Library/LaunchDaemons/com.vimeomonitor.service.plist
```

## Best Practices

### Monitoring the Service

1. **Regular Health Checks**: Monitor service status and logs
2. **Resource Monitoring**: Check CPU and memory usage
3. **Log Analysis**: Review logs for errors or unusual activity
4. **Configuration Backup**: Keep backups of working configurations

### Security Considerations

1. **Credentials**: Secure storage of API credentials
2. **Updates**: Keep the application and dependencies updated
3. **Access Control**: Limit access to service files and logs
4. **Network Security**: Use appropriate firewall rules

### Performance Optimization

1. **Log Rotation**: Ensure log rotation is working properly
2. **Resource Limits**: Adjust service resource limits if needed
3. **Monitoring Intervals**: Tune check intervals for your use case
4. **Network Configuration**: Optimize network monitoring settings

## Support

### Getting Help

1. **Check Logs**: Always start with service and application logs
2. **Verify Configuration**: Ensure all settings are correct
3. **Test Manually**: Try running the application manually first
4. **Documentation**: Review this guide and application documentation

### Common Commands Reference

```bash
# Installation
make setup-service              # Complete setup with service
make install-service           # Install service only

# Management
make service-status           # Check status
make service-start           # Start service
make service-stop            # Stop service
make service-restart         # Restart service
make service-logs           # View logs

# Maintenance
make status                 # Check system status
make clean-logs            # Clean old logs
make force-logrotate       # Force log rotation

# Removal
make uninstall-service     # Complete removal
```

This comprehensive service installation provides a robust, secure, and maintainable way to run the Vimeo Monitor as a system service with automatic startup at boot.
