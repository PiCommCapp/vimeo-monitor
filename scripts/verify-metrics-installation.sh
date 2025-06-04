#!/bin/bash

# Vimeo Monitor Metrics Installation Verification Script
# This script verifies that the Prometheus metrics are properly configured and accessible

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
INSTALL_DIR="/opt/vimeo-monitor"
METRICS_PORT="8000"
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

# Check if service is installed
check_service_installation() {
  log_step "Checking service installation..."

  if [[ -d "$INSTALL_DIR" ]]; then
    log_success "Installation directory exists: $INSTALL_DIR"
  else
    log_error "Installation directory not found: $INSTALL_DIR"
    return 1
  fi

  if [[ -f "$INSTALL_DIR/.env" ]]; then
    log_success "Environment configuration file exists"
  else
    log_error "Environment configuration file missing: $INSTALL_DIR/.env"
    return 1
  fi

  return 0
}

# Check Prometheus metrics configuration
check_metrics_configuration() {
  log_step "Checking Prometheus metrics configuration..."

  local env_file="$INSTALL_DIR/.env"

  if grep -q "ENABLE_PROMETHEUS_METRICS=true" "$env_file"; then
    log_success "Prometheus metrics enabled in configuration"
  else
    log_warning "Prometheus metrics not enabled in configuration"
    return 1
  fi

  if grep -q "PROMETHEUS_METRICS_PORT=" "$env_file"; then
    local port=$(grep "PROMETHEUS_METRICS_PORT=" "$env_file" | cut -d'=' -f2)
    log_success "Metrics port configured: $port"
    METRICS_PORT="$port"
  else
    log_info "Using default metrics port: $METRICS_PORT"
  fi

  return 0
}

# Check if service is running
check_service_status() {
  log_step "Checking service status..."

  if command -v systemctl >/dev/null 2>&1; then
    if systemctl is-active --quiet "$SERVICE_NAME"; then
      log_success "Service is running"
      return 0
    else
      log_warning "Service is not running"
      return 1
    fi
  elif [[ "$OSTYPE" == "darwin"* ]]; then
    if launchctl list | grep -q vimeomonitor; then
      log_success "Service is running (macOS)"
      return 0
    else
      log_warning "Service is not running (macOS)"
      return 1
    fi
  else
    log_warning "Cannot check service status on this platform"
    return 1
  fi
}

# Test metrics endpoint
test_metrics_endpoint() {
  log_step "Testing Prometheus metrics endpoint..."

  local endpoint="http://localhost:$METRICS_PORT/metrics"

  # Wait a moment for service to be ready
  sleep 2

  if curl -s --max-time 10 "$endpoint" >/dev/null 2>&1; then
    log_success "Metrics endpoint accessible: $endpoint"

    # Get sample metrics
    local sample_metrics=$(curl -s --max-time 5 "$endpoint" | head -5)
    if [[ -n "$sample_metrics" ]]; then
      log_info "Sample metrics output:"
      echo "$sample_metrics"
      log_success "Metrics data is being generated"
    else
      log_warning "Metrics endpoint accessible but no data returned"
    fi

    return 0
  else
    log_error "Metrics endpoint not accessible: $endpoint"
    return 1
  fi
}

# Check specific Vimeo Monitor metrics
check_vimeo_metrics() {
  log_step "Checking for Vimeo Monitor specific metrics..."

  local endpoint="http://localhost:$METRICS_PORT/metrics"

  if curl -s --max-time 10 "$endpoint" | grep -q "vimeo_monitor_"; then
    log_success "Vimeo Monitor metrics found"

    # Count the metrics
    local metric_count=$(curl -s --max-time 5 "$endpoint" | grep -c "^vimeo_monitor_" || echo "0")
    log_info "Found $metric_count Vimeo Monitor metrics"

    # Show some key metrics
    log_info "Key metrics available:"
    curl -s --max-time 5 "$endpoint" | grep "^vimeo_monitor_" | head -3 | while read -r line; do
      echo "  - $(echo "$line" | cut -d' ' -f1)"
    done

    return 0
  else
    log_error "No Vimeo Monitor specific metrics found"
    return 1
  fi
}

# Start service if not running
start_service_if_needed() {
  log_step "Starting service if needed..."

  if ! check_service_status; then
    log_info "Attempting to start service..."

    if command -v systemctl >/dev/null 2>&1; then
      sudo systemctl start "$SERVICE_NAME"
      sleep 5
      if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_success "Service started successfully"
        return 0
      else
        log_error "Failed to start service"
        return 1
      fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
      sudo launchctl load /Library/LaunchDaemons/com.vimeomonitor.service.plist
      sleep 5
      if launchctl list | grep -q vimeomonitor; then
        log_success "Service started successfully (macOS)"
        return 0
      else
        log_error "Failed to start service (macOS)"
        return 1
      fi
    else
      log_error "Cannot start service on this platform"
      return 1
    fi
  fi

  return 0
}

# Main verification function
main() {
  echo "🔍 Vimeo Monitor Metrics Installation Verification"
  echo "================================================="
  echo

  local all_tests_passed=true

  # Run verification steps
  if ! check_service_installation; then
    log_error "Service installation verification failed"
    all_tests_passed=false
  fi

  if ! check_metrics_configuration; then
    log_error "Metrics configuration verification failed"
    all_tests_passed=false
  fi

  # Try to start service if needed
  if ! start_service_if_needed; then
    log_error "Could not ensure service is running"
    all_tests_passed=false
  fi

  # Test metrics endpoint
  if ! test_metrics_endpoint; then
    log_error "Metrics endpoint test failed"
    all_tests_passed=false
  fi

  # Check Vimeo-specific metrics
  if ! check_vimeo_metrics; then
    log_error "Vimeo Monitor metrics verification failed"
    all_tests_passed=false
  fi

  echo
  if [[ "$all_tests_passed" == "true" ]]; then
    log_success "🎉 All verification tests passed!"
    echo
    log_info "Prometheus metrics are properly installed and accessible at:"
    echo "  📊 Metrics URL: http://localhost:$METRICS_PORT/metrics"
    echo "  🔧 Service: $SERVICE_NAME"
    echo "  📁 Installation: $INSTALL_DIR"
    echo
    log_info "You can now:"
    echo "  - Configure Prometheus to scrape: http://localhost:$METRICS_PORT/metrics"
    echo "  - Set up Grafana dashboard using this endpoint"
    echo "  - Monitor application metrics in real-time"
  else
    log_error "❌ Some verification tests failed"
    echo
    log_info "Common troubleshooting steps:"
    echo "  - Check service status: sudo systemctl status $SERVICE_NAME"
    echo "  - View service logs: sudo journalctl -u $SERVICE_NAME -f"
    echo "  - Verify configuration: cat $INSTALL_DIR/.env"
    echo "  - Test manual start: sudo systemctl start $SERVICE_NAME"
    echo
    exit 1
  fi
}

# Run main function
main "$@"
