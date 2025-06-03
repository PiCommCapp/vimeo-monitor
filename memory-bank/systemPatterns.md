# System Patterns

## Architectural Patterns

### Polling Pattern

The application uses a continuous polling pattern to check the Vimeo API status at regular intervals. This pattern is chosen for simplicity and reliability, rather than a more complex event-driven approach that might be less stable in this environment.

### Watchdog Pattern

The application implements a watchdog pattern to monitor for stalled processes or unexpected failures, automatically restarting components when necessary. This enhances resilience and self-healing capabilities.

### State Machine

The application follows a simple state machine pattern with two primary states:

1. **Stream Mode**: Active when a valid Vimeo stream is available
2. **Image Mode**: Active when no stream is available or during API failures

## Code Organization

### Single Responsibility Modules

Each Python module has a clearly defined responsibility:

- `monitor.py`: Main application logic for polling and state management
- `__main__.py`: Entry point for the application
- Environment configuration handled separately via `.env` file

### Process Management

The application uses subprocess management to control media player processes:

- Launches media players as separate processes
- Monitors subprocess state
- Kills and restarts processes as needed when state changes

## Error Handling

### Graceful Degradation

The system follows a graceful degradation pattern:

1. Attempt to play live stream (optimal experience)
2. Fall back to holding image if stream unavailable (acceptable experience)
3. Fall back to failure image if API unavailable (minimal acceptable experience)

### Comprehensive Logging

Structured logging patterns are used throughout the application to:

- Track state changes
- Record errors with appropriate detail
- Provide debugging information when needed

## Configuration Management

### Environment-Based Configuration

All configuration is externalized via environment variables, following the 12-factor app methodology for configuration. This separates code from configuration for better deployment flexibility.

### Isolated Credentials

Security credentials are kept separate from application code and loaded at runtime.

## Deployment Pattern

### Systemd Service Integration

The application is designed to be deployed as a systemd service, providing:

- Automatic startup on boot
- Restart on failure
- Proper process management
- Environment variable loading

## Future Enhancement Patterns

### Observer Pattern (Potential)

Future enhancements might implement an observer pattern for remote monitoring and diagnostics via MQTT or WebSockets.

### Configuration Synchronization (Potential)

A future enhancement might include a pattern for remote configuration synchronization while maintaining local fallbacks.
