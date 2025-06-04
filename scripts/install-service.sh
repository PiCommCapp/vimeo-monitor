#!/bin/bash

# Vimeo Monitor Service Installation Script
# This script installs the Vimeo Monitor as a system service

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
SERVICE_USER="vimeo-monitor"
SERVICE_GROUP="vimeo-monitor"
INSTALL_DIR="/opt/vimeo-monitor"
SERVICE_NAME="vimeo-monitor"
CURRENT_DIR="$(pwd)"

# Logging functions
log_info() {
  echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
  echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
  echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
  echo -e "${RED}❌ $1${NC}"
}

log_step() {
  echo -e "${BLUE}🔧 $1${NC}"
}

# Check if running as root
check_root() {
  if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root (use sudo)"
    exit 1
  fi
}

# Detect operating system
detect_os() {
  if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if command -v systemctl >/dev/null 2>&1; then
      OS_TYPE="systemd"
      log_info "Detected Linux with systemd"
    else
      OS_TYPE="linux"
      log_warning "Detected Linux without systemd - service installation may not work"
    fi
  elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="macos"
    log_info "Detected macOS - will use launchd"
  else
    OS_TYPE="unknown"
    log_error "Unsupported operating system: $OSTYPE"
    exit 1
  fi
}

# Create service user and group
create_service_user() {
  log_step "Creating service user and group..."

  if [[ "$OS_TYPE" == "systemd" ]] || [[ "$OS_TYPE" == "linux" ]]; then
    # Linux
    if ! getent group "$SERVICE_GROUP" >/dev/null 2>&1; then
      groupadd --system "$SERVICE_GROUP"
      log_success "Created group: $SERVICE_GROUP"
    else
      log_info "Group $SERVICE_GROUP already exists"
    fi

    if ! getent passwd "$SERVICE_USER" >/dev/null 2>&1; then
      useradd --system --gid "$SERVICE_GROUP" --home-dir "$INSTALL_DIR" \
        --shell /bin/false --comment "Vimeo Monitor Service" "$SERVICE_USER"
      log_success "Created user: $SERVICE_USER"
    else
      log_info "User $SERVICE_USER already exists"
    fi
  elif [[ "$OS_TYPE" == "macos" ]]; then
    # macOS
    if ! dscl . -read /Groups/"$SERVICE_GROUP" >/dev/null 2>&1; then
      # Find next available GID
      local gid=$(dscl . -list /Groups PrimaryGroupID | awk '{print $2}' | sort -n | tail -1)
      gid=$((gid + 1))

      dscl . -create /Groups/"$SERVICE_GROUP"
      dscl . -create /Groups/"$SERVICE_GROUP" PrimaryGroupID "$gid"
      log_success "Created group: $SERVICE_GROUP"
    else
      log_info "Group $SERVICE_GROUP already exists"
    fi

    if ! dscl . -read /Users/"$SERVICE_USER" >/dev/null 2>&1; then
      # Find next available UID
      local uid=$(dscl . -list /Users UniqueID | awk '{print $2}' | sort -n | tail -1)
      uid=$((uid + 1))
      local gid=$(dscl . -read /Groups/"$SERVICE_GROUP" PrimaryGroupID | awk '{print $2}')

      dscl . -create /Users/"$SERVICE_USER"
      dscl . -create /Users/"$SERVICE_USER" UniqueID "$uid"
      dscl . -create /Users/"$SERVICE_USER" PrimaryGroupID "$gid"
      dscl . -create /Users/"$SERVICE_USER" UserShell /bin/false
      dscl . -create /Users/"$SERVICE_USER" RealName "Vimeo Monitor Service"
      dscl . -create /Users/"$SERVICE_USER" NFSHomeDirectory "$INSTALL_DIR"
      log_success "Created user: $SERVICE_USER"
    else
      log_info "User $SERVICE_USER already exists"
    fi
  fi
}

# Create installation directory
create_install_dir() {
  log_step "Creating installation directory..."

  if [[ ! -d "$INSTALL_DIR" ]]; then
    mkdir -p "$INSTALL_DIR"
    log_success "Created directory: $INSTALL_DIR"
  else
    log_info "Directory $INSTALL_DIR already exists"
  fi

  # Create subdirectories
  mkdir -p "$INSTALL_DIR"/{logs,config_backups,bin}

  # Set ownership
  chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR"
  chmod 755 "$INSTALL_DIR"
  chmod 755 "$INSTALL_DIR"/logs
  chmod 755 "$INSTALL_DIR"/config_backups
  chmod 755 "$INSTALL_DIR"/bin

  log_success "Set up directory structure and permissions"
}

# Copy application files
copy_application_files() {
  log_step "Copying application files..."

  # Copy main application
  cp -r vimeo_monitor "$INSTALL_DIR/"

  # Copy configuration files
  cp -r config "$INSTALL_DIR/" 2>/dev/null || mkdir -p "$INSTALL_DIR/config"

  # Copy documentation
  cp -r docs "$INSTALL_DIR/" 2>/dev/null || true

  # Copy scripts
  cp -r scripts "$INSTALL_DIR/" 2>/dev/null || true

  # Copy essential files
  cp pyproject.toml "$INSTALL_DIR/"
  cp uv.lock "$INSTALL_DIR/" 2>/dev/null || true
  cp README.md "$INSTALL_DIR/" 2>/dev/null || true
  cp .env.example "$INSTALL_DIR/"

  # Copy .env if it exists, otherwise create from example
  if [[ -f .env ]]; then
    cp .env "$INSTALL_DIR/"
    log_success "Copied existing .env file"
  else
    cp .env.example "$INSTALL_DIR/.env"
    log_warning "Created .env from example - please configure before starting service"
  fi

  # Set ownership
  chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR"

  log_success "Application files copied to $INSTALL_DIR"
}

# Install Python environment
install_python_environment() {
  log_step "Installing Python environment..."

  # Check if uv is installed
  if ! command -v uv >/dev/null 2>&1; then
    log_step "Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    log_success "uv installed"
  fi

  # Create virtual environment and install dependencies
  cd "$INSTALL_DIR"
  sudo -u "$SERVICE_USER" uv sync

  # Ensure the virtual environment is accessible
  chown -R "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR/.venv"

  cd "$CURRENT_DIR"
  log_success "Python environment set up"
}

# Install TUI components
install_tui() {
  log_step "Installing Terminal User Interface (TUI)..."

  # Copy TUI script to installation directory
  if [[ -f "scripts/vimeo-tui" ]]; then
    cp scripts/vimeo-tui "$INSTALL_DIR/bin/"
    chmod +x "$INSTALL_DIR/bin/vimeo-tui"
    chown "$SERVICE_USER:$SERVICE_GROUP" "$INSTALL_DIR/bin/vimeo-tui"
    log_success "TUI script installed to $INSTALL_DIR/bin/"
  else
    log_warning "TUI script not found at scripts/vimeo-tui"
  fi

  # Create symlink in system PATH
  local symlink_paths=("/usr/local/bin" "/usr/bin")
  local symlink_created=false

  for path in "${symlink_paths[@]}"; do
    if [[ -d "$path" && -w "$path" ]]; then
      ln -sf "$INSTALL_DIR/bin/vimeo-tui" "$path/vimeo-tui"
      log_success "Created symlink: $path/vimeo-tui -> $INSTALL_DIR/bin/vimeo-tui"
      symlink_created=true
      break
    fi
  done

  if [[ "$symlink_created" == "false" ]]; then
    log_warning "Could not create symlink in system PATH"
    log_info "You can manually add $INSTALL_DIR/bin to your PATH or create a symlink"
  fi

  # Test TUI installation
  if "$INSTALL_DIR/bin/vimeo-tui" --version >/dev/null 2>&1; then
    log_success "TUI installation verified"
  else
    log_warning "TUI installation test failed"
  fi

  log_success "Terminal User Interface (TUI) installed"
}

# Configure Prometheus metrics
configure_metrics() {
  log_step "Configuring Prometheus metrics..."

  # Ensure metrics configuration is present in .env
  local env_file="$INSTALL_DIR/.env"

  # Check if metrics settings are already configured
  if ! grep -q "ENABLE_PROMETHEUS_METRICS" "$env_file"; then
    log_info "Adding Prometheus metrics configuration to .env..."
    cat >>"$env_file" <<'EOF'

# Prometheus Metrics Configuration (added by installer)
ENABLE_PROMETHEUS_METRICS=true
PROMETHEUS_METRICS_PORT=8000
EOF
    log_success "Prometheus metrics configuration added"
  else
    log_info "Prometheus metrics configuration already present"
  fi

  # Ensure metrics are enabled
  sed -i.bak 's/ENABLE_PROMETHEUS_METRICS=false/ENABLE_PROMETHEUS_METRICS=true/' "$env_file" 2>/dev/null || true

  # Set ownership
  chown "$SERVICE_USER:$SERVICE_GROUP" "$env_file"

  log_success "Prometheus metrics configured"
}

# Verify installation and metrics setup
verify_installation() {
  log_step "Verifying installation..."

  # Test Python environment
  cd "$INSTALL_DIR"
  if sudo -u "$SERVICE_USER" .venv/bin/python -c "import vimeo_monitor.metrics; print('Metrics module loaded successfully')" >/dev/null 2>&1; then
    log_success "Python environment and metrics module verified"
  else
    log_error "Failed to load metrics module"
    return 1
  fi

  # Test metrics initialization (without starting server)
  if sudo -u "$SERVICE_USER" .venv/bin/python -c "
from vimeo_monitor.metrics import PrometheusMetrics
metrics = PrometheusMetrics(enable_metrics=False)  # Test initialization only
print('Metrics initialization successful')
" >/dev/null 2>&1; then
    log_success "Metrics initialization verified"
  else
    log_warning "Metrics initialization test failed - check configuration"
  fi

  cd "$CURRENT_DIR"
  log_success "Installation verification completed"
}

# Test service startup (optional)
test_service_startup() {
  log_step "Testing service startup..."

  if [[ "$OS_TYPE" == "systemd" ]]; then
    # Start service temporarily to test
    systemctl start "$SERVICE_NAME"
    sleep 5

    # Check if service is running
    if systemctl is-active --quiet "$SERVICE_NAME"; then
      log_success "Service started successfully"

      # Check if metrics endpoint is accessible (give it time to start)
      sleep 10
      if curl -s http://localhost:8000/metrics >/dev/null 2>&1; then
        log_success "Prometheus metrics endpoint accessible at http://localhost:8000/metrics"
      else
        log_warning "Metrics endpoint not yet accessible - may need more time to start"
      fi

      # Stop service for now (it will auto-start on boot)
      systemctl stop "$SERVICE_NAME"
      log_info "Service stopped - will auto-start on boot"
    else
      log_warning "Service failed to start - check logs with: sudo journalctl -u $SERVICE_NAME"
    fi
  elif [[ "$OS_TYPE" == "macos" ]]; then
    log_info "Service will start automatically on macOS - test with: sudo launchctl list | grep vimeomonitor"
  else
    log_info "Manual testing required on this platform"
  fi
}

# Install systemd service
install_systemd_service() {
  log_step "Installing systemd service..."

  # Copy service file
  cp services/vimeo-monitor.service /etc/systemd/system/

  # Reload systemd
  systemctl daemon-reload

  # Enable service
  systemctl enable "$SERVICE_NAME"

  log_success "Systemd service installed and enabled"
}

# Install launchd service (macOS)
install_launchd_service() {
  log_step "Installing launchd service..."

  # Create launchd plist file
  cat >/Library/LaunchDaemons/com.vimeomonitor.service.plist <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.vimeomonitor.service</string>
    <key>ProgramArguments</key>
    <array>
        <string>$INSTALL_DIR/.venv/bin/python</string>
        <string>-m</string>
        <string>vimeo_monitor.monitor</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$INSTALL_DIR</string>
    <key>UserName</key>
    <string>$SERVICE_USER</string>
    <key>GroupName</key>
    <string>$SERVICE_GROUP</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$INSTALL_DIR/logs/service.log</string>
    <key>StandardErrorPath</key>
    <string>$INSTALL_DIR/logs/service.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>$INSTALL_DIR/.venv/bin:/usr/local/bin:/usr/bin:/bin</string>
        <key>PYTHONPATH</key>
        <string>$INSTALL_DIR</string>
    </dict>
</dict>
</plist>
EOF

  # Set permissions
  chmod 644 /Library/LaunchDaemons/com.vimeomonitor.service.plist

  # Load the service
  launchctl load /Library/LaunchDaemons/com.vimeomonitor.service.plist

  log_success "launchd service installed and loaded"
}

# Install service based on OS
install_service() {
  if [[ "$OS_TYPE" == "systemd" ]]; then
    install_systemd_service
  elif [[ "$OS_TYPE" == "macos" ]]; then
    install_launchd_service
  else
    log_warning "Service installation not supported on this platform"
    log_info "You can run the application manually from $INSTALL_DIR"
  fi
}

# Show post-installation information
show_post_install_info() {
  echo
  log_success "Installation completed successfully!"
  echo
  log_info "Service Details:"
  echo "  - Service name: $SERVICE_NAME"
  echo "  - User: $SERVICE_USER"
  echo "  - Installation directory: $INSTALL_DIR"
  echo "  - Log directory: $INSTALL_DIR/logs"
  echo "  - Metrics endpoint: http://localhost:8000/metrics"
  echo

  if [[ "$OS_TYPE" == "systemd" ]]; then
    log_info "Service Management Commands:"
    echo "  - Start service:    sudo systemctl start $SERVICE_NAME"
    echo "  - Stop service:     sudo systemctl stop $SERVICE_NAME"
    echo "  - Restart service:  sudo systemctl restart $SERVICE_NAME"
    echo "  - Check status:     sudo systemctl status $SERVICE_NAME"
    echo "  - View logs:        sudo journalctl -u $SERVICE_NAME -f"
    echo "  - Disable service:  sudo systemctl disable $SERVICE_NAME"
  elif [[ "$OS_TYPE" == "macos" ]]; then
    log_info "Service Management Commands:"
    echo "  - Start service:    sudo launchctl load /Library/LaunchDaemons/com.vimeomonitor.service.plist"
    echo "  - Stop service:     sudo launchctl unload /Library/LaunchDaemons/com.vimeomonitor.service.plist"
    echo "  - Check status:     sudo launchctl list | grep vimeomonitor"
    echo "  - View logs:        tail -f $INSTALL_DIR/logs/service.log"
  fi

  echo
  log_info "Prometheus Metrics:"
  echo "  - Metrics enabled: Yes (configured automatically)"
  echo "  - Metrics endpoint: http://localhost:8000/metrics"
  echo "  - Test metrics: curl http://localhost:8000/metrics"
  echo "  - Grafana integration: Use endpoint for data source"
  echo

  echo
  log_info "Terminal User Interface (TUI):"
  echo "  - TUI command: vimeo-tui (available system-wide)"
  echo "  - Alternative: $INSTALL_DIR/bin/vimeo-tui"
  echo "  - Help: vimeo-tui --help"
  echo "  - Version: vimeo-tui --version"
  echo "  - Features: Real-time monitoring, configuration management, log viewing"
  echo

  echo
  log_warning "Important Notes:"
  echo "  - Configure $INSTALL_DIR/.env with your Vimeo API credentials"
  echo "  - Adjust configuration files in $INSTALL_DIR/config/ as needed"
  echo "  - The service will start automatically on boot"
  echo "  - Logs are written to $INSTALL_DIR/logs/"
  echo "  - Prometheus metrics are enabled and will be available after service starts"
  echo "  - Access TUI from anywhere with 'vimeo-tui' command"
  echo

  log_info "Next Steps:"
  echo "  1. Edit $INSTALL_DIR/.env with your Vimeo API credentials"
  echo "  2. Start the service: sudo systemctl start $SERVICE_NAME"
  echo "  3. Check metrics: curl http://localhost:8000/metrics"
  echo "  4. Monitor logs: sudo journalctl -u $SERVICE_NAME -f"
  echo "  5. Use TUI: vimeo-tui"
  echo "  6. Setup Grafana dashboard using metrics endpoint"
  echo
}

# Main installation function
main() {
  echo "🚀 Vimeo Monitor Service Installation"
  echo "====================================="
  echo

  check_root
  detect_os
  create_service_user
  create_install_dir
  copy_application_files
  install_python_environment
  install_tui
  configure_metrics
  verify_installation
  install_service
  test_service_startup
  show_post_install_info
}

# Run main function
main "$@"
