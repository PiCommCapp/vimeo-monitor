# 🎨🎨🎨 ENTERING CREATIVE PHASE: ALGORITHM DESIGN

# API Failure Handling - Design Options Analysis

## Component Description

The API Failure Handling component is responsible for detecting and responding to Vimeo API failures in a robust and user-friendly manner. This component will enhance the current error handling mechanism by adding sophisticated detection, exponential backoff, proper failure image display, and specific handling for different error types.

## Requirements & Constraints

### Functional Requirements

1. Detect persistent API failures reliably
2. Implement reconnection strategy with exponential backoff
3. Display appropriate failure image when API is unavailable
4. Handle different types of API errors appropriately
5. Maintain backward compatibility with existing configurations

### Non-Functional Requirements

1. Minimize unnecessary mode switches (stability)
2. Provide detailed logging for troubleshooting
3. Allow configuration of all behavior parameters
4. Maintain simplicity of implementation

### Constraints

1. Must work within existing procedural code structure
2. Must maintain compatibility with existing configuration
3. Limited ability to test with actual API failures
4. Must handle a variety of error conditions reliably

## Design Options Analysis

### Option 1: Counter-Based Failure Detection

#### Description

Track consecutive failures and successes using counters. Enter failure mode when failures exceed a threshold and exit when successes exceed another threshold.

#### Code Structure

```python
# State tracking variables
api_failure_count = 0
api_success_count = 0
api_failure_mode = False

# Main loop with try/except
try:
    # API request
    # If successful:
    api_failure_count = 0
    api_success_count += 1
    if api_failure_mode and api_success_count >= STABILITY_THRESHOLD:
        exit_failure_mode()
except Exception:
    api_success_count = 0
    api_failure_count += 1
    if api_failure_count >= FAILURE_THRESHOLD:
        enter_failure_mode()
```

#### Pros

- Simple to implement and understand
- Predictable behavior
- Low computational overhead
- Easy to test
- Configurable thresholds

#### Cons

- Does not consider time between failures
- Could result in mode flapping in unstable conditions
- All errors treated equally regardless of type

### Option 2: Time-Window Based Detection

#### Description

Track failures within a sliding time window. Enter failure mode when failures within the window exceed a threshold.

#### Code Structure

```python
# State tracking variables
failure_timestamps = []  # List of timestamps of recent failures
api_failure_mode = False
WINDOW_SIZE = 300  # 5 minutes in seconds

# Main loop with try/except
try:
    # API request
    # If successful:
    if api_failure_mode:
        check_exit_failure_mode()
except Exception:
    # Record failure timestamp
    now = time.time()
    failure_timestamps.append(now)
    
    # Remove old timestamps outside window
    failure_timestamps = [t for t in failure_timestamps 
                         if now - t <= WINDOW_SIZE]
    
    # Check if failures in window exceed threshold
    if len(failure_timestamps) >= FAILURE_THRESHOLD:
        enter_failure_mode()
```

#### Pros

- Considers time between failures
- More sophisticated detection of persistent issues
- Automatically "forgets" old failures
- Less likely to false-trigger on occasional failures

#### Cons

- More complex implementation
- Higher memory usage
- More difficult to test
- Less predictable behavior

### Option 3: Hybrid Approach with Error Type Weighting

#### Description

Combine counter-based tracking with time awareness and error type weighting. Different error types have different weights toward failure mode.

#### Code Structure

```python
# State tracking variables
api_failure_count = 0
api_success_count = 0
api_failure_mode = False
error_weights = {
    "connection": 1.0,
    "timeout": 0.5,
    "http": 1.5,
    "auth": 2.0,
    "unknown": 1.0
}

# Main loop with try/except
try:
    # API request
    # If successful:
    handle_api_success()
except ConnectionError:
    handle_api_failure("connection")
except TimeoutError:
    handle_api_failure("timeout")
# etc.

def handle_api_failure(error_type):
    global api_failure_count
    weight = error_weights.get(error_type, 1.0)
    api_failure_count += weight
    
    if api_failure_count >= FAILURE_THRESHOLD:
        enter_failure_mode()
```

#### Pros

- Differentiates between error types
- More nuanced failure detection
- Can prioritize critical errors
- Flexible configuration

#### Cons

- Most complex implementation
- Requires tuning of weights
- Most difficult to test
- May be overkill for the current use case

## Recommended Approach

### Option 1: Counter-Based Failure Detection

For the vimeo-monitor application, the counter-based approach (Option 1) is recommended for the following reasons:

1. **Simplicity**: It aligns with the existing codebase's procedural style
2. **Predictability**: Behavior is easy to understand and debug
3. **Configurability**: Thresholds can be easily adjusted via environment variables
4. **Testability**: Straightforward to write unit tests for

The counter-based approach provides a good balance between reliability and implementation complexity. It addresses the core requirements while maintaining code simplicity and predictability.

## Implementation Guidelines

### State Management

1. Use global variables for state tracking to match existing code patterns
2. Create helper functions for state transitions to improve readability
3. Add comprehensive logging at each state change

### Exponential Backoff

1. Implement simple doubling backoff with configurable min/max
2. Reset backoff timer on successful API calls
3. Apply backoff only in failure mode

### Error Handling

1. Use specific exception types for better diagnostics
2. Implement helper functions for error handling
3. Add detailed logging for each error type

### Configuration

1. Use environment variables with sensible defaults
2. Document all configuration options
3. Handle missing configuration gracefully

### Testing Strategy

1. Create unit tests for state transitions
2. Implement mocks for API failures
3. Test exponential backoff logic
4. Verify failure image display

## Visual State Flow

```
                    Error Count ≥ Threshold
                    ┌────────────────────┐
                    │                    │
                    ▼                    │
┌──────────┐     ┌───────────┐     ┌────────────┐
│  Stream  │────▶│ No Stream │────▶│ API Failure │
│   Mode   │◀────│    Mode   │◀────│    Mode     │
└──────────┘     └───────────┘     └────────────┘
                    ▲                    │
                    │                    │
                    └────────────────────┘
                    Success Count ≥ Threshold
```

## Code Structure

```python
# Constants (from environment variables with defaults)
API_FAILURE_THRESHOLD = int(os.getenv("API_FAILURE_THRESHOLD", 3))
API_STABILITY_THRESHOLD = int(os.getenv("API_STABILITY_THRESHOLD", 5))
API_MIN_RETRY_INTERVAL = int(os.getenv("API_MIN_RETRY_INTERVAL", 10))
API_MAX_RETRY_INTERVAL = int(os.getenv("API_MAX_RETRY_INTERVAL", 300))
API_ENABLE_BACKOFF = os.getenv("API_ENABLE_BACKOFF", "true").lower() == "true"

# State tracking variables
api_failure_count = 0
api_success_count = 0
api_failure_mode = False
last_error_type = None
api_retry_interval = API_MIN_RETRY_INTERVAL

# Helper functions
def enter_failure_mode():
    global api_failure_mode
    if not api_failure_mode:
        logging.warning("Entering API failure mode after %d consecutive failures", 
                       api_failure_count)
        api_failure_mode = True

def exit_failure_mode():
    global api_failure_mode, api_retry_interval
    logging.info("Exiting API failure mode after %d consecutive successes", 
               api_success_count)
    api_failure_mode = False
    api_retry_interval = API_MIN_RETRY_INTERVAL  # Reset backoff timer

def calculate_backoff(current_interval):
    if not API_ENABLE_BACKOFF:
        return API_MIN_RETRY_INTERVAL
    next_interval = current_interval * 2
    return min(next_interval, API_MAX_RETRY_INTERVAL)

def handle_api_success():
    global api_failure_count, api_success_count
    api_failure_count = 0
    api_success_count += 1
    if api_failure_mode and api_success_count >= API_STABILITY_THRESHOLD:
        exit_failure_mode()

def handle_api_failure(error_type, error_message):
    global api_failure_count, api_success_count, last_error_type
    api_success_count = 0
    api_failure_count += 1
    last_error_type = error_type
    
    logging.error("API failure (%s): %s. Consecutive failures: %d", 
                 error_type, error_message, api_failure_count)
    
    if api_failure_count >= API_FAILURE_THRESHOLD:
        enter_failure_mode()
```

# 🎨🎨🎨 EXITING CREATIVE PHASE
