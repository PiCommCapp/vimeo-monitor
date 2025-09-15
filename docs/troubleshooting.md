# Vimeo Monitor - Troubleshooting Guide

## Common Issues and Solutions

### 1. Configuration Issues

#### Problem: "Required environment variable not set"
**Symptoms:**
- Application fails to start
- Error message about missing environment variables

**Solutions:**
1. Check that `.env` file exists in project root
2. Verify all required variables are set:
   ```bash
   VIMEO_TOKEN=your_token_here
   VIMEO_KEY=your_key_here
   VIMEO_SECRET=your_secret_here
   STATIC_IMAGE_PATH=media/holding.png
   ERROR_IMAGE_PATH=media/failure.png
   ```
3. Copy from `.env.sample` if needed:
   ```bash
   cp .env.sample .env
   # Edit .env with your actual credentials
   ```

#### Problem: "File not found" errors
**Symptoms:**
- Error messages about missing image files
- Application fails to start

**Solutions:**
1. Verify image files exist:
   ```bash
   ls -la media/holding.png
   ls -la media/failure.png
   ```
2. Check file permissions:
   ```bash
   chmod 644 media/*.png
   ```
3. Ensure paths in `.env` are correct (relative to project root)

### 2. Vimeo API Issues

#### Problem: "Failed to initialize Vimeo client"
**Symptoms:**
- Application fails to start
- API authentication errors

**Solutions:**
1. Verify Vimeo credentials are correct
2. Check API token permissions
3. Ensure network connectivity to Vimeo API
4. Test API access manually:
   ```bash
   curl -H "Authorization: bearer YOUR_TOKEN" https://api.vimeo.com/me
   ```

#### Problem: "Stream not found" or "No m3u8_playback_url"
**Symptoms:**
- Stream shows as offline when it should be live
- No video playback

**Solutions:**
1. Verify stream ID is correct in configuration
2. Check if stream is actually live on Vimeo
3. Verify stream selection number (1-6) matches your stream
4. Check Vimeo dashboard for stream status

### 3. Process Management Issues

#### Problem: VLC/FFmpeg process fails to start
**Symptoms:**
- No video display
- Process manager errors in logs

**Solutions:**
1. Verify VLC is installed:
   ```bash
   which vlc
   which cvlc
   ```
2. Install VLC if missing:
   ```bash
   sudo apt update
   sudo apt install vlc
   ```
3. Check FFmpeg installation:
   ```bash
   which ffplay
   ```
4. Install FFmpeg if missing:
   ```bash
   sudo apt install ffmpeg
   ```

#### Problem: Process keeps restarting
**Symptoms:**
- Frequent restart messages in logs
- Unstable video display

**Solutions:**
1. Check system resources (CPU, memory)
2. Verify network stability
3. Check for conflicting processes
4. Review restart limits in process manager
5. Check logs for specific error messages

### 4. Display Issues

#### Problem: No video display
**Symptoms:**
- Application runs but no video shows
- Process appears to be running

**Solutions:**
1. Check display configuration:
   ```bash
   xrandr
   ```
2. Verify display is active and configured
3. Check if another application is using the display
4. Test with static image first:
   ```bash
   ffplay -fs -loop 1 media/holding.png
   ```

#### Problem: Video displays but is choppy/poor quality
**Symptoms:**
- Video plays but with poor performance
- High CPU usage

**Solutions:**
1. Check system resources
2. Reduce video quality if possible
3. Check network bandwidth
4. Verify hardware acceleration is available
5. Consider reducing check interval

### 5. Logging Issues

#### Problem: No log files created
**Symptoms:**
- Application runs but no logs appear
- Cannot debug issues

**Solutions:**
1. Check logs directory exists:
   ```bash
   ls -la logs/
   ```
2. Create logs directory if missing:
   ```bash
   mkdir -p logs
   chmod 755 logs
   ```
3. Check file permissions
4. Verify log configuration in `.env`

#### Problem: Log files too large
**Symptoms:**
- Disk space issues
- Application performance problems

**Solutions:**
1. Check log rotation configuration
2. Manually clean old logs:
   ```bash
   find logs/ -name "*.log*" -mtime +7 -delete
   ```
3. Adjust log rotation settings in `.env`

### 6. Autostart Issues

#### Problem: Application doesn't start automatically
**Symptoms:**
- Manual start works but autostart fails
- No desktop files in autostart directory

**Solutions:**
1. Check autostart directory:
   ```bash
   ls -la ~/.config/autostart/
   ```
2. Install autostart files:
   ```bash
   make autostart-install
   ```
3. Verify desktop file permissions
4. Check system logs for autostart errors

#### Problem: Autostart fails with permission errors
**Symptoms:**
- Desktop file exists but application doesn't start
- Permission denied errors

**Solutions:**
1. Check desktop file permissions:
   ```bash
   chmod 644 ~/.config/autostart/streamreturn.desktop
   ```
2. Verify file ownership
3. Check if application path is correct in desktop file

### 7. Network Issues

#### Problem: Cannot connect to Vimeo API
**Symptoms:**
- Connection timeout errors
- API request failures

**Solutions:**
1. Check internet connectivity:
   ```bash
   ping api.vimeo.com
   ```
2. Check firewall settings
3. Verify proxy configuration if applicable
4. Test with different network if possible

#### Problem: Stream URL is invalid or expired
**Symptoms:**
- Stream found but video won't play
- VLC errors about invalid URL

**Solutions:**
1. Check if stream URL is still valid
2. Verify stream is actually live
3. Check Vimeo stream settings
4. Test URL manually with VLC

### 8. Performance Issues

#### Problem: High CPU usage
**Symptoms:**
- System becomes slow
- High CPU usage in process list

**Solutions:**
1. Check for multiple instances running
2. Increase check interval in configuration
3. Monitor system resources
4. Consider hardware limitations

#### Problem: Memory usage growing over time
**Symptoms:**
- Memory usage increases continuously
- System becomes unresponsive

**Solutions:**
1. Check for memory leaks in logs
2. Restart application periodically
3. Monitor log file sizes
4. Check for process accumulation

## Debugging Commands

### Check Application Status
```bash
# Check if application is running
ps aux | grep streammonitor

# Check process status
make test

# View recent logs
tail -f logs/stream_monitor.log
```

### Test Configuration
```bash
# Test configuration loading
uv run python3 -c "from vimeo_monitor import config; config.validate(); print('Configuration valid')"

# Test Vimeo API connection
uv run python3 -c "from vimeo_monitor import config; from vimeo import VimeoClient; client = VimeoClient(**config.get_vimeo_client_config()); print('API connection successful')"
```

### Test Media Playback
```bash
# Test static image display
ffplay -fs -loop 1 media/holding.png

# Test error image display
ffplay -fs -loop 1 media/failure.png

# Test VLC installation
cvlc --version
```

### System Information
```bash
# Check system resources
htop
free -h
df -h

# Check display configuration
xrandr

# Check network connectivity
ping api.vimeo.com
```

## Getting Help

### Log Files
- **Main log**: `logs/stream_monitor.log`
- **System logs**: `/var/log/syslog`
- **Autostart logs**: Check system logs for desktop file execution

### Configuration Files
- **Environment**: `.env`
- **Sample config**: `.env.sample`
- **Autostart**: `~/.config/autostart/streamreturn.desktop`

### Useful Commands
```bash
# Full system test
make test

# Clean and restart
make clean
make setup
make run

# Check autostart status
make autostart-install
make autostart-remove
```

## Prevention

### Regular Maintenance
1. Monitor log file sizes
2. Check system resources regularly
3. Verify network connectivity
4. Test application functionality periodically
5. Keep system and dependencies updated

### Best Practices
1. Use proper file permissions
2. Keep credentials secure
3. Monitor system resources
4. Regular testing and validation
5. Document any custom configurations

---

**Last Updated**: September 15, 2024  
**Version**: Phase 4 - Production Hardening
