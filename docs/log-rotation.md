# Log Rotation System

The Vimeo Monitor includes a comprehensive log rotation system to manage log files and prevent disk space issues. This system provides both Python-based automatic rotation and system-level log management.

## Features

### 🔄 Automatic Log Rotation

- **Size-based rotation**: Automatically rotates logs when they reach a configured size
- **Configurable backup count**: Keeps a specified number of backup files
- **Enhanced logging format**: Includes function names and line numbers for better debugging

### 🛠️ System-level Log Management

- **Logrotate integration**: Works with system logrotate for scheduled rotation
- **Compression support**: Automatically compresses old log files
- **Advanced log analysis**: Provides detailed statistics and insights

### 📊 Log Management Tools

- **Manual rotation**: Force log rotation when needed
- **Log compression**: Compress old logs to save space
- **Log analysis**: Detailed reports on log file usage
- **Automated cleanup**: Remove old logs based on age

## Configuration

### Environment Variables

Add these settings to your `.env` file:

```env
# Log rotation settings (Python RotatingFileHandler)
LOG_ROTATE_MAX_SIZE=10485760    # Maximum log file size in bytes (10MB default)
LOG_ROTATE_BACKUP_COUNT=5       # Number of backup log files to keep (5 default)
```

### Default Values

- **Max file size**: 10MB (10,485,760 bytes)
- **Backup count**: 5 files
- **Log format**: Enhanced with function names and line numbers

## Usage

### Automatic Rotation

Log rotation happens automatically when the current log file reaches the configured size:

```
vimeo_monitor.logs         # Current log file
vimeo_monitor.logs.1       # Most recent backup
vimeo_monitor.logs.2       # Second most recent backup
vimeo_monitor.logs.3       # Third most recent backup
vimeo_monitor.logs.4       # Fourth most recent backup
vimeo_monitor.logs.5       # Oldest backup (will be deleted on next rotation)
```

### Manual Log Management

#### Install System Log Rotation

```bash
make install-logrotate
```

This installs the logrotate configuration to `/etc/logrotate.d/vimeo-monitor`.

#### Analyze Log Files

```bash
make analyze-logs
```

Provides detailed statistics about your log files:

```
📊 Log Analysis Report for logs
==================================================
📁 Total log files: 3
📦 Compressed files: 1
📄 Uncompressed files: 2
💾 Total size: 15.2 MB (15,923,456 bytes)
🕐 Oldest log: 2024-01-15 09:30:15
🕐 Newest log: 2024-01-20 14:22:33
```

#### Compress Log Files

```bash
make compress-logs
```

Compresses old log files to save disk space.

#### Force Log Rotation

```bash
make rotate-logs
```

Manually triggers log rotation.

#### Clean Old Logs

```bash
make clean-old-logs
```

Removes log files older than 30 days.

#### Test Logrotate Configuration

```bash
make test-logrotate
```

Tests the system logrotate configuration without actually rotating files.

### Advanced Log Management

Use the log management utility directly for more control:

```bash
# Analyze logs in a specific directory
uv run python services/log_management.py analyze --log-dir /path/to/logs

# Rotate a specific log file
uv run python services/log_management.py rotate --file mylog.log --max-size 5242880

# Compress logs matching a pattern
uv run python services/log_management.py compress --pattern "*.log.*"

# Clean logs older than 14 days
uv run python services/log_management.py clean --days 14
```

## System Integration

### Systemd Service

The log rotation system works seamlessly with systemd services. The logrotate configuration includes signal handling to properly reopen log files after rotation.

### Cron Integration

System logrotate typically runs daily via cron. You can check the schedule:

```bash
cat /etc/cron.daily/logrotate
```

### Manual System Rotation

Force system-wide log rotation:

```bash
sudo logrotate -f /etc/logrotate.d/vimeo-monitor
```

## Log Format

The enhanced logging format provides more detailed information:

```
2025-06-04 11:38:36,951 - root - INFO - setup_logging:108 - Log rotation configured: max_size=10485760 bytes, backup_count=5
```

Format components:

- **Timestamp**: `2025-06-04 11:38:36,951`
- **Logger name**: `root`
- **Level**: `INFO`
- **Function**: `setup_logging:108` (function name and line number)
- **Message**: Actual log message

## Troubleshooting

### Log Rotation Not Working

1. Check file permissions on the log directory
2. Verify the `LOG_ROTATE_MAX_SIZE` setting
3. Ensure sufficient disk space
4. Check for file system errors

### Large Log Files

If logs are growing too quickly:

1. Reduce `LOG_ROTATE_MAX_SIZE`
2. Increase rotation frequency
3. Adjust log level to reduce verbosity
4. Enable compression earlier

### System Logrotate Issues

1. Check logrotate configuration syntax:

   ```bash
   sudo logrotate -d /etc/logrotate.d/vimeo-monitor
   ```

2. Verify file paths in the configuration
3. Check system logs for logrotate errors:

   ```bash
   sudo journalctl -u logrotate
   ```

## Performance Considerations

### File I/O Impact

- Log rotation happens quickly with minimal service interruption
- Compression occurs asynchronously and doesn't block logging
- Consider SSD storage for high-frequency logging

### Disk Space Management

- Monitor total log space usage
- Adjust backup count based on available storage
- Use compression for long-term log retention

### Network Considerations

- Large log files can impact backup systems
- Consider remote log shipping for production systems
- Implement log aggregation for multiple instances

## Best Practices

1. **Regular Monitoring**: Use `make analyze-logs` to monitor log growth
2. **Appropriate Sizing**: Set max file size based on your storage and analysis needs
3. **Retention Policy**: Balance backup count with storage constraints
4. **Compression**: Enable compression for logs older than current rotation
5. **Monitoring Integration**: Include log metrics in your monitoring system
6. **Backup Strategy**: Include rotated logs in your backup procedures

## Files and Locations

### Configuration Files

- `services/logrotation.conf`: System logrotate configuration
- `.env`: Application log rotation settings

### Management Scripts

- `services/log_management.py`: Advanced log management utility
- `Makefile`: Log management targets

### Log Files Location

- `./logs/`: Default log directory
- `/var/log/vimeo-monitor/`: System installation location
- `/home/*/logs/`: User-specific installations

## Migration from Old Logging

If upgrading from a version without log rotation:

1. Existing logs will continue to work
2. New rotation settings apply to new log entries
3. Use `make analyze-logs` to assess current log usage
4. Consider compressing existing large log files manually
5. Update backup scripts to account for multiple log files
