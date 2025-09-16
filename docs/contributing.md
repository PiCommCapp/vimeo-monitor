# Contributing

We welcome contributions to the Vimeo Monitor project! This guide will help you get started.

## 🤝 How to Contribute

### Types of Contributions
- **Bug fixes**: Fix issues and improve reliability
- **Feature enhancements**: Add new functionality
- **Documentation**: Improve guides and API documentation
- **Testing**: Add tests and improve test coverage
- **Performance**: Optimize system performance

### Getting Started
1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a feature branch** for your changes
4. **Make your changes** following our guidelines
5. **Test your changes** thoroughly
6. **Submit a pull request** with a clear description

## 🔧 Development Setup

### Prerequisites
- Python 3.12 or newer
- VLC media player (`cvlc`)
- FFmpeg (`ffplay`)
- Git for version control

### Setup Development Environment
```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/vimeo-monitor.git
cd vimeo-monitor

# Install dependencies
uv sync

# Install development dependencies
uv sync --dev

# Set up pre-commit hooks
uv run pre-commit install
```

### Development Dependencies
- **Testing**: pytest, pytest-cov
- **Code Quality**: black, isort, mypy, flake8
- **Documentation**: mkdocs, mkdocs-material
- **Pre-commit**: pre-commit hooks for code quality

## 📝 Code Style Guidelines

### Python Code Style
- **Formatting**: Use Black for code formatting
- **Import Sorting**: Use isort for import organization
- **Type Hints**: Use mypy for type checking
- **Linting**: Use flake8 for code linting

### Code Quality Standards
- **Type Annotations**: All functions must have type hints
- **Documentation**: All public functions must have docstrings
- **Testing**: New features must include tests
- **Error Handling**: Proper error handling and logging

### File Organization
- **Module Structure**: Follow existing module organization
- **Naming Conventions**: Use descriptive, clear names
- **File Size**: Keep files under 300 lines when possible
- **Separation of Concerns**: Each module should have a single responsibility

## 🧪 Testing

### Running Tests
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/vimeo_monitor

# Run specific test file
uv run pytest tests/test_monitor.py

# Run with verbose output
uv run pytest -v
```

### Test Requirements
- **Coverage**: Maintain test coverage above 80%
- **Unit Tests**: Test individual functions and methods
- **Integration Tests**: Test module interactions
- **Error Cases**: Test error handling and edge cases

### Writing Tests
```python
import pytest
from src.vimeo_monitor.config import Config

def test_config_loading():
    """Test configuration loading from environment variables."""
    config = Config()
    assert config.vimeo_access_token is not None
    assert config.vimeo_stream_id is not None

def test_config_validation():
    """Test configuration validation."""
    with pytest.raises(ValueError):
        # Test invalid configuration
        pass
```

## 📚 Documentation

### Documentation Standards
- **Markdown**: Use Markdown for all documentation
- **Structure**: Follow existing documentation structure
- **Examples**: Include code examples where helpful
- **Links**: Use relative links for internal documentation

### Updating Documentation
- **API Changes**: Update API reference when changing interfaces
- **Configuration**: Update configuration guide when adding new options
- **Examples**: Update examples when changing functionality
- **Troubleshooting**: Add new issues and solutions as discovered

### Building Documentation
```bash
# Build documentation locally
uv run mkdocs build

# Serve documentation locally
uv run mkdocs serve

# Check for broken links
uv run mkdocs build --strict
```

## 🔄 Pull Request Process

### Before Submitting
1. **Test your changes** thoroughly
2. **Run code quality checks** (black, isort, mypy, flake8)
3. **Update documentation** if needed
4. **Add tests** for new functionality
5. **Check test coverage** meets requirements

### Pull Request Guidelines
- **Clear Title**: Descriptive title explaining the change
- **Detailed Description**: Explain what changed and why
- **Testing**: Describe how you tested the changes
- **Documentation**: Note any documentation updates needed
- **Breaking Changes**: Clearly mark any breaking changes

### Review Process
- **Code Review**: All changes require code review
- **Testing**: Changes must pass all tests
- **Documentation**: Documentation must be updated
- **Approval**: At least one maintainer must approve

## 🐛 Bug Reports

### Reporting Bugs
When reporting bugs, please include:

- **Description**: Clear description of the issue
- **Steps to Reproduce**: Detailed steps to reproduce the bug
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Environment**: OS, Python version, dependencies
- **Logs**: Relevant log files and error messages

### Bug Report Template
```markdown
## Bug Description
Brief description of the bug

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.12.0]
- Dependencies: [e.g., uv 0.1.0]

## Logs
```
Paste relevant log output here
```
```

## 💡 Feature Requests

### Suggesting Features
When suggesting features, please include:

- **Use Case**: Why is this feature needed?
- **Proposed Solution**: How should it work?
- **Alternatives**: Other solutions considered
- **Implementation**: Any implementation ideas

### Feature Request Template
```markdown
## Feature Description
Brief description of the feature

## Use Case
Why is this feature needed?

## Proposed Solution
How should it work?

## Alternatives
Other solutions considered

## Implementation
Any implementation ideas
```

## 📋 Development Checklist

### Before Starting
- [ ] Read this contributing guide
- [ ] Set up development environment
- [ ] Understand the codebase structure
- [ ] Check existing issues and pull requests

### During Development
- [ ] Follow code style guidelines
- [ ] Write tests for new functionality
- [ ] Update documentation as needed
- [ ] Test changes thoroughly

### Before Submitting
- [ ] Run all tests and ensure they pass
- [ ] Run code quality checks
- [ ] Update documentation
- [ ] Write clear commit messages
- [ ] Create descriptive pull request

## 🏷️ Release Process

### Version Numbering
We use semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist
- [ ] Update version numbers
- [ ] Update changelog
- [ ] Run full test suite
- [ ] Build and test documentation
- [ ] Create release notes
- [ ] Tag release
- [ ] Deploy documentation

## 📞 Getting Help

### Community Support
- **GitHub Issues**: Report bugs and request features
- **GitHub Discussions**: Ask questions and discuss ideas
- **Documentation**: Check existing documentation first

### Contact Maintainers
- **GitHub**: @PiCommCapp
- **Issues**: Use GitHub issues for technical questions
- **Discussions**: Use GitHub discussions for general questions

## 📄 License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to the Vimeo Monitor project! Your contributions help make this project better for everyone.
