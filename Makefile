# Vimeo Monitor Makefile
# Makefile for Vimeo Monitor project with uv, autostart, and cleanup commands

.PHONY: help install setup serve build clean autostart-install autostart-remove test test-unit test-integration test-error-scenarios test-documentation test-health test-slow test-all run lint lint-strict format lint-fix uninstall fix-gpu-memory check-gpu-memory fix-video-resolution check-video-resolution

# Default target
## help: Display available commands
help:
	@echo "Vimeo Monitor - Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  setup           - Create virtual environment and install dependencies"
	@echo "  test            - Run the Vimeo Monitor (test mode)"
	@echo "  test-unit       - Run unit tests"
	@echo "  test-integration - Run integration tests"
	@echo "  test-error-scenarios - Run error scenario tests"
	@echo "  test-documentation - Run documentation tests"
	@echo "  test-health     - Run health monitoring tests"
	@echo "  test-slow       - Run slow tests"
	@echo "  test-all        - Run all tests (system + unit)"
	@echo "  run             - Run the Vimeo Monitor"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint            - Run basic linting (ruff, black, isort)"
	@echo "  lint-strict     - Run strict linting (includes mypy type checking)"
	@echo "  format          - Auto-format code with black and isort"
	@echo "  lint-fix        - Auto-fix linting issues"
	@echo ""
	@echo "Installation:"
	@echo "  install         - Run automated installation script"
	@echo "  uninstall       - Run automated uninstallation script"
	@echo "  autostart-install - Install autostart desktop files"
	@echo "  autostart-remove  - Remove autostart desktop files"
	@echo ""
	@echo "System Configuration:"
	@echo "  fix-gpu-memory  - Fix GPU memory allocation for video playback"
	@echo "  check-gpu-memory - Check current GPU memory allocation"
	@echo "  fix-video-resolution - Set static HDMI video resolution (1920x1080@50Hz)"
	@echo "  check-video-resolution - Check current video resolution configuration"
	@echo ""
	@echo "Documentation:"
	@echo "  serve           - Start MkDocs development server"
	@echo "  build           - Build MkDocs static site"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean           - Clean all build artifacts and temporary files"
	@echo "  help            - Show this help message"

# Install uv package manager
install:
	@echo "Installing uv..."
	curl -LsSf https://astral.sh/uv/install.sh | sh
	@echo "uv installed successfully!"

# Create virtual environment and install dependencies
setup:
	@echo "Setting up Vimeo Monitor environment..."
	@echo "Installing dependencies with uv..."
	uv sync
	@echo "Creating required directories..."
	@mkdir -p logs media
	@echo "Setup complete!"

# Start MkDocs development server using uvx (no local install needed)
serve:
	@echo "Starting MkDocs development server..."
	uvx mkdocs serve

# Build MkDocs static site using uvx
build:
	@echo "Building MkDocs static site..."
	uvx mkdocs build

# Run Vimeo Monitor (test mode with timeout)
test:
	@echo "Running Vimeo Monitor in test mode (5 second timeout)..."
	@timeout 5 uv run streammonitor.py || echo "Test completed"

# Run unit tests
test-unit:
	@echo "Running unit tests..."
	@uv run python -m pytest tests/ -v -m "unit"

# Run integration tests
test-integration:
	@echo "Running integration tests..."
	@uv run python -m pytest tests/integration/ -v -m "integration"

# Run error scenario tests
test-error-scenarios:
	@echo "Running error scenario tests..."
	@uv run python -m pytest tests/error_scenarios/ -v -m "error_scenarios"

# Run documentation tests
test-documentation:
	@echo "Running documentation tests..."
	@uv run python -m pytest tests/test_documentation.py -v -m "documentation"

# Run health monitoring tests
test-health:
	@echo "Running health monitoring tests..."
	@uv run python -m pytest tests/test_health_module.py -v -m "health"

# Run slow tests
test-slow:
	@echo "Running slow tests..."
	@uv run python -m pytest tests/ -v -m "slow"

# Run all tests
test-all: test test-unit test-integration test-error-scenarios test-documentation test-health
	@echo "All tests completed"

# Lint the codebase
lint:
	@echo "Running code linting..."
	@echo "Running ruff (fast linter)..."
	@uv run ruff check src/ tests/ streammonitor.py
	@echo "Running black (code formatter)..."
	@uv run black --check src/ tests/ streammonitor.py
	@echo "Running isort (import sorter)..."
	@uv run isort --check-only src/ tests/ streammonitor.py
	@echo "Linting completed successfully!"

# Lint with type checking
lint-strict:
	@echo "Running strict code linting..."
	@echo "Running ruff (fast linter)..."
	@uv run ruff check src/ tests/ streammonitor.py
	@echo "Running black (code formatter)..."
	@uv run black --check src/ tests/ streammonitor.py
	@echo "Running isort (import sorter)..."
	@uv run isort --check-only src/ tests/ streammonitor.py
	@echo "Running mypy (type checker)..."
	@uv run mypy src/ streammonitor.py
	@echo "Strict linting completed successfully!"

# Format the codebase
format:
	@echo "Auto-formatting code..."
	@uv run black src/ tests/ streammonitor.py
	@uv run isort src/ tests/ streammonitor.py
	@echo "Code formatting completed!"

# Auto-fix linting issues
lint-fix:
	@echo "Auto-fixing linting issues..."
	@uv run ruff check --fix src/ tests/ streammonitor.py
	@uv run black src/ tests/ streammonitor.py
	@uv run isort src/ tests/ streammonitor.py
	@echo "Linting fixes completed!"

# CI/CD validation (same as GitHub Actions)
ci-validate:
	@echo "Running CI/CD validation..."
	@echo "Running linting (ruff)..."
	@uv run ruff check .
	@echo "Running formatting check (black)..."
	@uv run black --check .
	@echo "Running import sorting check (isort)..."
	@uv run isort --check-only .
	@echo "Running type checking (mypy)..."
	@uv run mypy src/
	@echo "Running tests..."
	@uv run pytest tests/ -v --cov=src --cov-report=xml
	@echo "CI/CD validation completed successfully!"

# Build documentation

# Run Vimeo Monitor
run:
	@echo "Starting Vimeo Monitor..."
	@uv run streammonitor.py

# Install autostart desktop files
autostart-install:
	@echo "Installing autostart desktop files..."
	@echo "Creating ~/.config/autostart directory..."
	@mkdir -p ~/.config/autostart
	@echo "Installing streamreturn.desktop..."
	@cp install/streamreturn.desktop ~/.config/autostart/
	@echo "Autostart files installed successfully!"
	@echo "Vimeo Monitor will start automatically on next login."

# Remove autostart desktop files
autostart-remove:
	@echo "Removing autostart desktop files..."
	@rm -f ~/.config/autostart/streamreturn.desktop
	@rm -f ~/.config/autostart/xrandr.desktop
	@echo "Autostart files removed successfully!"

# Clean all build artifacts and temporary files
clean:
	@echo "Cleaning Vimeo Monitor project..."
	@echo "Removing build artifacts..."
	@rm -rf site/
	@rm -rf .cache/
	@rm -rf .pytest_cache/
	@rm -rf __pycache__/
	@rm -rf src/__pycache__/
	@rm -rf src/vimeo_monitor/__pycache__/
	@echo "Removing log files..."
	@rm -f logs/*.log*
	@echo "Removing Python cache files..."
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "Removing temporary files..."
	@rm -f .coverage
	@rm -f .coverage.*
	@rm -rf htmlcov/
	@rm -rf dist/
	@rm -rf build/
	@rm -rf *.egg-info/
	@rm -rf vimeo_monitor.egg-info/
	@echo "Clean complete!"

# Installation targets
uninstall:
	@echo "Running uninstallation script..."
	@chmod +x scripts/uninstall.sh
	@./scripts/uninstall.sh

# Development workflow - setup and serve
dev: setup serve

# Full build workflow
deploy: build
	@echo "Site built in 'site/' directory"
	@echo "Ready for deployment!"

# System Configuration Commands
fix-gpu-memory:
	@echo "Fixing GPU memory allocation for video playback..."
	@echo "Current GPU memory allocation:"
	@vcgencmd get_mem gpu || echo "vcgencmd not available"
	@echo ""
	@echo "Checking if gpu_mem is already configured..."
	@if grep -q "^gpu_mem=" /boot/firmware/config.txt 2>/dev/null; then \
		echo "GPU memory already configured in /boot/firmware/config.txt"; \
		grep "^gpu_mem=" /boot/firmware/config.txt; \
	else \
		echo "Adding gpu_mem=128 to /boot/firmware/config.txt..."; \
		echo "gpu_mem=128" | sudo tee -a /boot/firmware/config.txt; \
		echo "GPU memory allocation updated successfully!"; \
		echo ""; \
		echo "⚠️  IMPORTANT: A reboot is required for changes to take effect."; \
		echo "   Run: sudo reboot"; \
		echo ""; \
		echo "After reboot, verify with: make check-gpu-memory"; \
	fi

check-gpu-memory:
	@echo "Checking GPU memory allocation..."
	@echo "Current GPU memory:"
	@vcgencmd get_mem gpu || echo "vcgencmd not available"
	@echo ""
	@echo "Current ARM memory:"
	@vcgencmd get_mem arm || echo "vcgencmd not available"
	@echo ""
	@echo "System temperature:"
	@vcgencmd measure_temp || echo "vcgencmd not available"

# Video resolution configuration commands
fix-video-resolution:
	@echo "Setting static video resolution (1920x1080@50Hz)..."
	@echo "This requires sudo privileges to modify boot configuration"
	@chmod +x scripts/fix-video-resolution.sh
	@sudo scripts/fix-video-resolution.sh
	@echo ""
	@echo "After reboot, verify with: make check-video-resolution"

check-video-resolution:
	@echo "Checking video resolution configuration..."
	@chmod +x scripts/check-video-resolution.sh
	@scripts/check-video-resolution.sh
