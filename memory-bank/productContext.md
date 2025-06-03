# Product Context

## Purpose

The vimeo-monitor is a self-contained video kiosk solution designed to display an HLS livestream from Vimeo in public or semi-public settings. It provides a robust, self-healing system that can reliably display video content with minimal maintenance requirements.

## Target Usage Scenarios

- **Digital Signage**: Displaying live video feeds in retail or corporate environments
- **Event Displays**: Showing live event streams in satellite locations
- **Information Kiosks**: Providing live video information in public spaces
- **Monitoring Stations**: Displaying live feeds that need to be visually monitored
- **Remote Viewing**: Allowing remote audiences to view live streams in dedicated spaces

## User Types

1. **End Users**: People viewing the display (passive interaction only)
2. **System Administrators**: IT personnel who configure and maintain the system
3. **Content Providers**: Teams that manage the Vimeo live stream content

## Key Product Requirements

- **Reliability**: Must operate 24/7 with minimal downtime or manual intervention
- **Resilience**: Must recover automatically from network issues, API failures, or stream interruptions
- **Simplicity**: Minimal configuration required for deployment
- **Visibility**: Clear status indicators for system health (optional overlay)
- **Maintainability**: Simple update mechanism and logging

## Success Metrics

- **Uptime**: 99.9% display availability (stream or fallback image)
- **Recovery Time**: Self-recovery within 15 seconds of any failure
- **Configuration Effort**: Less than 10 minutes to configure for new deployments
- **Update Process**: Updates completed in under 5 minutes

## Current Limitations

- Limited to Vimeo as the streaming source
- Requires a persistent display connection
- No touch/interactive capabilities
- Requires Raspberry Pi hardware specifically
- No remote management interface beyond SSH

## Future Product Direction

Based on the project brief, potential future enhancements include:

- Remote configuration management
- GUI-based settings interface
- Integration with HDMI-CEC for display control
- Remote diagnostics and monitoring via MQTT or WebSockets
- Log rotation for long-term deployments
- Multi-source support beyond Vimeo

## Deployment Context

The product is designed for:

- Fixed-location installations
- Continuous operation
- Headless (no keyboard/mouse) usage after initial setup
- Environments with reliable power and network connectivity
