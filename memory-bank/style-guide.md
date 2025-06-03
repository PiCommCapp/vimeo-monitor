# Style Guide

## Python Coding Style

This project follows PEP 8 and additional style conventions as enforced by the ruff linter configured in pyproject.toml.

### General Guidelines

- Use 4 spaces for indentation (no tabs)
- Line length limit of 120 characters (as per ruff config)
- Use snake_case for variable and function names
- Use CamelCase for class names
- Use UPPER_CASE for constants
- Use docstrings for all functions, classes, and modules

### Import Style

- Imports should be grouped in the following order:
  1. Standard library imports
  2. Related third-party imports
  3. Local application/library specific imports
- Within each group, imports should be sorted alphabetically
- Use absolute imports rather than relative imports when possible

```python
# Standard library imports
import os
import time
import subprocess
import logging

# Third-party imports
from vimeo import VimeoClient
from requests.exceptions import RequestException

# Local imports
from vimeo_monitor.utils import some_utility
```

### Comments

- Use comments sparingly and only when needed to explain complex logic
- Prefer self-documenting code through clear naming and structure
- Use docstrings for all public modules, functions, classes, and methods

### Error Handling

- Use specific exception types rather than bare `except:` clauses
- Always log exceptions with appropriate context
- Prefer try/except over checking conditions where appropriate

```python
try:
    # Operation that might fail
    result = operation()
except SpecificException as e:
    logging.error("Operation failed: %s", str(e))
    logging.debug("Full error details:", exc_info=True)
```

### Logging

- Use appropriate log levels:
  - DEBUG: Detailed information for debugging
  - INFO: Confirmation that things are working as expected
  - WARNING: Something unexpected happened but the application can continue
  - ERROR: More serious problem, application may not be able to perform a function
  - CRITICAL: Very serious error, application may not be able to continue
- Include context in log messages

```python
logging.info("Starting operation with parameter: %s", parameter)
logging.error("Failed to connect to API: %s", error_message)
```

## Code Organization

### Module Structure

- Each module should have a clear, single responsibility
- Use separate modules for distinct functionality
- Include `__init__.py` files to define public API

### Function and Method Guidelines

- Functions should do one thing and do it well
- Keep functions short and focused
- Use descriptive names that indicate what the function does
- Use type hints for function parameters and return values

```python
def check_stream_status(stream_id: str) -> bool:
    """Check if the stream with the given ID is active.
    
    Args:
        stream_id: The ID of the stream to check
        
    Returns:
        True if the stream is active, False otherwise
    """
    # Function implementation
```

## Testing Guidelines

- Write tests for all functionality
- Use pytest for test framework
- Keep tests in a separate `tests` directory mirroring the package structure
- Name test files with `test_` prefix
- Name test functions with `test_` prefix
- Test both success and failure cases

## Documentation

- All code should be self-documenting
- Use docstrings for all public modules, classes, functions, and methods
- Document parameters, return values, and exceptions
- Provide examples where appropriate

## Configuration

- Keep configuration separate from code
- Use environment variables for configuration
- Document all configuration options
- Provide sensible defaults
- Validate configuration values
