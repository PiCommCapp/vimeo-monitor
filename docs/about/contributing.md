# Contributing to vimeo-monitor

Thank you for your interest in contributing to vimeo-monitor! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for everyone.

## How to Contribute

### Reporting Bugs

- Check if the bug has already been reported in the Issues section
- Use the bug report template when creating a new issue
- Include detailed steps to reproduce the bug
- Include expected and actual behavior
- Include relevant logs and screenshots if applicable

### Suggesting Features

- Check if the feature has already been suggested in the Issues section
- Use the feature request template when creating a new issue
- Provide a clear description of the feature
- Explain why this feature would be useful
- Include any relevant examples or mockups

### Pull Requests

1. Fork the repository
2. Create a new branch for your feature/fix
3. Make your changes
4. Write or update tests as needed
5. Ensure all tests pass
6. Update documentation if necessary
7. Submit a pull request

### Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/vimeo-monitor.git
   cd vimeo-monitor
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

### Code Style

- Follow PEP 8 style guide for Python code
- Use meaningful variable and function names
- Write docstrings for all public functions and classes
- Keep functions small and focused
- Write unit tests for new functionality

### Testing

- Run tests before submitting a pull request:
  ```bash
  pytest
  ```
- Ensure test coverage remains high
- Add tests for new features and bug fixes

### Documentation

- Update documentation for any new features or changes
- Follow the existing documentation style
- Include examples where appropriate
- Keep the README up to date

## Commit Messages

- Use clear and descriptive commit messages
- Reference issues and pull requests when applicable
- Follow conventional commits format:
  - feat: A new feature
  - fix: A bug fix
  - docs: Documentation changes
  - style: Code style changes
  - refactor: Code refactoring
  - test: Adding or modifying tests
  - chore: Maintenance tasks

## Review Process

1. All pull requests require at least one review
2. Address any feedback from reviewers
3. Ensure CI checks pass
4. Once approved, a maintainer will merge your changes

## Questions?

If you have any questions about contributing, please:
- Open an issue
- Contact the maintainers
- Check the project documentation

Thank you for contributing to vimeo-monitor!
