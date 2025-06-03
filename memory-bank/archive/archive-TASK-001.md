# Archive: TASK-001 - Improve API Failure Handling

## Task Information

**Task ID**: TASK-001  
**Description**: Improve API Failure Handling  
**Status**: Planning Completed  
**Complexity Level**: Level 2 (Simple Enhancement)
**Creation Date**: June 3, 2024
**Planning Date**: June 3, 2024
**Implementation Date**: Pending

## Task Summary

Enhance the vimeo-monitor application's API failure handling mechanism to improve reliability and user experience. The improvements include sophisticated error detection, exponential backoff for reconnection attempts, proper failure image display, and specific handling for different error types.

## Planning Documentation

### Objectives

- Enhance the API failure detection mechanism
- Implement cooldown period before reconnection attempts
- Add proper API failure image display with separate path
- Create specific error handling for different API failure modes

### Implementation Plan

#### 1. Enhanced API Error Detection

- Create an API failure counter to track consecutive failures
- Implement detection for different error types:
  - Network errors (connection issues)
  - API errors (server-side problems)
  - Authentication errors (credentials issues)
  - Rate limiting errors (too many requests)
- Add a state tracking mechanism to detect rapid state changes (instability)

**Code Implementation:**

```python
# New global variables for API failure tracking
api_failure_count = 0
api_success_count = 0
api_failure_mode = False
last_api_error = None
api_retry_interval = int(os.getenv("API_MIN_RETRY_INTERVAL", 10))

# Constants from environment
API_FAILURE_THRESHOLD = int(os.getenv("API_FAILURE_THRESHOLD", 3))
API_STABILITY_THRESHOLD = int(os.getenv("API_STABILITY_THRESHOLD", 5))
API_MIN_RETRY_INTERVAL = int(os.getenv("API_MIN_RETRY_INTERVAL", 10))
API_MAX_RETRY_INTERVAL = int(os.getenv("API_MAX_RETRY_INTERVAL", 300))
API_ENABLE_BACKOFF = os.getenv("API_ENABLE_BACKOFF", "true").lower() == "true"
```

#### 2. Cooldown Mechanism

- Implement exponential backoff for reconnection attempts
- Start with a 10-second retry, doubling up to a maximum of 5 minutes
- Reset backoff timer when a successful connection is established
- Add a stability counter to ensure API is stable before switching back to stream mode

**Code Implementation:**

```python
def calculate_backoff(current_interval):
    """Calculate the next retry interval using exponential backoff."""
    if not API_ENABLE_BACKOFF:
        return API_MIN_RETRY_INTERVAL
        
    # Double the current interval
    next_interval = current_interval * 2
    
    # Cap at maximum
    return min(next_interval, API_MAX_RETRY_INTERVAL)

# In the main loop, after catching an exception:
if api_failure_mode:
    # We're already in failure mode, use the backoff timer
    logging.info("In API failure mode. Waiting %d seconds before retry...", api_retry_interval)
    time.sleep(api_retry_interval)
    
    # Calculate next backoff interval
    api_retry_interval = calculate_backoff(api_retry_interval)
else:
    # Use the regular check interval
    time.sleep(CHECK_INTERVAL)
```

#### 3. API Failure Image Support

- Add support for API_FAIL_IMAGE_PATH in environment configuration
- Create a new state "api_failure" distinct from "image" state
- Update mode selection logic to handle three states:
  - "stream": Valid stream available
  - "image": No stream but API is functioning
  - "api_failure": API is not functioning correctly

**Code Implementation:**

```python
# Define the path to failure image
API_FAIL_IMAGE_PATH = os.getenv("API_FAIL_IMAGE_PATH")

# In the mode selection logic:
if api_failure_mode:
    new_mode = "api_failure"
elif "m3u8_playback_url" in response_data:
    new_mode = "stream"
else:
    new_mode = "image"

# In the process handling section:
if new_mode == "api_failure":
    logging.warning("API instability detected. Displaying failure image.")
    failure_image_command = [
        "ffplay",
        "-fs",
        "-loop", "1",  # loop the image indefinitely
        API_FAIL_IMAGE_PATH
    ]
    logging.info("Executing play command for API failure image: %s", " ".join(failure_image_command))
    current_process = subprocess.Popen(failure_image_command)
elif new_mode == "stream":
    # Existing stream mode code
elif new_mode == "image":
    # Existing image mode code
```

#### 4. Error Handling Implementation

- Refactor the try/except block to handle specific exception types
- Add more detailed logging for each type of failure
- Create helper functions for error handling to improve code readability
- Add configuration option for failure thresholds

**Code Implementation:**

```python
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

# In the main try/except block:
try:
    # Existing API request code...
    
    # If we get here, the API request was successful
    handle_api_success()
    
except requests.exceptions.ConnectionError as e:
    handle_api_failure("connection", str(e))
except requests.exceptions.Timeout as e:
    handle_api_failure("timeout", str(e))
except requests.exceptions.HTTPError as e:
    handle_api_failure("http", str(e))
except requests.exceptions.RequestException as e:
    handle_api_failure("request", str(e))
except Exception as e:
    handle_api_failure("unknown", str(e))
    logging.exception("Unexpected error:")
```

#### 5. Testing

- Create unit tests for new error handling logic
- Test with simulated API failures
- Test stability detection algorithm
- Test proper image switching based on different error conditions

**Test Plan:**

1. Test consecutive API failures trigger failure mode
2. Test consecutive successes exit failure mode
3. Test proper display of API failure image
4. Test exponential backoff mechanism
5. Test detection of different error types

### Files to Modify

- `vimeo_monitor/monitor.py`: Main application logic
- `.env.sample`: Update with new configuration options

**Proposed .env.sample additions:**

```
# API failure handling configuration
API_FAILURE_THRESHOLD=3 # Number of consecutive failures before entering failure mode
API_STABILITY_THRESHOLD=5 # Number of consecutive successes before exiting failure mode
API_MIN_RETRY_INTERVAL=10 # Minimum retry interval in seconds
API_MAX_RETRY_INTERVAL=300 # Maximum retry interval in seconds
API_ENABLE_BACKOFF=true # Enable exponential backoff for retry intervals
```

### Potential Challenges

- Distinguishing between temporary and persistent API failures
- Avoiding false positives in instability detection
- Ensuring smooth transitions between states
- Maintaining backwards compatibility with existing configurations

## Next Steps

1. Review and finalize implementation plan
2. Begin implementation phase
3. Create unit tests for the new functionality
4. Document changes for users and administrators
