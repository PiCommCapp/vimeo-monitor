#!/bin/bash
# Vimeo Monitor Installation Script
# This script installs and configures the Vimeo Monitor system

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
LOG_DIR="$PROJECT_DIR/logs"
MEDIA_DIR="$PROJECT_DIR/media"

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

check_system() {
    log_info "Checking system requirements..."
    
    # Check if running on supported OS
    if [[ ! -f /etc/os-release ]]; then
        log_error "Cannot determine operating system"
        exit 1
    fi
    
    source /etc/os-release
    if [[ "$ID" != "debian" && "$ID" != "ubuntu" && "$ID" != "raspbian" ]]; then
        log_warning "This script is designed for Debian/Ubuntu/Raspbian systems"
        log_warning "Proceeding anyway, but some features may not work"
    fi
    
    log_success "System check completed"
}

install_dependencies() {
    log_info "Installing system dependencies..."
    
    # Update package list
    sudo apt update
    
    # Install required packages
    sudo apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        vlc \
        ffmpeg \
        curl \
        git \
        make \
        python3-dev \
        build-essential
    
    # Verify FFmpeg installation for health monitoring
    if command -v ffprobe &> /dev/null; then
        log_success "FFmpeg/FFprobe installed successfully (required for health monitoring)"
    else
        log_error "FFmpeg/FFprobe installation failed (required for health monitoring)"
        exit 1
    fi
    
    # Verify VLC installation
    if command -v vlc &> /dev/null; then
        log_success "VLC installed successfully"
    else
        log_error "VLC installation failed"
        exit 1
    fi
    
    log_success "System dependencies installed"
}

install_uv() {
    log_info "Installing UV package manager..."
    
    # Check if uv is already installed
    if command -v uv &> /dev/null; then
        log_success "UV is already installed"
        return
    fi
    
    # Install uv
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Add to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"
    
    # Add to PATH permanently
    if ! grep -q "~/.cargo/bin" ~/.bashrc; then
        echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
    fi
    
    log_success "UV package manager installed"
}

setup_project() {
    log_info "Setting up project directory..."
    
    # Create project directory if it doesn't exist
    if [[ ! -d "$PROJECT_DIR" ]]; then
        log_error "Project directory $PROJECT_DIR does not exist"
        log_error "Please clone the repository first:"
        log_error "git clone <repository-url> $PROJECT_DIR"
        exit 1
    fi
    
    cd "$PROJECT_DIR"
    
    # Create required directories
    mkdir -p "$LOG_DIR"
    mkdir -p "$MEDIA_DIR"
    
    # Set proper permissions
    chmod 755 "$LOG_DIR"
    chmod 755 "$MEDIA_DIR"
    
    log_success "Project directory setup completed"
}

install_python_dependencies() {
    log_info "Installing Python dependencies..."
    
    cd "$PROJECT_DIR"
    
    # Install dependencies using uv
    export PATH="$HOME/.cargo/bin:$PATH"
    uv sync
    
    # Ask if health monitoring should be installed
    read -p "Do you want to install health monitoring dependencies? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Installing health monitoring dependencies..."
        uv sync --extra health
        
        # Verify health monitoring dependencies
        if uv run python3 -c "import fastapi, uvicorn, psutil, prometheus_client, speedtest, requests" 2>/dev/null; then
            log_success "Health monitoring dependencies installed and verified"
        else
            log_warning "Health monitoring dependencies installed but verification failed"
        fi
    else
        log_info "Skipping health monitoring dependencies"
    fi
    
    log_success "Python dependencies installed"
}

setup_environment() {
    log_info "Setting up environment configuration..."
    
    cd "$PROJECT_DIR"
    
    # Create .env file if it doesn't exist
    if [[ ! -f ".env" ]]; then
        if [[ -f ".env.sample" ]]; then
            cp .env.sample .env
            log_warning "Created .env file from .env.sample"
            log_warning "Please edit .env with your actual Vimeo credentials"
        else
            log_error ".env.sample file not found"
            exit 1
        fi
    else
        log_info ".env file already exists"
    fi
    
    # Ask if health monitoring should be enabled
    read -p "Do you want to enable health monitoring? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if grep -q "HEALTH_MONITORING_ENABLED=true" .env; then
            log_info "Health monitoring is already enabled in .env"
        else
            # Update health monitoring configuration in .env
            sed -i 's/HEALTH_MONITORING_ENABLED=false/HEALTH_MONITORING_ENABLED=true/' .env
            log_success "Health monitoring enabled in .env"
        fi
    fi
    
    # Set proper permissions for .env
    chmod 600 .env
    
    log_success "Environment configuration setup completed"
}

setup_autostart() {
    log_info "Setting up autostart configuration..."
    
    cd "$PROJECT_DIR"
    
    # Create autostart directory
    mkdir -p ~/.config/autostart
    
    # Install autostart files
    make autostart-install
    
    log_success "Autostart configuration setup completed"
}

test_installation() {
    log_info "Testing installation..."
    
    cd "$PROJECT_DIR"
    
    # Test configuration
    export PATH="$HOME/.cargo/bin:$PATH"
    if uv run python3 -c "from vimeo_monitor import config; config.validate(); print('Configuration valid')"; then
        log_success "Configuration test passed"
    else
        log_warning "Configuration test failed - please check your .env file"
    fi
    
    # Test health monitoring imports if enabled
    if grep -q "HEALTH_MONITORING_ENABLED=true" .env; then
        log_info "Testing health monitoring imports..."
        if uv run python3 -c "try: from vimeo_monitor.health_module import HealthModule; print('Health monitoring imports valid'); except ImportError as e: print(f'Health monitoring imports failed: {e}'); exit(1)"; then
            log_success "Health monitoring imports test passed"
        else
            log_warning "Health monitoring imports test failed - please check your installation"
        fi
    fi
    
    # Test basic functionality
    if make test; then
        log_success "Basic functionality test passed"
    else
        log_warning "Basic functionality test failed - check logs for details"
    fi
    
    # Test health monitoring functionality if enabled
    if grep -q "HEALTH_MONITORING_ENABLED=true" .env; then
        log_info "Testing health monitoring functionality..."
        if uv run python3 -c "try: from vimeo_monitor.health_module import HealthModule; from vimeo_monitor import config, get_logger; hm = HealthModule(config, get_logger(config)); print('Health monitoring functionality test passed'); except Exception as e: print(f'Health monitoring functionality test failed: {e}'); exit(1)"; then
            log_success "Health monitoring functionality test passed"
        else
            log_warning "Health monitoring functionality test failed - please check your installation"
        fi
    fi
    
    log_success "Installation testing completed"
}

show_next_steps() {
    log_info "Installation completed! Next steps:"
    echo
    echo "1. Edit your configuration:"
    echo "   nano $PROJECT_DIR/.env"
    echo
    echo "2. Test the application:"
    echo "   cd $PROJECT_DIR"
    echo "   make test"
    echo
    echo "3. Run the application:"
    echo "   make run"
    echo
    # Show health monitoring info if enabled
    if grep -q "HEALTH_MONITORING_ENABLED=true" .env; then
        HEALTH_PORT=$(grep "HEALTH_METRICS_PORT" .env | cut -d= -f2)
        HEALTH_HOST=$(grep "HEALTH_METRICS_HOST" .env | cut -d= -f2)
        if [[ -z "$HEALTH_PORT" ]]; then HEALTH_PORT=8080; fi
        if [[ -z "$HEALTH_HOST" ]]; then HEALTH_HOST="0.0.0.0"; fi
        echo "4. Access health metrics:"
        echo "   http://<your-ip>:$HEALTH_PORT/metrics"
        echo
        echo "5. Configure Prometheus to scrape metrics:"
        echo "   - Add this to prometheus.yml:"
        echo "     scrape_configs:"
        echo "       - job_name: 'vimeo_monitor'"
        echo "         scrape_interval: 15s"
        echo "         static_configs:"
        echo "           - targets: ['<your-ip>:$HEALTH_PORT']"
        echo
        echo "6. Check autostart status:"
        echo "   ls -la ~/.config/autostart/"
        echo
        echo "7. View logs:"
        echo "   tail -f $PROJECT_DIR/logs/stream_monitor.log"
        echo
    else
        echo "4. Check autostart status:"
        echo "   ls -la ~/.config/autostart/"
        echo
        echo "5. View logs:"
        echo "   tail -f $PROJECT_DIR/logs/stream_monitor.log"
        echo
    fi
    echo "For troubleshooting, see:"
    echo "   $PROJECT_DIR/docs/troubleshooting.md"
    echo
    echo "For health monitoring documentation, see:"
    echo "   $PROJECT_DIR/docs/health-monitoring.md"
    echo
    log_success "Vimeo Monitor installation completed successfully!"
}

# Main installation process
main() {
    log_info "Starting Vimeo Monitor installation..."
    echo
    
    check_root
    check_system
    install_dependencies
    install_uv
    setup_project
    install_python_dependencies
    setup_environment
    setup_autostart
    test_installation
    show_next_steps
}

# Run main function
main "$@"
