# 🎨🎨🎨 ENTERING CREATIVE PHASE: ALGORITHM DESIGN

# API Error Type Handling - Design Considerations

## Component Description

This component enhances the error handling capabilities of the vimeo-monitor application by implementing specific handling strategies for different types of API errors. It improves error diagnosis, logging, and recovery strategies based on the nature of the error.

## Requirements & Constraints

### Functional Requirements

1. Distinguish between different types of API errors
2. Implement appropriate handling for each error type
3. Provide detailed logging for troubleshooting
4. Support potential future differentiated responses

### Constraints

1. Must work with the Python requests library error hierarchy
2. Must maintain compatibility with the existing error handling flow
3. Should not overly complicate the main code flow

## API Error Categories

### 1. Connection Errors

**Description:**
Errors related to network connectivity, such as inability to establish a connection to the Vimeo API.

**Common Causes:**

- Network outage
- DNS resolution failure
- Firewall blocking connection
- Server unreachable

**Example Exception:**
`requests.exceptions.ConnectionError`

**Handling Strategy:**

- Log with network diagnostics information
- Potentially trigger network connectivity check
- These errors strongly indicate a local network issue

### 2. Timeout Errors

**Description:**
Errors that occur when a request takes too long to complete.

**Common Causes:**

- Vimeo API server overloaded
- Network congestion
- Request complexity too high

**Example Exception:**
`requests.exceptions.Timeout`

**Handling Strategy:**

- Log with timing information
- Consider increasing timeouts for future requests
- These may be transient and resolve on retry

### 3. HTTP Errors

**Description:**
Errors that occur when the Vimeo API returns an HTTP error status code.

**Common Causes:**

- 400 Bad Request: Invalid parameters
- 401 Unauthorized: Authentication issues
- 403 Forbidden: Permission issues
- 404 Not Found: Resource doesn't exist
- 429 Too Many Requests: Rate limiting
- 500 Server Error: Vimeo API internal error

**Example Exception:**
`requests.exceptions.HTTPError`

**Handling Strategy:**

- Extract status code and response body
- Log detailed information
- For authentication errors (401/403), may require admin intervention
- For rate limiting (429), implement backoff strategy

### 4. SSL Errors

**Description:**
Errors related to SSL certificate validation.

**Common Causes:**

- Invalid or expired SSL certificate
- Certificate authority not trusted
- Clock synchronization issues

**Example Exception:**
`requests.exceptions.SSLError`

**Handling Strategy:**

- Log SSL-specific details
- These may require system configuration changes
- Rarely resolve themselves without intervention

### 5. General Request Exceptions

**Description:**
Any other errors that occur during the request process that don't fit into the above categories.

**Example Exception:**
`requests.exceptions.RequestException` (base class)

**Handling Strategy:**

- Generic error handling
- Log as much context as possible
- Treat as potentially transient

### 6. Unexpected Exceptions

**Description:**
Any other exceptions that are not related to the requests library.

**Example Exception:**
`Exception` (catch-all)

**Handling Strategy:**

- Last resort error handling
- Log full traceback
- Consider these as potential bugs that need investigation

## Design Options Analysis

### Option 1: Simple Error Type Logging

#### Description

Catch different error types and log them differently, but apply the same recovery strategy.

#### Code Structure

```python
try:
    # API request code
    response = client.get(stream_url)
    # Success handling
except requests.exceptions.ConnectionError as e:
    logging.error("Network connection error: %s", str(e))
    increment_failure_counter()
except requests.exceptions.Timeout as e:
    logging.error("Request timeout: %s", str(e))
    increment_failure_counter()
except requests.exceptions.HTTPError as e:
    logging.error("HTTP error: %s", str(e))
    increment_failure_counter()
except requests.exceptions.RequestException as e:
    logging.error("Request error: %s", str(e))
    increment_failure_counter()
except Exception as e:
    logging.error("Unexpected error: %s", str(e))
    logging.exception("Full traceback:")
    increment_failure_counter()
```

#### Pros

- Simple implementation
- Better logging for troubleshooting
- Easy to understand
- Minimal code changes

#### Cons

- Same handling strategy for all error types
- No differentiated recovery based on error type
- Limited future extensibility

### Option 2: Error Type-Based Recovery Strategies

#### Description

Implement different recovery strategies based on the type of error.

#### Code Structure

```python
try:
    # API request code
    response = client.get(stream_url)
    # Success handling
except requests.exceptions.ConnectionError as e:
    logging.error("Network connection error: %s", str(e))
    handle_network_error(e)
except requests.exceptions.Timeout as e:
    logging.error("Request timeout: %s", str(e))
    handle_timeout_error(e)
except requests.exceptions.HTTPError as e:
    status_code = e.response.status_code if hasattr(e, 'response') else None
    logging.error("HTTP error %s: %s", status_code, str(e))
    handle_http_error(e, status_code)
except requests.exceptions.RequestException as e:
    logging.error("Request error: %s", str(e))
    handle_request_error(e)
except Exception as e:
    logging.error("Unexpected error: %s", str(e))
    logging.exception("Full traceback:")
    handle_unexpected_error(e)

def handle_network_error(error):
    # Network-specific handling
    increment_failure_counter()
    # Maybe trigger network diagnostics

def handle_timeout_error(error):
    # Timeout-specific handling
    increment_failure_counter()
    # Maybe increase timeout for next attempt

def handle_http_error(error, status_code):
    # HTTP-specific handling
    if status_code in (401, 403):
        # Authentication issues
        logging.critical("Authentication failure with Vimeo API")
        # Maybe set a flag for admin notification
    elif status_code == 429:
        # Rate limiting
        logging.warning("Rate limit exceeded")
        # Maybe implement more aggressive backoff
    # ...
    increment_failure_counter()

def handle_request_error(error):
    # Generic request error handling
    increment_failure_counter()

def handle_unexpected_error(error):
    # Unexpected error handling
    increment_failure_counter()
    # Maybe trigger admin notification
```

#### Pros

- Differentiated handling based on error type
- More sophisticated recovery strategies
- Better extensibility for future enhancements
- More detailed logging

#### Cons

- More complex implementation
- More code to maintain
- More difficult to test
- Potential for inconsistent behavior

### Option 3: Error Type Weighting

#### Description

Apply different weights to different error types when determining whether to enter failure mode.

#### Code Structure

```python
# Error weights configuration
error_weights = {
    "connection": 1.0,
    "timeout": 0.5,
    "http_4xx": 1.5,
    "http_5xx": 1.0,
    "ssl": 2.0,
    "request": 1.0,
    "unexpected": 2.0
}

try:
    # API request code
    response = client.get(stream_url)
    # Success handling
except requests.exceptions.ConnectionError as e:
    logging.error("Network connection error: %s", str(e))
    handle_api_failure("connection", str(e))
except requests.exceptions.Timeout as e:
    logging.error("Request timeout: %s", str(e))
    handle_api_failure("timeout", str(e))
except requests.exceptions.HTTPError as e:
    status_code = e.response.status_code if hasattr(e, 'response') else None
    error_type = f"http_{status_code // 100}xx"
    logging.error("HTTP error %s: %s", status_code, str(e))
    handle_api_failure(error_type, str(e))
# ... other exception handlers

def handle_api_failure(error_type, error_message):
    global api_failure_count
    
    # Apply weight based on error type
    weight = error_weights.get(error_type, 1.0)
    api_failure_count += weight
    
    logging.error("API failure (%s): %s. Weighted failure count: %f", 
                 error_type, error_message, api_failure_count)
    
    # Check if we should enter failure mode
    if api_failure_count >= API_FAILURE_THRESHOLD:
        enter_failure_mode()
```

#### Pros

- Most sophisticated error handling
- Different error types have appropriate impact
- Critical errors can trigger failure mode faster
- Transient errors have less impact

#### Cons

- Most complex implementation
- Requires tuning of weights
- Hardest to explain and understand
- Most difficult to test

## Recommended Approach

### Option 1: Simple Error Type Logging

For the vimeo-monitor application, the simple error type logging approach (Option 1) is recommended for the following reasons:

1. **Simplicity**: It maintains the simplicity of the existing code while improving diagnostics
2. **Maintainability**: It's easier to maintain and understand
3. **Testability**: It's more straightforward to test
4. **Sufficient Improvement**: It provides significantly better diagnostics than the current implementation

While the more sophisticated options offer additional capabilities, the simple approach strikes the right balance between improvement and complexity for this enhancement.

## Implementation Guidelines

### Exception Hierarchy

The requests library has the following exception hierarchy:

```
RequestException
├── HTTPError
├── ConnectionError
│   ├── ProxyError
│   └── SSLError
├── Timeout
│   ├── ConnectTimeout
│   └── ReadTimeout
├── URLRequired
└── TooManyRedirects
```

The implementation should respect this hierarchy, catching more specific exceptions before their parent classes.

### Logging Best Practices

1. Include exception details in log messages
2. Use appropriate log levels:
   - ERROR: For all API failures
   - WARNING: For entering/exiting failure mode
   - INFO: For state transitions
   - DEBUG: For detailed diagnostics
3. Include context in log messages
4. For unexpected exceptions, log the full traceback

### Code Implementation

```python
try:
    # Build the Vimeo API request URL
    stream_url = f"https://api.vimeo.com/me/live_events/{stream_id}/m3u8_playback"

    # Request JSON data
    response = client.get(stream_url)
    response_data = response.json()
    
    # Add debug logging for the API response
    logging.debug("Vimeo API Response: %s", response_data)
    
    # If we get here, the API request was successful
    handle_api_success()
    
except requests.exceptions.ConnectionError as e:
    logging.error("Network connection error: %s", str(e))
    handle_api_failure("connection", str(e))
    
except requests.exceptions.Timeout as e:
    logging.error("Request timeout: %s", str(e))
    handle_api_failure("timeout", str(e))
    
except requests.exceptions.HTTPError as e:
    status_code = e.response.status_code if hasattr(e, 'response') else "unknown"
    logging.error("HTTP error %s: %s", status_code, str(e))
    handle_api_failure(f"http_{status_code}", str(e))
    
except requests.exceptions.RequestException as e:
    logging.error("Request error: %s", str(e))
    handle_api_failure("request", str(e))
    
except Exception as e:
    logging.error("Unexpected error: %s", str(e))
    logging.exception("Full traceback:")
    handle_api_failure("unexpected", str(e))
```

### Helper Functions

```python
def handle_api_success():
    """Handle successful API responses and track consecutive successes."""
    global api_failure_count, api_success_count, api_failure_mode, api_retry_interval
    
    # Reset failure counter and increment success counter
    api_failure_count = 0
    api_success_count += 1
    
    # If we're in failure mode, check if we should exit
    if api_failure_mode and api_success_count >= API_STABILITY_THRESHOLD:
        logging.info("Exiting API failure mode after %d consecutive successes", 
                   api_success_count)
        api_failure_mode = False
        api_retry_interval = API_MIN_RETRY_INTERVAL  # Reset backoff timer

def handle_api_failure(error_type, error_message):
    """Handle API failures and track consecutive failures."""
    global api_failure_count, api_success_count, api_failure_mode, last_api_error
    
    # Reset success counter and increment failure counter
    api_success_count = 0
    api_failure_count += 1
    last_api_error = error_type
    
    logging.error("API failure (%s): %s. Consecutive failures: %d", 
                 error_type, error_message, api_failure_count)
    
    # Check if we should enter failure mode
    if api_failure_count >= API_FAILURE_THRESHOLD:
        if not api_failure_mode:
            logging.warning("Entering API failure mode after %d consecutive failures", 
                           api_failure_count)
            api_failure_mode = True
```

### Future Enhancement Possibilities

While the simple approach is recommended for the initial implementation, future enhancements could include:

1. Error type-specific recovery strategies (Option 2)
2. Error weighting system (Option 3)
3. Admin notifications for critical errors
4. More sophisticated network diagnostics

These enhancements could be considered after the basic functionality is implemented and tested.

# 🎨🎨🎨 EXITING CREATIVE PHASE
