#!/bin/bash

# Vimeo Monitor Service Uninstall Script
# This script removes the Vimeo Monitor service and all installed components

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
      log_info "Detected Linux without systemd"
    fi
  elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="macos"
    log_info "Detected macOS"
  else
    OS_TYPE="unknown"
    log_warning "Unknown operating system: $OSTYPE"
  fi
}

# Stop and remove systemd service
remove_systemd_service() {
  log_step "Removing systemd service..."

  # Stop service if running
  if systemctl is-active --quiet "$SERVICE_NAME"; then
    systemctl stop "$SERVICE_NAME"
    log_success "Service stopped"
  fi

  # Disable service
  if systemctl is-enabled --quiet "$SERVICE_NAME"; then
    systemctl disable "$SERVICE_NAME"
    log_success "Service disabled"
  fi

  # Remove service file
  if [[ -f "/etc/systemd/system/$SERVICE_NAME.service" ]]; then
    rm "/etc/systemd/system/$SERVICE_NAME.service"
    log_success "Service file removed"
  fi

  # Reload systemd
  systemctl daemon-reload
  systemctl reset-failed

  log_success "Systemd service removed"
}

# Remove launchd service (macOS)
remove_launchd_service() {
  log_step "Removing launchd service..."

  local plist_file="/Library/LaunchDaemons/com.vimeomonitor.service.plist"

  # Stop service if running
  if launchctl list | grep -q "com.vimeomonitor.service"; then
    launchctl unload "$plist_file" 2>/dev/null || true
    log_success "Service stopped"
  fi

  # Remove plist file
  if [[ -f "$plist_file" ]]; then
    rm "$plist_file"
    log_success "Service file removed"
  fi

  log_success "launchd service removed"
}

# Remove service based on OS
remove_service() {
  if [[ "$OS_TYPE" == "systemd" ]]; then
    remove_systemd_service
  elif [[ "$OS_TYPE" == "macos" ]]; then
    remove_launchd_service
  else
    log_warning "No service removal needed for this platform"
  fi
}

# Remove installation directory
remove_install_dir() {
  log_step "Removing installation directory..."

  if [[ -d "$INSTALL_DIR" ]]; then
    # Ask for confirmation before removing logs
    echo
    log_warning "This will remove all application files including logs."
    read -p "Do you want to backup logs before removal? (y/N): " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
      if [[ -d "$INSTALL_DIR/logs" ]]; then
        backup_dir="/tmp/vimeo-monitor-logs-$(date +%Y%m%d-%H%M%S)"
        cp -r "$INSTALL_DIR/logs" "$backup_dir"
        log_success "Logs backed up to: $backup_dir"
      fi
    fi

    rm -rf "$INSTALL_DIR"
    log_success "Installation directory removed"
  else
    log_info "Installation directory does not exist"
  fi
}

# Remove service user and group
remove_service_user() {
  log_step "Removing service user and group..."

  if [[ "$OS_TYPE" == "systemd" ]] || [[ "$OS_TYPE" == "linux" ]]; then
    # Linux
    if getent passwd "$SERVICE_USER" >/dev/null 2>&1; then
      userdel "$SERVICE_USER"
      log_success "Removed user: $SERVICE_USER"
    else
      log_info "User $SERVICE_USER does not exist"
    fi

    if getent group "$SERVICE_GROUP" >/dev/null 2>&1; then
      groupdel "$SERVICE_GROUP"
      log_success "Removed group: $SERVICE_GROUP"
    else
      log_info "Group $SERVICE_GROUP does not exist"
    fi
  elif [[ "$OS_TYPE" == "macos" ]]; then
    # macOS
    if dscl . -read /Users/"$SERVICE_USER" >/dev/null 2>&1; then
      dscl . -delete /Users/"$SERVICE_USER"
      log_success "Removed user: $SERVICE_USER"
    else
      log_info "User $SERVICE_USER does not exist"
    fi

    if dscl . -read /Groups/"$SERVICE_GROUP" >/dev/null 2>&1; then
      dscl . -delete /Groups/"$SERVICE_GROUP"
      log_success "Removed group: $SERVICE_GROUP"
    else
      log_info "Group $SERVICE_GROUP does not exist"
    fi
  fi
}

# Remove logrotate configuration
remove_logrotate_config() {
  log_step "Removing logrotate configuration..."

  if [[ -f "/etc/logrotate.d/vimeo-monitor" ]]; then
    rm "/etc/logrotate.d/vimeo-monitor"
    log_success "Logrotate configuration removed"
  else
    log_info "Logrotate configuration does not exist"
  fi
}

# Show post-uninstall information
show_post_uninstall_info() {
  echo
  log_success "Uninstallation completed successfully!"
  echo
  log_info "The following components have been removed:"
  echo "  - Vimeo Monitor service"
  echo "  - Installation directory: $INSTALL_DIR"
  echo "  - Service user: $SERVICE_USER"
  echo "  - Service group: $SERVICE_GROUP"
  echo "  - Logrotate configuration"
  echo
  log_info "The system has been restored to its original state."
  echo
}

# Main uninstall function
main() {
  echo "🗑️  Vimeo Monitor Service Uninstall"
  echo "===================================="
  echo

  log_warning "This will completely remove the Vimeo Monitor service and all its components."
  read -p "Are you sure you want to continue? (y/N): " -n 1 -r
  echo

  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "Uninstall cancelled"
    exit 0
  fi

  echo
  check_root
  detect_os
  remove_service
  remove_install_dir
  remove_service_user
  remove_logrotate_config
  show_post_uninstall_info
}

# Run main function
main "$@"
