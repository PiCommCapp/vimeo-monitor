# Raspberry Pi 5 Deployment Guide

## Pre-Deployment Checklist

### Hardware Setup

- [ ] Raspberry Pi 5 (or Pi 4 with 4GB+ RAM)
- [ ] 32GB+ MicroSD card (Class 10 or better)
- [ ] HDMI display connected
- [ ] Network connection (Ethernet recommended for stability)
- [ ] Power supply appropriate for Pi model

### Software Prerequisites

- [ ] Raspberry Pi OS Desktop (Bookworm or later) - **NOT Lite version**
- [ ] System fully updated (`sudo apt update && sudo apt upgrade`)
- [ ] X11 desktop environment running
- [ ] SSH enabled (if managing remotely)

## Step-by-Step Deployment

### 1. System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install -y \
    python3-pip \
    python3-venv \
    python3-tk \
    python3-tkinter \
    ffmpeg \
    curl \
    make \
    build-essential \
    git \
    logrotate

# Install optional monitoring tools
sudo apt install -y htop iotop

# Verify critical components
python3 -c "import tkinter; print('✅ tkinter available')"
ffplay -version
echo $DISPLAY  # Should show :0
```

### 2. Application Installation

```bash
# Clone repository
cd /home/pi
git clone https://github.com/yourusername/vimeo-monitor.git
cd vimeo-monitor

# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# Install application dependencies
make install

# Verify installation
make status
```

### 3. Configuration

```bash
# Create configuration from template
cp .env.sample .env

# Edit configuration (replace with your values)
nano .env
```

**Required Configuration Items:**

```env
# Vimeo API credentials (obtain from Vimeo Developer portal)
VIMEO_TOKEN="your_actual_token"
VIMEO_KEY="your_actual_key"
VIMEO_SECRET="your_actual_secret"
VIMEO_STREAM_ID="your_stream_id"

# Image paths (create these directories and add images)
HOLDING_IMAGE_PATH=/home/pi/vimeo-monitor/images/holding.jpg
API_FAIL_IMAGE_PATH=/home/pi/vimeo-monitor/images/failure.jpg

# Network overlay (should work out of box on Pi)
DISPLAY_NETWORK_STATUS=true
OVERLAY_POSITION=top-right
```

### 4. Create Required Directories and Images

```bash
# Create images directory
mkdir -p /home/pi/vimeo-monitor/images

# Create or copy your holding and failure images
# holding.jpg - displayed when stream is inactive
# failure.jpg - displayed when API is failing

# Example: Create simple test images (replace with your designs)
convert -size 1920x1080 xc:black -fill white -gravity center \
    -annotate +0+0 "Stream Inactive\nPlease Wait" \
    /home/pi/vimeo-monitor/images/holding.jpg

convert -size 1920x1080 xc:red -fill white -gravity center \
    -annotate +0+0 "Connection Issues\nRetrying..." \
    /home/pi/vimeo-monitor/images/failure.jpg
```

### 5. Test Installation

```bash
# Test application manually
cd /home/pi/vimeo-monitor
uv run -m vimeo_monitor.monitor

# Expected output:
# Network status overlay initialized: enabled=True, mode=gui, position=top-right
# Starting Vimeo stream monitor...
# Mode change: None -> stream
# Stream active. URL: https://...
```

**Verify These Components:**

- [ ] GUI overlay appears on screen (top-right corner by default)
- [ ] Video stream starts playing if active
- [ ] Status updates appear in logs
- [ ] No error messages about missing dependencies

### 6. Production Service Setup

```bash
# Install log rotation
make install-logrotate

# Copy systemd service file
sudo cp services/vimeo-monitor.service /etc/systemd/system/

# Edit service file for your installation
sudo nano /etc/systemd/system/vimeo-monitor.service

# Update these paths in the service file:
# WorkingDirectory=/home/pi/vimeo-monitor
# ExecStart=/home/pi/vimeo-monitor/.venv/bin/python -m vimeo_monitor.monitor
# User=pi
# Group=pi

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable vimeo-monitor
sudo systemctl start vimeo-monitor

# Verify service is running
sudo systemctl status vimeo-monitor
```

### 7. Auto-Start on Boot Configuration

```bash
# Ensure X11 starts automatically (should be default on Desktop)
sudo systemctl enable lightdm  # or gdm3 depending on desktop environment

# Verify display manager
systemctl status display-manager

# Configure automatic login (optional, for kiosk mode)
sudo raspi-config
# Advanced Options -> Autologin -> Desktop Autologin
```

## Verification Tests

### Basic Functionality Test

```bash
# Check service status
sudo systemctl status vimeo-monitor

# Check logs for errors
sudo journalctl -fu vimeo-monitor --since "10 minutes ago"

# Test network connectivity
ping api.vimeo.com

# Verify GUI components
python3 -c "import tkinter; root=tkinter.Tk(); root.withdraw(); print('✅ GUI test passed')"
```

### Network Overlay Test

```bash
# Look for overlay initialization in logs
grep -i "overlay" /home/pi/vimeo-monitor/logs/vimeo_monitor.logs

# Check for GUI mode activation
grep -i "mode=gui" /home/pi/vimeo-monitor/logs/vimeo_monitor.logs

# Monitor real-time status updates
tail -f /home/pi/vimeo-monitor/logs/vimeo_monitor.logs
```

### Performance Test

```bash
# Monitor CPU usage (should be low)
htop

# Check memory usage
free -h

# Monitor disk space
df -h

# Check log rotation is working
ls -la /home/pi/vimeo-monitor/logs/
```

## Common Raspberry Pi Specific Issues

### GUI Not Working

```bash
# Check if running in console mode
who
# Should show pi on tty7 or similar (GUI session)

# Start desktop if needed
startx

# Check display variable
echo $DISPLAY
# Should be :0

# Test X11 directly
xeyes  # Should show eyes that follow cursor
```

### Performance Issues

```bash
# Check Pi temperature
vcgencmd measure_temp
# Should be under 80°C

# Check GPU memory split
vcgencmd get_mem gpu
# Should be 64MB or higher for video

# Adjust GPU memory if needed
sudo raspi-config
# Advanced Options -> Memory Split -> Set to 128
```

### Network Issues

```bash
# Check WiFi signal strength
iwconfig wlan0

# Test network stability
ping -c 20 api.vimeo.com

# Check for dropped packets
netstat -i
```

### Storage Issues

```bash
# Check available space
df -h /

# Clean up if needed
sudo apt autoremove
sudo apt autoclean

# Check log sizes
du -sh /home/pi/vimeo-monitor/logs/
```

## Monitoring and Maintenance

### Daily Checks

```bash
# Service status
sudo systemctl status vimeo-monitor

# Recent logs
sudo journalctl -u vimeo-monitor --since today

# Disk space
df -h
```

### Weekly Maintenance

```bash
# Update system
sudo apt update && sudo apt upgrade

# Restart service to clear any memory leaks
sudo systemctl restart vimeo-monitor

# Check log rotation
ls -la /home/pi/vimeo-monitor/logs/
```

### Log Analysis

```bash
# Analyze logs for patterns
make analyze-logs

# Check for API failures
grep "API failure" /home/pi/vimeo-monitor/logs/vimeo_monitor.logs

# Monitor overlay performance
grep "overlay" /home/pi/vimeo-monitor/logs/vimeo_monitor.logs
```

## Kiosk Mode Configuration (Optional)

For a true kiosk experience where only the video stream is visible:

```bash
# Install unclutter to hide mouse cursor
sudo apt install unclutter

# Edit desktop autostart
mkdir -p ~/.config/lxsession/LXDE-pi
nano ~/.config/lxsession/LXDE-pi/autostart

# Add these lines:
@xset s off
@xset -dpms
@xset s noblank
@unclutter -idle 0.1 -root

# Disable desktop wallpaper and taskbar
pcmanfm --set-wallpaper="" --wallpaper-mode=color --wallpaper-color=#000000

# Auto-hide taskbar
# Right-click taskbar -> Panel Settings -> Advanced -> Minimize when not in use
```

## Remote Management

### SSH Access

```bash
# Connect from development machine
ssh pi@<raspberry-pi-ip>

# Monitor application remotely
ssh pi@<raspberry-pi-ip> "sudo journalctl -fu vimeo-monitor"

# Update application remotely
ssh pi@<raspberry-pi-ip> "cd /home/pi/vimeo-monitor && git pull && sudo systemctl restart vimeo-monitor"
```

### VNC Access (for GUI debugging)

```bash
# Enable VNC on Pi
sudo raspi-config
# Interface Options -> VNC -> Enable

# Connect from development machine
# Use RealVNC or similar VNC client to connect to Pi's IP address
```

## Backup and Recovery

### Configuration Backup

```bash
# Backup configuration
cp .env .env.backup.$(date +%Y%m%d)

# Backup logs
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/
```

### System Image Backup

```bash
# From another Linux machine, backup entire SD card
sudo dd if=/dev/sdX of=vimeo-monitor-backup-$(date +%Y%m%d).img bs=4M status=progress

# Compress backup
gzip vimeo-monitor-backup-$(date +%Y%m%d).img
```

## Performance Optimization

### For Raspberry Pi 4

```bash
# Increase GPU memory split
sudo raspi-config
# Advanced Options -> Memory Split -> 128

# Enable GPU acceleration
sudo nano /boot/config.txt
# Add: gpu_mem=128
```

### For Raspberry Pi 5

```bash
# Pi 5 has better default settings
# Monitor performance with:
htop
vcgencmd measure_temp
vcgencmd get_throttled
```

This deployment guide ensures a smooth transition from development to production on Raspberry Pi hardware with all necessary prerequisites clearly documented.
