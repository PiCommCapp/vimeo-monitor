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

