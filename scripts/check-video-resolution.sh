#!/bin/bash
# Script to check the current video resolution parameter in cmdline.txt

CMDLINE_FILE="/boot/firmware/cmdline.txt"

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

# Check if file is a single line
LINE_COUNT=$(wc -l < "$CMDLINE_FILE")
if [ "$LINE_COUNT" -ne 0 ] && [ "$LINE_COUNT" -ne 1 ]; then
  echo "⚠️  Warning: $CMDLINE_FILE should be a single line file"
  echo "Current line count: $LINE_COUNT"
fi

echo "Checking video resolution parameters in $CMDLINE_FILE..."

# Check if any video parameter exists
if grep -q "video=" "$CMDLINE_FILE"; then
  echo "✓ Video resolution parameters found:"
  grep -o "video=[^ ]*" "$CMDLINE_FILE"
  
  # Check specifically for HDMI-A-1 parameter
  if grep -q "video=HDMI-A-1:" "$CMDLINE_FILE"; then
    echo "✓ HDMI-A-1 configuration is present"
    CURRENT_PARAM=$(grep -o "video=HDMI-A-1:[^ ]*" "$CMDLINE_FILE")
    echo "Current parameter: $CURRENT_PARAM"
    
    # Check if it's the recommended parameter
    if grep -q "video=HDMI-A-1:1920x1080M@50" "$CMDLINE_FILE"; then
      echo "✓ Recommended parameter is configured (1920x1080M@50)"
    else
      echo "⚠️  Different resolution is configured"
      echo "Recommended: video=HDMI-A-1:1920x1080M@50"
      echo "To update, run: sudo make fix-video-resolution"
    fi
  else
    echo "⚠️  Other video parameters found, but no HDMI-A-1 configuration"
    echo "To configure HDMI-A-1, run: sudo make fix-video-resolution"
  fi
else
  echo "❌ No video resolution parameters found"
  echo "To configure video resolution, run: sudo make fix-video-resolution"
fi

# Display current screen resolution if xrandr is available
if command -v xrandr &> /dev/null && [ -n "$DISPLAY" ]; then
  echo -e "\nCurrent screen resolution:"
  xrandr | grep -w connected -A1 | grep -v connected
else
  echo -e "\nNote: xrandr not available or not in X session"
  echo "Cannot display current screen resolution"
fi

exit 0
