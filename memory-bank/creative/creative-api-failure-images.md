# 🎨🎨🎨 ENTERING CREATIVE PHASE: UI/UX DESIGN

# API Failure Image Display - Design Considerations

## Component Description

This component handles the visual display of error states when the Vimeo API is experiencing issues. It provides clear visual feedback to viewers about the current system state and expected behavior.

## Requirements & User Needs

### Functional Requirements

1. Display a distinct failure image when API failures are detected
2. Transition smoothly between states (stream → no stream → API failure)
3. Support configuration of custom failure images
4. Maintain backward compatibility with existing configurations

### User Needs

1. **Viewers**: Need to understand that the system is experiencing temporary issues
2. **Administrators**: Need to quickly identify the current system state for troubleshooting
3. **Content Providers**: Need assurance that viewers are being properly informed of issues

## Design Options Analysis

### Option 1: Basic Failure Image

#### Description

A simple static image with text indicating API issues. This is the simplest approach and requires minimal changes to the existing code.

#### Visual Mockup

```
┌───────────────────────────────────────┐
│                                       │
│                                       │
│                                       │
│              VIMEO API                │
│          TEMPORARILY OFFLINE          │
│                                       │
│         Please stand by...            │
│                                       │
│                                       │
└───────────────────────────────────────┘
```

#### Implementation

```python
# Using existing ffplay infrastructure
failure_image_command = [
    "ffplay",
    "-fs",
    "-loop", "1",  # loop the image indefinitely
    API_FAIL_IMAGE_PATH
]
current_process = subprocess.Popen(failure_image_command)
```

#### Pros

- Simple implementation
- Consistent with existing code patterns
- Low resource usage
- Easy to customize by changing image file

#### Cons

- Static display with no dynamic information
- No visual indication of reconnection attempts
- Limited diagnostics for troubleshooting

### Option 2: Enhanced Failure Image with Status Information

#### Description

An enhanced image display that includes basic status information such as error type, time of failure, and reconnection status.

#### Visual Mockup

```
┌───────────────────────────────────────┐
│                                       │
│                                       │
│              VIMEO API                │
│          TEMPORARILY OFFLINE          │
│                                       │
│         Please stand by...            │
│                                       │
│ Error: Network Connection             │
│ Next retry in: 40 seconds             │
└───────────────────────────────────────┘
```

#### Implementation

This would require a more complex implementation:

```python
def create_status_image(error_type, retry_seconds):
    # Create a temporary image with status information
    # Using PIL or similar library
    # Return path to temporary image
    
# In the main loop:
if new_mode == "api_failure":
    status_image = create_status_image(last_error_type, api_retry_interval)
    failure_image_command = [
        "ffplay",
        "-fs",
        "-loop", "1",
        status_image
    ]
    current_process = subprocess.Popen(failure_image_command)
```

#### Pros

- More informative for users and administrators
- Shows active recovery attempts
- Provides diagnostic information

#### Cons

- Significantly more complex implementation
- Requires additional dependencies (PIL or similar)
- More resource intensive
- More difficult to test

### Option 3: HTML-Based Status Display

#### Description

Use a local HTML file with CSS/JavaScript to display a more dynamic and informative error state.

#### Visual Mockup

```
┌───────────────────────────────────────┐
│                                       │
│           ⚠️ VIMEO API ⚠️             │
│          TEMPORARILY OFFLINE          │
│                                       │
│         Please stand by...            │
│                                       │
│ [███████████▒▒▒▒▒▒▒] Reconnecting...  │
│                                       │
│ Status: Attempting to reconnect       │
└───────────────────────────────────────┘
```

#### Implementation

```python
def generate_html_status(error_type, retry_seconds):
    # Generate HTML with current status
    html_content = f"""
    <html>
    <head>
        <style>/* CSS styles */</style>
    </head>
    <body>
        <div class="error-container">
            <h1>⚠️ VIMEO API ⚠️</h1>
            <h2>TEMPORARILY OFFLINE</h2>
            <p>Please stand by...</p>
            <div class="progress-bar">
                <!-- Progress bar styling -->
            </div>
            <p>Status: Attempting to reconnect</p>
            <p>Error: {error_type}</p>
            <p>Next retry in: {retry_seconds} seconds</p>
        </div>
    </body>
    </html>
    """
    # Write to temporary file
    # Return path to file

# In main loop:
if new_mode == "api_failure":
    html_path = generate_html_status(last_error_type, api_retry_interval)
    failure_display_command = [
        "chromium-browser",  # or other browser
        "--kiosk",  # fullscreen mode
        f"file://{html_path}"
    ]
    current_process = subprocess.Popen(failure_display_command)
```

#### Pros

- Most informative and visually appealing
- Can include dynamic updates
- Best user experience
- Most diagnostic information

#### Cons

- Completely different approach from current implementation
- Requires browser installation
- Most complex implementation
- Highest resource usage
- Most dependencies

## Recommended Approach

### Option 1: Basic Failure Image

For the vimeo-monitor application, the basic failure image approach (Option 1) is recommended for the following reasons:

1. **Consistency**: Maintains consistency with the existing implementation
2. **Simplicity**: Requires minimal code changes
3. **Reliability**: Fewer dependencies and less complexity means fewer potential issues
4. **Customizability**: Administrators can still create custom informative images

While the enhanced options would provide more information, they introduce significantly more complexity and dependencies. For a system that prioritizes reliability and simplicity, the basic approach is most appropriate.

## Implementation Guidelines

### Image Design Recommendations

1. **High Contrast**: Use high contrast colors for visibility
2. **Clear Typography**: Use large, readable fonts
3. **Simple Message**: Keep the message clear and concise
4. **Branding Consistency**: Maintain consistent branding with other aspects of the application
5. **Neutral Tone**: Avoid alarming language, focus on the temporary nature of the issue

### Sample Image Content

```
┌───────────────────────────────────────┐
│                                       │
│                                       │
│            [Company Logo]             │
│                                       │
│              VIMEO STREAM             │
│          TEMPORARILY UNAVAILABLE      │
│                                       │
│      The stream will resume when      │
│        service is restored.           │
│                                       │
└───────────────────────────────────────┘
```

### Configuration

1. Set a default path for the API failure image
2. Allow customization via environment variable
3. Fall back to the holding image if the failure image is not found

### Code Implementation

```python
# In environment setup:
API_FAIL_IMAGE_PATH = os.getenv("API_FAIL_IMAGE_PATH")

# In mode selection:
if api_failure_mode:
    new_mode = "api_failure"
elif "m3u8_playback_url" in response_data:
    new_mode = "stream"
else:
    new_mode = "image"

# In display logic:
if new_mode == "api_failure":
    # Check if failure image exists
    if API_FAIL_IMAGE_PATH and os.path.exists(API_FAIL_IMAGE_PATH):
        image_path = API_FAIL_IMAGE_PATH
    else:
        # Fall back to holding image
        logging.warning("API failure image not found, using holding image instead")
        image_path = HOLDING_IMAGE_PATH
        
    logging.warning("API instability detected. Displaying failure image.")
    failure_image_command = [
        "ffplay",
        "-fs",
        "-loop", "1",  # loop the image indefinitely
        image_path
    ]
    logging.info("Executing command for API failure image: %s", " ".join(failure_image_command))
    current_process = subprocess.Popen(failure_image_command)
```

### Future Enhancement Possibilities

While the basic approach is recommended for the initial implementation, future enhancements could include:

1. Simple status overlay on top of the failure image
2. Periodic refresh of the image to show updated information
3. Integration with the network status display feature (planned enhancement)

These enhancements could be considered after the basic functionality is implemented and tested.

# 🎨🎨🎨 EXITING CREATIVE PHASE
