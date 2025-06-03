# Task Tracking

## Current Task

**Task ID**: TASK-001  
**Description**: Improve API Failure Handling  
**Status**: Planning  
**Complexity Level**: Level 2 (Simple Enhancement)

## Task Details

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
- `.env.sample`: Update with new configuration options (see proposed new configuration below)

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

### Progress

- [x] Create enhanced API error detection logic
- [x] Implement cooldown and backoff mechanism
- [x] Add API_FAIL_IMAGE_PATH support
- [x] Add specific handling for different error types
- [x] Restructure code as proper Python module with main() function
- [ ] Write tests for new error handling functionality

## Previous Tasks

### Task ID: N/A - Initial project setup  

**Description**: Initial Memory Bank setup and project analysis  
**Status**: Completed  
**Complexity Level**: N/A (Memory Bank Initialization)

**Progress**:

- [x] Created Memory Bank directory structure
- [x] Documented project brief
- [x] Documented technical context
- [x] Documented product context
- [x] Documented system patterns
- [x] Documented active context
- [x] Documented progress status
- [x] Perform analysis of code for potential improvements
- [x] Identify specific enhancement tasks

### Code Analysis Findings

1. **API Error Handling**
   - Current implementation has basic error handling for RequestException
   - Could benefit from more specific error handling and recovery strategies
   - No clear distinction between temporary API failures and prolonged outages

2. **Media Player Management**
   - Uses subprocess to launch media players (ffplay, cvlc)
   - Basic process monitoring with poll() check
   - Could benefit from more robust process management and health checks

3. **Configuration**
   - Uses environment variables directly with os.getenv()
   - No validation or default values for configuration
   - No centralized configuration management

4. **Logging**
   - Basic logging setup with file and console handlers
   - No log rotation mechanism
   - Could benefit from more structured logging

5. **Code Structure**
   - Simple procedural code in monitor.py
   - Limited modularity and separation of concerns
   - Could benefit from more object-oriented approach for better testability

## Pending Tasks

### Potential Enhancement Tasks

1. ~~**Improve API Failure Handling**~~ (SELECTED: TASK-001)
   - Add more sophisticated detection of unstable API responses
   - Implement cooldown period before attempting reconnection
   - Add proper API failure image display
   - Add specific error handling for different API failure modes

2. **Add Network Status Display** (TASK-002)
   - Implement configurable on-screen network status indicator
   - Show connection status and stream health
   - Add option to toggle visibility

3. **Implement Log Rotation** (TASK-003)
   - Add log rotation mechanism to prevent disk space issues
   - Maintain reasonable log history
   - Configure rotation parameters (size, count, compression)

4. ~~**Create GUI Settings Panel**~~ **Create TUI Settings Panel for SSH with Whiptail** (TASK-004)
   - Develop simple Tk or PyQT interface for configuration
   - Allow runtime configuration changes
   - Provide status monitoring

5. ~~**Add HDMI CEC Integration**~~
   - Implement display power control via HDMI CEC
   - Power on/off display based on schedule or status
   - Handle display sleep during inactive periods

6. **Develop Remote Diagnostics** (TASK-006)
   - Implement Prometheus-compatible `/metrics` HTTP endpoint
   - Expose system health metrics (API state, uptime, failures)
   - Allow integration with standard monitoring tools
   - Provide real-time status information

7. **Refactor Code Structure** (TASK-007)
   - Implement object-oriented design for better modularity
   - Create separate classes for API client, media player, and monitoring
   - Improve testability with dependency injection

8. **Enhance Configuration Management** (TASK-008)
   - Create centralized configuration with validation
   - Add support for configuration file in addition to environment variables
   - Implement configuration reload without restart

## Notes

The project appears to be functional but could benefit from several enhancements to improve reliability, monitoring, and ease of configuration. Initial analysis suggests the core architecture is sound, but there are opportunities to add features that would make deployment and maintenance easier.

## Task Prioritization

Tasks have been prioritized based on impact and effort:

1. **TASK-001**: Improve API Failure Handling (HIGH PRIORITY)
   - Directly addresses core reliability issues
   - Relatively straightforward implementation
   - Significant impact on user experience

2. **TASK-003**: Implement Log Rotation
   - Important for long-term stability
   - Moderate implementation complexity

3. **TASK-008**: Enhance Configuration Management
   - Improves deployment and maintenance experience
   - Foundation for other enhancements

4. **TASK-002**: Add Network Status Display
   - Provides valuable user feedback
   - Depends on stable API handling

5. **TASK-007**: Refactor Code Structure
   - Improves maintainability
   - Foundation for more complex features

6. **TASK-004**: Create GUI Settings Panel
   - Improves admin experience
   - Higher complexity, lower immediate impact

7. **TASK-006**: Develop Remote Diagnostics
   - Valuable for remote management
   - Higher complexity, special requirements

8. **TASK-005**: Add HDMI CEC Integration
   - Nice-to-have feature
   - Requires specific hardware testing
