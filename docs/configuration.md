# Configuration

The Vimeo Monitor uses environment variables for all configuration settings. This approach provides security, flexibility, and easy deployment across different environments.

## 🔧 Environment Variables

### Required Configuration

#### Vimeo API Credentials
```bash
# Vimeo API credentials (required)
VIMEO_ACCESS_TOKEN=your_vimeo_access_token_here
VIMEO_CLIENT_ID=your_vimeo_client_id_here
VIMEO_CLIENT_SECRET=your_vimeo_client_secret_here
```

#### Stream Configuration
```bash
# Stream settings (required)
VIMEO_STREAM_ID=your_stream_id_here
STREAM_CHECK_INTERVAL=30
```

### Optional Configuration

#### Logging Configuration
```bash
# Logging settings (optional)
LOG_LEVEL=INFO
LOG_FILE=logs/vimeo_monitor.log
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

#### Process Management
```bash
# Process management (optional)
PROCESS_RESTART_DELAY=5
PROCESS_MAX_RESTARTS=10
PROCESS_HEALTH_CHECK_INTERVAL=60
```

#### Display Configuration
```bash
# Display settings (optional)
DISPLAY_WIDTH=1920
DISPLAY_HEIGHT=1080
DISPLAY_FULLSCREEN=true
DISPLAY_BORDERLESS=true
```

#### Media Files
```bash
# Media file paths (optional)
HOLDING_IMAGE_PATH=media/holding.png
FAILURE_IMAGE_PATH=media/failure.png
```

### Health Monitoring Configuration

#### Health Monitoring (Optional)
```bash
# Health monitoring (default: disabled)
HEALTH_MONITORING_ENABLED=false
HEALTH_METRICS_PORT=8080
HEALTH_METRICS_HOST=0.0.0.0
```

#### Monitoring Intervals
```bash
# Monitoring intervals (optional)
HEALTH_HARDWARE_INTERVAL=10
HEALTH_NETWORK_INTERVAL=30
HEALTH_STREAM_INTERVAL=60
```

#### Network Monitoring
```bash
# Network monitoring (optional)
HEALTH_NETWORK_ENABLED=true
HEALTH_NETWORK_PING_HOSTS=8.8.8.8,1.1.1.1,vimeo.com
HEALTH_NETWORK_SPEEDTEST_ENABLED=true
HEALTH_NETWORK_SPEEDTEST_INTERVAL=300
```

#### Stream & Hardware Monitoring
```bash
# Stream and hardware monitoring (optional)
HEALTH_STREAM_ENABLED=true
HEALTH_STREAM_FFPROBE_TIMEOUT=15
HEALTH_HARDWARE_ENABLED=true
```

## 📁 Configuration Files

### .env File
Create a `.env` file in the project root with your configuration:

```bash
# Copy the sample file
cp .env.sample .env

# Edit with your settings
nano .env
```

### .env.sample
The project includes a `.env.sample` file with all available configuration options and their default values.

## 🔒 Security Best Practices

### Credential Management
- **Never commit `.env` files** to version control
- **Use strong, unique tokens** for Vimeo API credentials
- **Rotate credentials regularly** for production environments
- **Use environment-specific configurations** for different deployments

### File Permissions
```bash
# Set secure permissions on .env file
chmod 600 .env

# Ensure only owner can read/write
chown $USER:$USER .env
```

### Production Deployment
- Use system environment variables instead of `.env` files
- Implement proper access controls for configuration files

## ⚙️ Configuration Validation

The system automatically validates configuration on startup:

### Required Variables Check
- Vimeo API credentials must be present
- Stream ID must be specified
- All required paths must be accessible

### Value Validation
- Numeric values are validated for reasonable ranges
- File paths are checked for existence
- Network settings are validated for proper format

### Error Handling
- Configuration errors are logged with detailed messages
- System startup is prevented with invalid configuration
- Helpful error messages guide users to fix issues

## 🔄 Configuration Reloading

### Runtime Configuration
- Most configuration is loaded at startup
- Some settings can be changed via environment variables
- Restart required for most configuration changes

### Hot Reloading (Future)
- Planned feature for configuration hot-reloading
- Will allow changes without system restart
- Will include validation and rollback capabilities

## 📊 Configuration Examples

### Development Environment
```bash
# Development settings
LOG_LEVEL=DEBUG
HEALTH_MONITORING_ENABLED=true
HEALTH_METRICS_PORT=8080
STREAM_CHECK_INTERVAL=10
```

### Production Environment
```bash
# Production settings
LOG_LEVEL=INFO
HEALTH_MONITORING_ENABLED=true
HEALTH_METRICS_PORT=8080
STREAM_CHECK_INTERVAL=30
PROCESS_MAX_RESTARTS=5
```

### Raspberry Pi Environment
```bash
# Raspberry Pi optimized settings
LOG_LEVEL=WARNING
HEALTH_MONITORING_ENABLED=true
HEALTH_HARDWARE_INTERVAL=30
HEALTH_NETWORK_INTERVAL=60
HEALTH_STREAM_INTERVAL=120
```

## 🐛 Troubleshooting Configuration

### Common Issues

#### Missing Environment Variables
```
Error: VIMEO_ACCESS_TOKEN not found
Solution: Add VIMEO_ACCESS_TOKEN to your .env file
```

#### Invalid File Paths
```
Error: HOLDING_IMAGE_PATH not accessible
Solution: Check file exists and permissions are correct
```

#### Network Configuration Issues
```
Error: Invalid HEALTH_METRICS_HOST format
Solution: Use valid IP address or hostname
```

### Configuration Testing
```bash
# Test configuration without starting the system
uv run python -c "from src.vimeo_monitor.config import Config; print('Configuration valid')"

# Check specific configuration values
uv run python -c "from src.vimeo_monitor.config import Config; c = Config(); print(f'Stream ID: {c.vimeo_stream_id}')"
```

## 📚 Related Documentation

- **[Installation Guide](installation.md)** - Setting up the system
- **[Quick Start](quick-start.md)** - Step-by-step setup
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions
- **[Health Monitoring](health-monitoring.md)** - Monitoring configuration
- **[API Reference](api-reference.md)** - Configuration API details
