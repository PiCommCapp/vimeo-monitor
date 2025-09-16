# Development Setup

Guide for setting up a development environment for the Vimeo Monitor project.

## 🔧 Prerequisites

### System Requirements
- **Python**: 3.12 or newer
- **OS**: Linux (Ubuntu, Raspberry Pi OS, or similar)
- **Memory**: 1GB RAM minimum, 2GB recommended
- **Storage**: 500MB free space

### Required Software
- **VLC**: `sudo apt install vlc` (Ubuntu/Debian)
- **FFmpeg**: `sudo apt install ffmpeg` (Ubuntu/Debian)
- **Git**: `sudo apt install git` (Ubuntu/Debian)
- **uv**: Python package manager (install instructions below)

## 🚀 Development Environment Setup

### Step 1: Install uv Package Manager
```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Reload shell or source profile
source ~/.bashrc
```

### Step 2: Clone Repository
```bash
# Clone the repository
git clone https://github.com/PiCommCapp/vimeo-monitor.git
cd vimeo-monitor

# Add upstream remote (for contributing)
git remote add upstream https://github.com/PiCommCapp/vimeo-monitor.git
```

### Step 3: Install Dependencies
```bash
# Install all dependencies including development tools
uv sync --dev

# Verify installation
uv run python --version
uv run python -c "import vimeo_monitor; print('Installation successful')"
```

### Step 4: Set Up Pre-commit Hooks
```bash
# Install pre-commit hooks
uv run pre-commit install

# Test pre-commit hooks
uv run pre-commit run --all-files
```

## 🧪 Testing Setup

### Running Tests
```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=src/vimeo_monitor --cov-report=html

# Run specific test file
uv run pytest tests/test_monitor.py

# Run with verbose output
uv run pytest -v

# Run tests in watch mode (rerun on file changes)
uv run pytest-watch
```

### Test Configuration
The project uses pytest with the following configuration:

```python
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --strict-markers --strict-config
```

### Coverage Requirements
- **Minimum Coverage**: 80% overall
- **Critical Paths**: 90% coverage for core modules
- **New Code**: 100% coverage for new functionality

## 🔍 Code Quality Tools

### Code Formatting
```bash
# Format code with Black
uv run black src/ tests/

# Check formatting
uv run black --check src/ tests/
```

### Import Sorting
```bash
# Sort imports with isort
uv run isort src/ tests/

# Check import sorting
uv run isort --check-only src/ tests/
```

### Type Checking
```bash
# Run type checking with mypy
uv run mypy src/

# Run with strict mode
uv run mypy --strict src/
```

### Linting
```bash
# Run linting with flake8
uv run flake8 src/ tests/

# Run with specific configuration
uv run flake8 --config=setup.cfg src/ tests/
```

### All Quality Checks
```bash
# Run all quality checks
uv run pre-commit run --all-files

# Run specific hook
uv run pre-commit run black
uv run pre-commit run mypy
uv run pre-commit run pytest
```

## 📚 Documentation Development

### Building Documentation
```bash
# Build documentation
uv run mkdocs build

# Serve documentation locally
uv run mkdocs serve

# Build with strict mode (fail on warnings)
uv run mkdocs build --strict
```

### Documentation Structure
```
docs/
├── index.md              # Home page
├── installation.md       # Installation guide
├── configuration.md      # Configuration reference
├── quick-start.md        # Quick start guide
├── usage.md              # Usage guide
├── troubleshooting.md    # Troubleshooting guide
├── health-monitoring.md  # Health monitoring guide
├── api-reference.md      # API reference
├── contributing.md       # Contributing guide
├── development.md        # This file
├── architecture.md       # Architecture overview
├── changelog.md          # Version history
└── license.md            # License information
```

### Documentation Standards
- **Markdown**: Use Markdown for all documentation
- **Examples**: Include code examples where helpful
- **Links**: Use relative links for internal documentation
- **Structure**: Follow existing documentation structure

## 🔧 Development Workflow

### Feature Development
1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write code following style guidelines
   - Add tests for new functionality
   - Update documentation as needed

3. **Test Changes**
   ```bash
   # Run tests
   uv run pytest
   
   # Run quality checks
   uv run pre-commit run --all-files
   
   # Build documentation
   uv run mkdocs build
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   # Create pull request on GitHub
   ```

### Bug Fix Workflow
1. **Create Bug Fix Branch**
   ```bash
   git checkout -b fix/issue-description
   ```

2. **Fix Bug**
   - Identify and fix the issue
   - Add test to prevent regression
   - Update documentation if needed

3. **Test Fix**
   ```bash
   # Run specific test
   uv run pytest tests/test_specific_issue.py
   
   # Run all tests
   uv run pytest
   ```

4. **Commit and Push**
   ```bash
   git add .
   git commit -m "fix: resolve issue description"
   git push origin fix/issue-description
   ```

## 🐛 Debugging

### Debug Configuration
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with debug output
uv run python -m vimeo_monitor
```

### Debug Tools
```bash
# Run with Python debugger
uv run python -m pdb -m vimeo_monitor

# Run with verbose output
uv run python -m vimeo_monitor --verbose

# Check configuration
uv run python -c "from src.vimeo_monitor.config import Config; print(Config())"
```

### Log Analysis
```bash
# View logs in real-time
tail -f logs/vimeo_monitor.log

# Search logs for specific errors
grep -i error logs/vimeo_monitor.log

# View recent logs
tail -n 100 logs/vimeo_monitor.log
```

## 🔄 Continuous Integration

### Local CI Testing
```bash
# Run all CI checks locally
uv run pytest
uv run black --check src/ tests/
uv run isort --check-only src/ tests/
uv run mypy src/
uv run flake8 src/ tests/
uv run mkdocs build --strict
```

### GitHub Actions
The project uses GitHub Actions for CI/CD:

- **Tests**: Run pytest on multiple Python versions
- **Code Quality**: Run black, isort, mypy, flake8
- **Documentation**: Build and deploy MkDocs
- **Security**: Run security scans

## 📦 Package Management

### Dependency Management
```bash
# Add new dependency
uv add package-name

# Add development dependency
uv add --dev package-name

# Update dependencies
uv sync --upgrade

# Remove dependency
uv remove package-name
```

### Virtual Environment
```bash
# Activate virtual environment
source .venv/bin/activate

# Deactivate virtual environment
deactivate

# Show installed packages
uv pip list
```

## 🚀 Performance Testing

### Benchmarking
```bash
# Run performance tests
uv run pytest tests/test_performance.py

# Profile memory usage
uv run python -m memory_profiler src/vimeo_monitor/monitor.py

# Profile CPU usage
uv run python -m cProfile -m vimeo_monitor
```

### Load Testing
```bash
# Test with high load
uv run python -m vimeo_monitor --load-test

# Monitor system resources
htop
```

## 📚 Related Documentation

- **[Contributing](contributing.md)** - How to contribute to the project
- **[API Reference](api-reference.md)** - Complete API documentation
- **[Configuration](configuration.md)** - Configuration reference
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions
