# Vimeo Monitor Project Brief

## PROJECT OVERVIEW

**Project Name**: Vimeo Monitor Refactoring  
**Project Type**: System Refactoring & Modernization  
**Duration**: 4 weeks  
**Approach**: Incremental refactoring with testing at each phase  
**Risk Level**: Low (incremental approach)

## CURRENT SYSTEM

### What It Does
The Vimeo Monitor is a Python application that:
- Monitors Vimeo live stream events using the Vimeo API
- Retrieves m3u8 stream links for live streams
- Displays full-screen video streams with audio when live
- Shows a static "Off Air" image when streams are not live
- Runs continuously on a Raspberry Pi
- Auto-restarts on stream loss

### Current Architecture
- **Single File**: `streammonitor.py` (120 lines)
- **Monolithic Design**: All functionality in one script
- **Hardcoded Configuration**: API credentials, paths, and settings in source code
- **Basic Logging**: Simple file logging to hardcoded path
- **Limited Error Handling**: Basic try-catch with minimal recovery

### Current Issues
- **Security Risk**: API credentials hardcoded in source code
- **Maintenance Difficulty**: Single monolithic script
- **Configuration Inflexibility**: All settings hardcoded
- **Limited Error Recovery**: Basic error handling
- **Reliability Issues**: Requires daily restarts (unstable)
- **Poor Logging**: No log rotation, hardcoded log path

## PROJECT GOALS

### Primary Goals
1. **Security**: Move API credentials to environment variables
2. **Maintainability**: Break monolithic script into modular components
3. **Configuration**: Externalize all configuration settings
4. **Reliability**: Improve error handling and system stability
5. **Logging**: Implement proper logging with rotation

### Secondary Goals
1. **Documentation**: Create comprehensive documentation
2. **Testing**: Add basic test suite
3. **Deployment**: Create installation and setup scripts
4. **Monitoring**: Add basic health monitoring

## TARGET ARCHITECTURE

### Modular Design
```
main.py (Orchestrator)
├── config.py (Configuration Management)
├── logger.py (Logging & Rotation)
├── process_manager.py (Subprocess Management)
└── monitor.py (Core Monitoring Logic)
```

### Key Improvements
- **Security**: Environment variable configuration
- **Modularity**: Clear separation of concerns
- **Maintainability**: Easy to modify and extend
- **Reliability**: Better error handling and recovery
- **Logging**: Structured logging with rotation
- **Configuration**: Externalized and validated settings

## IMPLEMENTATION APPROACH

### Incremental Refactoring
- **Phase 1**: Security & Logging (Week 1)
- **Phase 2**: Modularization (Week 2)
- **Phase 3**: Enhancement (Week 3)
- **Phase 4**: Production Hardening (Week 4)

### Risk Mitigation
- **Small Steps**: Each phase is small and testable
- **Incremental Testing**: Test at each phase
- **Rollback Capability**: Easy to revert changes
- **Functionality Preservation**: Maintain all existing features

## TECHNICAL REQUIREMENTS

### Environment
- **Platform**: Raspberry Pi (Linux ARM)
- **Python**: 3.12+
- **Dependencies**: pyvimeo, VLC, FFmpeg
- **New Dependencies**: python-dotenv (minimal)

### Configuration
- **Environment Variables**: All credentials and settings
- **Validation**: Configuration validation and error handling
- **Documentation**: Clear configuration guide

### Logging
- **Rotation**: Daily rotation, keep 7 days
- **Structured**: Consistent log format
- **Levels**: Configurable log levels
- **Management**: Automatic log cleanup

## SUCCESS CRITERIA

### Phase 1 Success
- [ ] No hardcoded credentials in source code
- [ ] Log files rotate automatically
- [ ] System maintains all existing functionality
- [ ] Configuration is externalized and validated

### Phase 2 Success
- [ ] All hardcoded paths moved to environment variables
- [ ] Process management is modular and reusable
- [ ] Configuration validation prevents runtime errors
- [ ] System maintains stability with new process management

### Phase 3 Success
- [ ] Monitoring logic is modular and testable
- [ ] Main script is simple and focused
- [ ] Error handling is comprehensive
- [ ] System is more reliable and maintainable

### Phase 4 Success
- [ ] System is production-ready
- [ ] Comprehensive error recovery
- [ ] Complete documentation
- [ ] Automated testing
- [ ] Easy installation and setup

## CONSTRAINTS & ASSUMPTIONS

### Constraints
- **Production System**: Must maintain functionality throughout refactoring
- **Platform**: Must work on existing Raspberry Pi setup
- **Dependencies**: Minimize new dependencies
- **Time**: 4-week timeline
- **Risk**: Low risk approach required

### Assumptions
- **Vimeo API**: API remains stable and compatible
- **VLC/FFmpeg**: Media players remain available and compatible
- **System Access**: Full access to system for configuration changes
- **Testing**: Can test changes in development environment

## STAKEHOLDERS

### Primary Stakeholders
- **System Administrator**: Manages the Raspberry Pi system
- **End Users**: Viewers of the live streams
- **Developers**: Future maintenance and development

### Success Metrics
- **System Uptime**: Improved reliability and stability
- **Maintenance Time**: Reduced time for configuration changes
- **Security**: Eliminated hardcoded credentials
- **Documentation**: Complete setup and troubleshooting guides

## RISK ASSESSMENT

### Technical Risks
- **API Changes**: Vimeo API changes could break functionality
- **Dependency Issues**: New dependencies could cause conflicts
- **Performance Impact**: Refactoring could affect performance
- **Compatibility**: Changes might not work on target platform

### Process Risks
- **Scope Creep**: Adding features beyond core requirements
- **Testing Gaps**: Insufficient testing could introduce bugs
- **Documentation**: Incomplete documentation could cause issues
- **Rollback**: Difficulty reverting changes if problems arise

### Mitigation Strategies
- **Incremental Changes**: Small, testable changes
- **Comprehensive Testing**: Test at each phase
- **Documentation**: Document all changes
- **Monitoring**: Monitor system health throughout
- **Rollback Plan**: Maintain ability to revert changes

## DELIVERABLES

### Phase 1 Deliverables
- `.env` file with all credentials and configuration
- `config.py` module with environment variable management
- `logger.py` module with log rotation
- Updated main script using new modules
- Basic test of new configuration system

### Phase 2 Deliverables
- `process_manager.py` module with enhanced subprocess handling
- Enhanced `config.py` with validation and all externalized settings
- Updated main script using process manager
- Configuration validation and error handling

### Phase 3 Deliverables
- `monitor.py` module with core monitoring logic
- Refactored `main.py` as simple orchestrator
- Enhanced error handling throughout system
- Graceful shutdown and signal handling

### Phase 4 Deliverables
- Auto-recovery mechanisms
- Health monitoring system
- Comprehensive documentation
- Test suite with good coverage
- Installation and setup scripts

## TIMELINE

| Week | Phase | Focus | Key Deliverables |
|------|-------|-------|------------------|
| 1 | Foundation | Security & Logging | .env, config.py, logger.py |
| 2 | Modularization | Process Management | process_manager.py, enhanced config |
| 3 | Enhancement | Monitoring Logic | monitor.py, refactored main.py |
| 4 | Hardening | Production Ready | Auto-recovery, docs, tests |

## NEXT STEPS

1. **Begin Phase 1**: Start with environment configuration
2. **Set up testing**: Create test environment
3. **Document progress**: Track implementation progress
4. **Monitor system**: Ensure stability throughout changes
5. **Prepare for Phase 2**: Plan process management extraction

---

**Status**: Project brief complete  
**Next Action**: Begin Phase 1 implementation  
**Priority**: High - Start with environment configuration
