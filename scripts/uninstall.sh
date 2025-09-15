#!/bin/bash
# Vimeo Monitor Uninstallation Script
# This script removes the Vimeo Monitor system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/home/admin/code/vimeo-monitor"
SERVICE_USER="admin"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root"
        exit 1
    fi
}

stop_application() {
    log_info "Stopping Vimeo Monitor application..."
    
    # Kill any running instances
    pkill -f "streammonitor.py" || true
    pkill -f "vimeo-monitor" || true
    
    # Wait a moment for processes to stop
    sleep 2
    
    log_success "Application stopped"
}

remove_autostart() {
    log_info "Removing autostart configuration..."
    
    # Remove autostart files
    rm -f ~/.config/autostart/streamreturn.desktop
    rm -f ~/.config/autostart/xrandr.desktop
    
    # Remove autostart directory if empty
    if [[ -d ~/.config/autostart ]] && [[ -z "$(ls -A ~/.config/autostart)" ]]; then
        rmdir ~/.config/autostart
    fi
    
    log_success "Autostart configuration removed"
}

remove_project_files() {
    log_info "Removing project files..."
    
    if [[ -d "$PROJECT_DIR" ]]; then
        # Ask for confirmation
        echo -n "Remove project directory $PROJECT_DIR? (y/N): "
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            rm -rf "$PROJECT_DIR"
            log_success "Project directory removed"
        else
            log_info "Project directory kept"
        fi
    else
        log_info "Project directory not found"
    fi
}

remove_system_dependencies() {
    log_info "Removing system dependencies..."
    
    # Ask for confirmation
    echo -n "Remove system dependencies (VLC, FFmpeg, etc.)? (y/N): "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        sudo apt remove -y vlc ffmpeg
        log_success "System dependencies removed"
    else
        log_info "System dependencies kept"
    fi
}

remove_uv() {
    log_info "Removing UV package manager..."
    
    # Ask for confirmation
    echo -n "Remove UV package manager? (y/N): "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        # Remove uv installation
        rm -rf ~/.cargo/bin/uv
        rm -rf ~/.local/share/uv
        
        # Remove from PATH in .bashrc
        sed -i '/export PATH="\$HOME\/.cargo\/bin:\$PATH"/d' ~/.bashrc
        
        log_success "UV package manager removed"
    else
        log_info "UV package manager kept"
    fi
}

cleanup_logs() {
    log_info "Cleaning up log files..."
    
    # Remove log files from system directories
    sudo rm -f /var/log/vimeo-monitor.log
    sudo rm -f /var/log/stream_monitor.log
    
    log_success "Log files cleaned up"
}

show_completion() {
    log_info "Uninstallation completed!"
    echo
    echo "The following items have been removed:"
    echo "- Vimeo Monitor application"
    echo "- Autostart configuration"
    echo "- Project files (if confirmed)"
    echo "- System dependencies (if confirmed)"
    echo "- UV package manager (if confirmed)"
    echo "- Log files"
    echo
    log_success "Vimeo Monitor uninstallation completed successfully!"
}

# Main uninstallation process
main() {
    log_info "Starting Vimeo Monitor uninstallation..."
    echo
    
    check_root
    stop_application
    remove_autostart
    remove_project_files
    remove_system_dependencies
    remove_uv
    cleanup_logs
    show_completion
}

# Run main function
main "$@"
