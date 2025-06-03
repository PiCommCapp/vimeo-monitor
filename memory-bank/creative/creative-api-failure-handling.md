# Creative Phase: API Failure Handling Enhancement

## Design Considerations

### Error Detection Philosophy

The enhanced error detection system should balance between two competing goals:

1. **Responsiveness**: Quickly detecting and responding to actual API failures
2. **Stability**: Avoiding unnecessary mode switches due to transient issues

To achieve this balance, the design follows these principles:

- Use a counter-based approach rather than immediate mode switches
- Track different types of errors separately for better diagnostics
- Implement configurable thresholds for entering/exiting failure mode
- Use exponential backoff to reduce API hammering during issues

### State Management Design

The application should maintain a clear separation between three distinct states:

1. **Stream Mode**: The optimal state - showing the live stream from Vimeo
2. **No Stream Mode**: The standard fallback - showing the holding image when a stream isn't available
3. **API Failure Mode**: The new error state - showing a specific failure image when the API is unstable

The state transitions should follow this flow:

```
                 ┌───────────────────┐
                 │                   │
                 ▼                   │
  ┌──────────┐      ┌───────────┐      ┌──────────────┐
  │  Stream  │─────▶│ No Stream │─────▶│ API Failure  │
  │   Mode   │◀─────│    Mode   │◀─────│     Mode     │
  └──────────┘      └───────────┘      └──────────────┘
       ▲                                      │
       │                                      │
       └──────────────────────────────────────┘
```

### Cooldown Mechanism Design

The cooldown mechanism uses exponential backoff to avoid hammering the API during failures:

- Initial retry interval: 10 seconds
- Each failure doubles the interval up to a maximum of 5 minutes
- After successful reconnection, reset to the initial interval

```
                          Max: 5 min
                             ┌───
                             │
Retry     ┌───┬───┬───┬───┬─┘
Interval  │   │   │   │   │
          │   │   │   │   │
          └───┴───┴───┴───┘
          10s  20s  40s  80s ...
          
            Consecutive Failures
```

### Error Categorization

The application will categorize errors into distinct types for better diagnostics and potential differentiated handling:

1. **Network Errors**: Connection issues, DNS problems, etc.
2. **API Errors**: Server-side issues, rate limiting, etc.
3. **Authentication Errors**: Invalid credentials, expired tokens, etc.
4. **Unexpected Errors**: Any other unhandled exceptions

### Visual Distinction

Each state should be visually distinct to aid in troubleshooting:

1. **Stream Mode**: The live video stream (full motion)
2. **No Stream Mode**: The holding image (static, professional-looking)
3. **API Failure Mode**: The failure image (visually distinct from holding image)

The failure image should include minimal diagnostic information without exposing sensitive details.

## Design Decisions

1. **Counter-Based Transition**: Use consecutive failure/success counters rather than time-based detection
   - **Rationale**: More predictable behavior and simpler to implement/test
   - **Alternative**: Time window-based detection (e.g., "3 failures in 5 minutes")

2. **Global State Variables**: Use global variables for state tracking
   - **Rationale**: Matches existing code pattern and simplicity
   - **Alternative**: Class-based implementation with proper encapsulation

3. **Exponential Backoff**: Implement exponential backoff with configurable parameters
   - **Rationale**: Industry standard approach for handling temporary failures
   - **Alternative**: Fixed retry interval or random jitter

4. **Specific Exception Handling**: Catch and handle specific exception types
   - **Rationale**: Provides better diagnostics and potential for specific responses
   - **Alternative**: Generic exception handling

5. **Environment Configuration**: Use environment variables for all parameters
   - **Rationale**: Consistent with existing code and allows for deployment-specific tuning
   - **Alternative**: Configuration file or hardcoded defaults

## Visual Mockups

### Normal State Flow

```
┌───────────────────────────────────────┐
│                                       │
│                                       │
│                                       │
│                                       │
│             LIVE STREAM               │
│                                       │
│                                       │
│                                       │
│                                       │
└───────────────────────────────────────┘
              Stream Mode

┌───────────────────────────────────────┐
│                                       │
│                                       │
│                                       │
│                                       │
│            HOLDING IMAGE              │
│                                       │
│                                       │
│                                       │
│                                       │
└───────────────────────────────────────┘
           No Stream Mode
```

### Failure State

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
           API Failure Mode
```

## Technical Implementation Notes

1. Use helper functions to separate concerns:
   - Error detection logic
   - State transition logic
   - Retry interval calculation

2. Add comprehensive logging at each stage:
   - Log all API responses at DEBUG level
   - Log state transitions at INFO level
   - Log errors with full context at ERROR level

3. Ensure backwards compatibility:
   - Provide sensible defaults for all new configuration options
   - Gracefully handle missing failure image

4. Consider future enhancements:
   - Status overlay could show reconnection progress
   - Different failure images for different error types
   - Remote monitoring of failure states
