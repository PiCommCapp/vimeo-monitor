.DEFAULT_GOAL := help

.PHONY: install-uv
install-uv: ## Install uv package manager
	@echo "🚀 Installing uv"
	@curl -LsSf https://astral.sh/uv/install.sh | sh

.PHONY: help
help: ## Show this help message
	@uv run python -c "import re; \
	[[print(f'\033[36m{m[0]:<20}\033[0m {m[1]}') for m in re.findall(r'^([a-zA-Z_-]+):.*?## (.*)$$', open(makefile).read(), re.M)] for makefile in ('$(MAKEFILE_LIST)').strip().split()]"

.PHONY: install
install: ## Install the virtual environment and dependencies
	@echo "🚀 Creating virtual environment"
	@uv sync

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