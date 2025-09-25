#!/bin/bash
# Script to safely add video resolution parameter to cmdline.txt
# Adds video=HDMI-A-1:1920x1080M@50 to the beginning of cmdline.txt
# Ensures file remains a single line

CMDLINE_FILE="/boot/firmware/cmdline.txt"
VIDEO_PARAM="video=HDMI-A-1:1920x1080M@50"
BACKUP_FILE="/boot/firmware/cmdline.txt.backup.$(date +%Y%m%d_%H%M%S)"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "⚠️  This script must be run with sudo privileges"
  echo "Please run: sudo $0"
  exit 1
fi

# Check if cmdline.txt exists
if [ ! -f "$CMDLINE_FILE" ]; then
  echo "❌ Error: $CMDLINE_FILE does not exist"
  echo "This script is designed for Raspberry Pi OS systems"
  exit 1
fi

# Check if file is readable
if [ ! -r "$CMDLINE_FILE" ]; then
  echo "❌ Error: Cannot read $CMDLINE_FILE"
  exit 1
fi

# Check if file is writable
if [ ! -w "$CMDLINE_FILE" ]; then
  echo "❌ Error: Cannot write to $CMDLINE_FILE"
  exit 1
fi

# Check if file is a single line
LINE_COUNT=$(wc -l < "$CMDLINE_FILE")
if [ "$LINE_COUNT" -ne 0 ] && [ "$LINE_COUNT" -ne 1 ]; then
  echo "❌ Error: $CMDLINE_FILE must be a single line file"
  echo "Current line count: $LINE_COUNT"
  exit 1
fi

# Check if video parameter already exists
if grep -q "$VIDEO_PARAM" "$CMDLINE_FILE"; then
  echo "✓ Video resolution parameter already exists in $CMDLINE_FILE"
  echo "Current parameter: $VIDEO_PARAM"
  exit 0
fi

# Check if any video parameter already exists
if grep -q "video=HDMI-A-1:" "$CMDLINE_FILE"; then
  echo "⚠️  Different video resolution parameter already exists"
  echo "Current parameter:"
  grep -o "video=HDMI-A-1:[^ ]*" "$CMDLINE_FILE"
  
  read -p "Replace with $VIDEO_PARAM? (y/n): " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Operation cancelled"
    exit 0
  fi
  
  # Create backup
  echo "Creating backup of $CMDLINE_FILE to $BACKUP_FILE"
  cp "$CMDLINE_FILE" "$BACKUP_FILE"
  
  # Replace existing video parameter
  sed -i "s/video=HDMI-A-1:[^ ]*/$VIDEO_PARAM/" "$CMDLINE_FILE"
  
  echo "✓ Replaced existing video parameter with $VIDEO_PARAM"
  echo "⚠️  IMPORTANT: A reboot is required for changes to take effect"
  echo "   Run: sudo reboot"
  exit 0
fi

# Create backup
echo "Creating backup of $CMDLINE_FILE to $BACKUP_FILE"
cp "$CMDLINE_FILE" "$BACKUP_FILE"

# Add video parameter to beginning of file
echo "Adding $VIDEO_PARAM to beginning of $CMDLINE_FILE"
sed -i "s/^/$VIDEO_PARAM /" "$CMDLINE_FILE"

# Verify file is still a single line
NEW_LINE_COUNT=$(wc -l < "$CMDLINE_FILE")
if [ "$NEW_LINE_COUNT" -ne 0 ] && [ "$NEW_LINE_COUNT" -ne 1 ]; then
  echo "❌ Error: File modification resulted in multiple lines"
  echo "Restoring backup from $BACKUP_FILE"
  cp "$BACKUP_FILE" "$CMDLINE_FILE"
  exit 1
fi

echo "✓ Successfully added $VIDEO_PARAM to $CMDLINE_FILE"
echo "⚠️  IMPORTANT: A reboot is required for changes to take effect"
echo "   Run: sudo reboot"
exit 0
