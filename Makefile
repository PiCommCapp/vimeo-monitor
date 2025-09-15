# Vimeo Monitor Makefile
# Makefile for Vimeo Monitor project with uv, autostart, and cleanup commands

.PHONY: help install setup serve build clean autostart-install autostart-remove test run

# Default target
help:
	@echo "Vimeo Monitor - Available commands:"
	@echo "  install         - Install uv package manager"
	@echo "  setup           - Create virtual environment and install dependencies"
	@echo "  test            - Run the Vimeo Monitor (test mode)"
	@echo "  run             - Run the Vimeo Monitor"
	@echo "  autostart-install - Install autostart desktop files"
	@echo "  autostart-remove  - Remove autostart desktop files"
	@echo "  serve           - Start MkDocs development server"
	@echo "  build           - Build MkDocs static site"
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
	@echo "Installing xrandr.desktop..."
	@cp install/xrandr.desktop ~/.config/autostart/
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

# Development workflow - setup and serve
dev: setup serve

# Full build workflow
deploy: build
	@echo "Site built in 'site/' directory"
	@echo "Ready for deployment!"
