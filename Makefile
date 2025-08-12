.DEFAULT_GOAL := help

# Core Variables
PROJECT_NAME := vimeo-monitor
SERVICE_NAME := vimeo-monitor

.PHONY: help
help: ## Show available commands


# === SETUP & INSTALLATION ===
.PHONY: install-uv
install-uv:
	@echo "🔍 Checking uv installation..."
	@command -v uv >/dev/null 2>&1 || { \
		echo "🚀 Installing uv..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	}
	@echo "✅ uv available: $$(uv --version)"

.PHONY: lint
lint: ## Run code quality checks
	@echo "🔍 Running code quality checks..."
	@uv run ruff check .
	@uv run ruff format .

.PHONY: clean
clean: ## Clean build artifacts and caches
	@echo "🧹 Cleaning up..."
	@rm -rf build/ dist/ *.egg-info .coverage .pytest_cache .mypy_cache .ruff_cache
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true

# === MONITORING ===
.PHONY: status
status: ## Show comprehensive system status


.PHONY: logs
logs: ## Manage logs: make logs ACTION (analyze|compress|rotate|clean)

