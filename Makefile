.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help message
	@echo "🔧 Vimeo Monitor - Available Commands"
	@echo "====================================="
	@echo ""
	@echo "📦 Installation & Setup:"
	@echo "  setup                Complete setup: check status, install dependencies, and verify"
	@echo "  setup-service        Complete setup including system service installation"
	@echo "  install              Install the virtual environment and dependencies"
	@echo "  install-uv           Install uv package manager"
	@echo "  status               Check installation status of key components"
	@echo ""
	@echo "🔧 Service Management:"
	@echo "  install-service      Install Vimeo Monitor as a system service (requires sudo)"
	@echo "  uninstall-service    Uninstall Vimeo Monitor system service (requires sudo)"
	@echo "  service-start        Start the Vimeo Monitor service"
	@echo "  service-stop         Stop the Vimeo Monitor service"
	@echo "  service-restart      Restart the Vimeo Monitor service"
	@echo "  service-status       Check the status of the Vimeo Monitor service"
	@echo "  service-logs         View service logs"
	@echo "  verify-metrics       Verify Prometheus metrics installation and accessibility"
	@echo "  install-logrotate    Install system logrotate configuration (requires sudo)"
	@echo "  test-logrotate       Test logrotate configuration without actually rotating"
	@echo "  force-logrotate      Force log rotation now (for testing)"
	@echo ""
	@echo "📋 Development & Testing:"
	@echo "  test                 Run tests with pytest"
	@echo "  test-network         Run network monitoring tests"
	@echo "  test-performance     Test performance optimization functionality"
	@echo "  test-tui             Test TUI installation and functionality"
	@echo "  tui                  Launch the Terminal User Interface (TUI)"
	@echo "  tui-dev              Launch TUI in development mode with debug logging"
	@echo "  benchmark-performance Run performance benchmarks"
	@echo "  performance-status   Show current performance metrics"
	@echo "  clear-caches         Clear all application caches"
	@echo "  lint                 Run code linting checks"
	@echo "  format               Format code using ruff"
	@echo "  check                Run all checks (linting and tests)"
	@echo "  clean                Clean up build artifacts and cache files"
	@echo "  build                Build the project package"
	@echo ""
	@echo "📊 Log Management:"
	@echo "  analyze-logs         Analyze log files and show statistics"
	@echo "  compress-logs        Compress old log files to save space"
	@echo "  rotate-logs          Manually rotate current log file"
	@echo "  clean-logs           Clean old log files (keep current log)"
	@echo "  clean-old-logs       Clean log files older than 30 days"
	@echo ""
	@echo "📚 Documentation:"
	@echo "  docs                 Build documentation"
	@echo "  serve-docs           Serve documentation locally"
	@echo "  help                 Show this help message"
	@echo ""
	@echo "🔧 Other:"
	@echo "  update-deps          Update project dependencies"
	@echo ""
	@echo "💡 Quick Start:"
	@echo "  • Development:     make setup"
	@echo "  • With Service:    make setup-service"
	@echo "  • Check Status:    make status"
	@echo "  • Run Tests:       make test"
	@echo "  • View Logs:       make service-logs"
	@echo ""

.PHONY: install-uv
install-uv: ## Install uv package manager
	@echo "🔍 Checking for uv installation..."
	@if command -v uv >/dev/null 2>&1; then \
		echo "✅ uv is already installed: $$(uv --version)"; \
	else \
		echo "🚀 Installing uv package manager..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		echo "✅ uv installation completed"; \
	fi

.PHONY: install
install: ## Install the virtual environment and dependencies
	@echo "🔍 Checking for uv installation..."
	@if ! command -v uv >/dev/null 2>&1; then \
		echo "⚠️  uv not found, installing automatically..."; \
		$(MAKE) install-uv; \
	else \
		echo "✅ uv is available: $$(uv --version)"; \
	fi
	@echo "🚀 Creating virtual environment and installing dependencies"
	@uv sync
	@echo "📋 Installing logrotate configuration..."
	@if [ ! -f services/logrotation.conf ]; then \
		echo "❌ Error: services/logrotation.conf not found"; \
		exit 1; \
	fi
	@sudo cp services/logrotation.conf /etc/logrotate.d/vimeo-monitor
	@sudo chmod 644 /etc/logrotate.d/vimeo-monitor
	@echo "✅ Logrotate configuration installed to /etc/logrotate.d/vimeo-monitor"
	@echo "📝 Note: Adjust log file paths in the configuration as needed"

.PHONY: install-service
install-service: ## Install Vimeo Monitor as a system service (requires sudo)
	@echo "🚀 Installing Vimeo Monitor as system service..."
	@if [ ! -f scripts/install-service.sh ]; then \
		echo "❌ Error: scripts/install-service.sh not found"; \
		exit 1; \
	fi
	@if [ ! -f services/vimeo-monitor.service ]; then \
		echo "❌ Error: services/vimeo-monitor.service not found"; \
		exit 1; \
	fi
	@echo "⚠️  This will install the service to run at boot automatically"
	@echo "📍 Installation directory: /opt/vimeo-monitor"
	@echo "👤 Service will run as user: vimeo-monitor"
	@echo ""
	@./scripts/install-service.sh

.PHONY: uninstall-service
uninstall-service: ## Uninstall Vimeo Monitor system service (requires sudo)
	@echo "🗑️  Uninstalling Vimeo Monitor system service..."
	@if [ ! -f scripts/uninstall-service.sh ]; then \
		echo "❌ Error: scripts/uninstall-service.sh not found"; \
		exit 1; \
	fi
	@./scripts/uninstall-service.sh

.PHONY: service-status
service-status: ## Check the status of the Vimeo Monitor service
	@echo "🔍 Checking Vimeo Monitor service status..."
	@if command -v systemctl >/dev/null 2>&1; then \
		echo "📊 Systemd Service Status:"; \
		sudo systemctl status vimeo-monitor --no-pager || true; \
		echo ""; \
		echo "📈 Prometheus Metrics Status:"; \
		if curl -s http://localhost:8000/metrics >/dev/null 2>&1; then \
			echo "✅ Metrics endpoint accessible at http://localhost:8000/metrics"; \
			echo "📊 Sample metrics:"; \
			curl -s http://localhost:8000/metrics | head -5; \
		else \
			echo "❌ Metrics endpoint not accessible (service may not be running)"; \
		fi; \
	elif [[ "$$OSTYPE" == "darwin"* ]]; then \
		echo "📊 launchd Service Status:"; \
		sudo launchctl list | grep vimeomonitor || echo "Service not found"; \
		echo ""; \
		echo "📈 Prometheus Metrics Status:"; \
		if curl -s http://localhost:8000/metrics >/dev/null 2>&1; then \
			echo "✅ Metrics endpoint accessible at http://localhost:8000/metrics"; \
		else \
			echo "❌ Metrics endpoint not accessible (service may not be running)"; \
		fi; \
	else \
		echo "⚠️  Service status check not supported on this platform"; \
	fi

.PHONY: service-start
service-start: ## Start the Vimeo Monitor service
	@echo "▶️  Starting Vimeo Monitor service..."
	@if command -v systemctl >/dev/null 2>&1; then \
		sudo systemctl start vimeo-monitor; \
		echo "✅ Service started"; \
	elif [[ "$$OSTYPE" == "darwin"* ]]; then \
		sudo launchctl load /Library/LaunchDaemons/com.vimeomonitor.service.plist; \
		echo "✅ Service started"; \
	else \
		echo "⚠️  Service start not supported on this platform"; \
	fi

.PHONY: service-stop
service-stop: ## Stop the Vimeo Monitor service
	@echo "⏹️  Stopping Vimeo Monitor service..."
	@if command -v systemctl >/dev/null 2>&1; then \
		sudo systemctl stop vimeo-monitor; \
		echo "✅ Service stopped"; \
	elif [[ "$$OSTYPE" == "darwin"* ]]; then \
		sudo launchctl unload /Library/LaunchDaemons/com.vimeomonitor.service.plist; \
		echo "✅ Service stopped"; \
	else \
		echo "⚠️  Service stop not supported on this platform"; \
	fi

.PHONY: service-restart
service-restart: ## Restart the Vimeo Monitor service
	@echo "🔄 Restarting Vimeo Monitor service..."
	@if command -v systemctl >/dev/null 2>&1; then \
		sudo systemctl restart vimeo-monitor; \
		echo "✅ Service restarted"; \
	elif [[ "$$OSTYPE" == "darwin"* ]]; then \
		sudo launchctl unload /Library/LaunchDaemons/com.vimeomonitor.service.plist || true; \
		sudo launchctl load /Library/LaunchDaemons/com.vimeomonitor.service.plist; \
		echo "✅ Service restarted"; \
	else \
		echo "⚠️  Service restart not supported on this platform"; \
	fi

.PHONY: service-logs
service-logs: ## View service logs
	@echo "📋 Viewing Vimeo Monitor service logs..."
	@if command -v systemctl >/dev/null 2>&1; then \
		echo "Use Ctrl+C to exit log viewing"; \
		sudo journalctl -u vimeo-monitor -f; \
	elif [[ "$$OSTYPE" == "darwin"* ]]; then \
		if [ -f /opt/vimeo-monitor/logs/service.log ]; then \
			echo "Use Ctrl+C to exit log viewing"; \
			tail -f /opt/vimeo-monitor/logs/service.log; \
		else \
			echo "❌ Log file not found: /opt/vimeo-monitor/logs/service.log"; \
		fi \
	else \
		echo "⚠️  Service logs not supported on this platform"; \
	fi

.PHONY: install-logrotate
install-logrotate: ## Install system logrotate configuration (requires sudo)
	@echo "📋 Installing logrotate configuration..."
	@if [ ! -f services/logrotation.conf ]; then \
		echo "❌ Error: services/logrotation.conf not found"; \
		exit 1; \
	fi
	@sudo cp services/logrotation.conf /etc/logrotate.d/vimeo-monitor
	@sudo chmod 644 /etc/logrotate.d/vimeo-monitor
	@echo "✅ Logrotate configuration installed to /etc/logrotate.d/vimeo-monitor"
	@echo "📝 Note: Adjust log file paths in the configuration as needed"

.PHONY: test-logrotate
test-logrotate: ## Test logrotate configuration without actually rotating
	@echo "🧪 Testing logrotate configuration..."
	@sudo logrotate -d /etc/logrotate.d/vimeo-monitor

.PHONY: force-logrotate
force-logrotate: ## Force log rotation now (for testing)
	@echo "🔄 Forcing log rotation..."
	@sudo logrotate -f /etc/logrotate.d/vimeo-monitor

.PHONY: clean-logs
clean-logs: ## Clean old log files (keep current log)
	@echo "🧹 Cleaning old log files..."
	@find ./logs -name "*.log.*" -type f -delete 2>/dev/null || true
	@find ./logs -name "*.log.*.gz" -type f -delete 2>/dev/null || true
	@echo "✅ Old log files cleaned"

.PHONY: analyze-logs
analyze-logs: ## Analyze log files and show statistics
	@echo "📊 Analyzing log files..."
	@uv run python services/log_management.py analyze

.PHONY: compress-logs
compress-logs: ## Compress old log files to save space
	@echo "🗜️ Compressing log files..."
	@uv run python services/log_management.py compress

.PHONY: rotate-logs
rotate-logs: ## Manually rotate current log file
	@echo "🔄 Rotating log files..."
	@uv run python services/log_management.py rotate

.PHONY: clean-old-logs
clean-old-logs: ## Clean log files older than 30 days
	@echo "🧹 Cleaning old log files (30+ days)..."
	@uv run python services/log_management.py clean --days 30

.PHONY: clean
clean: ## Clean up build artifacts and cache files
	@echo "🧹 Cleaning up..."
	@rm -rf build/ dist/ *.egg-info .coverage .pytest_cache .mypy_cache .ruff_cache
	@find . -type d -name "__pycache__" -exec rm -rf {} +
	@find . -type f -name "*.pyc" -delete

.PHONY: test
test: ## Run tests with pytest
	@echo "🧪 Running tests..."
	@uv run pytest tests/ -v

.PHONY: test-network
test-network: ## Run network monitoring tests
	@echo "🧪 Running network monitoring tests..."
	@uv run python test_network_monitoring.py

.PHONY: test-performance
test-performance: ## Test performance optimization functionality
	@echo "🧪 Testing performance optimization..."
	@uv run python test_performance_optimization.py

.PHONY: benchmark-performance
benchmark-performance: ## Run performance benchmarks
	@echo "📊 Running performance benchmarks..."
	@echo "This will run the application with performance monitoring for 2 minutes..."
	@timeout 120 uv run -m vimeo_monitor.monitor || echo "Benchmark completed"

.PHONY: performance-status
performance-status: ## Show current performance metrics
	@echo "📈 Performance Status:"
	@echo "Memory usage:"
	@python -c "import psutil; print(f'  CPU: {psutil.cpu_percent()}%'); print(f'  Memory: {psutil.virtual_memory().percent}%')"
	@echo "Disk usage:"
	@df -h . | tail -1 | awk '{print "  Disk: " $$5 " used"}'

.PHONY: clear-caches
clear-caches: ## Clear all application caches
	@echo "🧹 Clearing application caches..."
	@python -c "\
import sys, os; \
sys.path.insert(0, '.'); \
try: \
    from vimeo_monitor.performance import IntelligentCache; \
    cache = IntelligentCache(); \
    cache.clear(); \
    print('✅ Caches cleared'); \
except ImportError: \
    print('⚠️  Performance module not available'); \
except Exception as e: \
    print(f'❌ Error clearing caches: {e}')"

.PHONY: metrics-server
metrics-server: ## Start Prometheus metrics server (standalone)
	@echo "📊 Starting Prometheus metrics server..."
	@echo "Metrics will be available at: http://localhost:8000/metrics"
	@uv run python -c "\
from vimeo_monitor.metrics import PrometheusMetrics; \
import time; \
metrics = PrometheusMetrics(enable_metrics=True, metrics_port=8000); \
metrics.start_metrics_server(); \
print('Metrics server started. Press Ctrl+C to stop...'); \
try: \
    while True: \
        time.sleep(1); \
except KeyboardInterrupt: \
    print('\\nStopping metrics server...'); \
    metrics.stop_metrics_server(); \
    print('Metrics server stopped')"

.PHONY: test-metrics
test-metrics: ## Test Prometheus metrics collection
	@echo "🧪 Testing Prometheus metrics..."
	@uv run python -c "\
from vimeo_monitor.metrics import PrometheusMetrics; \
import time; \
print('Initializing metrics...'); \
metrics = PrometheusMetrics(enable_metrics=True, metrics_port=8001); \
metrics.start_metrics_server(); \
print('Recording test metrics...'); \
metrics.record_api_request('test_endpoint', 0.5, 'success'); \
metrics.record_cache_hit(); \
metrics.update_stream_status('test_stream', True); \
time.sleep(2); \
summary = metrics.get_metrics_summary(); \
print('Metrics summary:', summary); \
exported = metrics.export_metrics(); \
print('Sample metrics output:'); \
print(exported[:500] + '...' if len(exported) > 500 else exported); \
metrics.stop_metrics_server(); \
print('✅ Metrics test completed')"

.PHONY: verify-metrics
verify-metrics: ## Verify Prometheus metrics installation and configuration
	@echo "🔍 Verifying metrics installation..."
	@if [ -f scripts/verify-metrics-installation.sh ]; then \
		sudo ./scripts/verify-metrics-installation.sh; \
	else \
		echo "❌ Verification script not found: scripts/verify-metrics-installation.sh"; \
		exit 1; \
	fi

.PHONY: metrics-status
metrics-status: ## Show current metrics endpoint status
	@echo "📊 Prometheus Metrics Status:"
	@echo "Checking metrics endpoint..."
	@curl -s http://localhost:8000/metrics | head -10 || echo "❌ Metrics server not running (start application or run 'make metrics-server')"
	@echo ""
	@echo "ℹ️  To start metrics server: make metrics-server"
	@echo "ℹ️  To test metrics: make test-metrics"
	@echo "ℹ️  To verify installation: make verify-metrics"

.PHONY: lint
lint: ## Run code linting checks
	@echo "🔍 Running linting checks..."
	@uv run ruff check .
	@uv run mypy vimeo_monitor

.PHONY: format
format: ## Format code using ruff
	@echo "✨ Formatting code..."
	@uv run ruff format .

.PHONY: docs
docs: ## Build documentation
	@echo "📚 Building documentation..."
	@uv run mkdocs build

.PHONY: serve-docs
serve-docs: ## Serve documentation locally
	@echo "🌐 Serving documentation..."
	@uv run mkdocs serve

.PHONY: update-deps
update-deps: ## Update project dependencies
	@echo "🔄 Updating dependencies..."
	@uv pip compile pyproject.toml -o requirements.txt
	@uv pip compile pyproject.toml --extra dev -o requirements-dev.txt

.PHONY: check
check: lint test ## Run all checks (linting and tests)

.PHONY: build
build: clean ## Build the project package
	@echo "🏗️ Building package..."
	@uv run python -m build

.PHONY: status
status: ## Check installation status of key components
	@echo "🔍 System Status Check"
	@echo "======================"
	@printf "📦 uv package manager: "
	@if command -v uv >/dev/null 2>&1; then \
		echo "✅ Installed ($$(uv --version))"; \
	else \
		echo "❌ Not installed (run 'make install-uv')"; \
	fi
	@printf "🐍 Python virtual environment: "
	@if [ -d .venv ]; then \
		echo "✅ Present"; \
	else \
		echo "❌ Missing (run 'make install')"; \
	fi
	@printf "📋 Dependencies: "
	@if [ -f uv.lock ]; then \
		echo "✅ Lock file present"; \
	else \
		echo "⚠️  No lock file (run 'make install')"; \
	fi
	@printf "📝 Log directory: "
	@if [ -d logs ]; then \
		echo "✅ Present"; \
	else \
		echo "⚠️  Missing (will be created automatically)"; \
	fi
	@printf "⚙️  Configuration: "
	@if [ -f .env ]; then \
		echo "✅ .env file present"; \
	else \
		echo "⚠️  Missing .env file (copy from .env.sample)"; \
	fi
	@printf "🔧 System service: "
	@if command -v systemctl >/dev/null 2>&1; then \
		if systemctl is-enabled vimeo-monitor >/dev/null 2>&1; then \
			echo "✅ Installed and enabled"; \
		else \
			echo "❌ Not installed (run 'make install-service')"; \
		fi; \
	elif [[ "$$OSTYPE" == "darwin"* ]]; then \
		if [ -f /Library/LaunchDaemons/com.vimeomonitor.service.plist ]; then \
			echo "✅ Installed"; \
		else \
			echo "❌ Not installed (run 'make install-service')"; \
		fi; \
	else \
		echo "⚠️  Service not supported on this platform"; \
	fi

.PHONY: setup
setup: ## Complete setup: check status, install dependencies, and verify
	@echo "🚀 Starting complete setup..."
	@echo ""
	$(MAKE) status
	@echo ""
	@echo "🔧 Installing dependencies..."
	$(MAKE) install
	@echo ""
	@echo "✅ Setup complete! Running final status check..."
	@echo ""
	$(MAKE) status
	@echo ""
	@echo "🎉 Development setup complete!"
	@echo ""
	@echo "📋 Next steps:"
	@echo "  - Configure .env file with your Vimeo API credentials"
	@echo "  - Run 'uv run -m vimeo_monitor.monitor' to test manually"
	@echo "  - Run 'make install-service' to install as system service"
	@echo ""

.PHONY: setup-service
setup-service: ## Complete setup including system service installation
	@echo "🚀 Starting complete setup with service installation..."
	@echo ""
	$(MAKE) setup
	@echo ""
	@echo "🔧 Installing system service..."
	$(MAKE) install-service
	@echo ""
	@echo "✅ Complete setup with service installation finished!"
	@echo ""

.PHONY: tui
tui: ## Launch the Terminal User Interface (TUI)
	@echo "🚀 Starting Vimeo Monitor TUI..."
	@if [ -f scripts/vimeo-tui ]; then \
		./scripts/vimeo-tui --dev; \
	else \
		echo "❌ TUI script not found at scripts/vimeo-tui"; \
		exit 1; \
	fi

.PHONY: tui-dev
tui-dev: ## Launch TUI in development mode with debug logging
	@echo "🚀 Starting TUI in development mode with debug logging..."
	@if [ -f scripts/vimeo-tui ]; then \
		./scripts/vimeo-tui --dev --log-level DEBUG; \
	else \
		echo "❌ TUI script not found at scripts/vimeo-tui"; \
		exit 1; \
	fi

.PHONY: test-tui
test-tui: ## Test TUI installation and functionality
	@echo "🧪 Testing TUI installation..."
	@if [ -f scripts/vimeo-tui ]; then \
		echo "✅ TUI script found"; \
		./scripts/vimeo-tui --version; \
		echo "📋 TUI help:"; \
		./scripts/vimeo-tui --help | head -10; \
	else \
		echo "❌ TUI script not found at scripts/vimeo-tui"; \
		exit 1; \
	fi
