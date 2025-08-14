# Tasks - Vimeo Monitor Project

## Current Task: Project Initialization

### Status: IN PROGRESS
- **Started**: VAN mode initialization
- **Phase**: Memory Bank setup
- **Priority**: HIGH

### Task Description
Initialize the Memory Bank system and assess the Vimeo Monitor project for proper development workflow setup.

### Completed Steps
- [x] Create Memory Bank directory structure
- [x] Create activeContext.md
- [x] Create progress.md
- [x] Create systemPatterns.md
- [x] Create techContext.md
- [x] Create productContext.md
- [x] Create tasks.md

### Current Step
- [ ] Assess project complexity level
- [ ] Determine appropriate development mode
- [ ] Initialize task tracking for development

### Next Actions
1. Analyze project requirements and scope
2. Determine complexity level (Level 1-4)
3. Set appropriate development mode
4. Create initial development plan

### Notes
- Project involves Python development for Raspberry Pi 5
- Includes API integration, media playback, and system integration
- Requires fault tolerance and monitoring capabilities
- Target: autonomous video kiosk system

## Project Overview
- **Name**: vimeo-monitor
- **Type**: Python-based video kiosk system
- **Platform**: Raspberry Pi 5 with X11
- **Purpose**: Continuous video display with intelligent fallback
- **Status**: Initial development phase

# Task: Vimeo Monitor Core Feature Plan (Level 3)

## Description
Design and implement the core Vimeo livestream monitoring service for Raspberry Pi 5 with robust failover, process self-healing, and a Prometheus `/metrics` endpoint. Includes Vimeo API polling, stream validation via `ffprobe`, fullscreen playback (`cvlc` preferred; fallback `ffplay`/`mpv`), and fallback images when stream/API unavailable.

## Complexity
- Level: 3 (Feature)
- Type: Intermediate Feature spanning multiple components (API, playback, monitoring, metrics)

## Technology Stack
- Language: Python 3.12+
- Runner: `uv`
- Media tools: `ffprobe`, `ffplay`, `cvlc` (preferred), `mpv` (optional)
- Libraries: `pyvimeo`, `requests`, `prometheus-client`, `python-dotenv`, `psutil`, `watchdog`, `pydantic`
- OS: Raspberry Pi OS Desktop (X11)

## Technology Validation Checkpoints
- [ ] Verify `uv run -V` works and Python 3.12+ available
- [ ] Verify `ffprobe -version` present on device
- [ ] Verify at least one player available: `cvlc --version` or `ffplay -version`
- [ ] Minimal POC: spawn player to display local holding image for 3s, then exit
- [ ] Minimal POC: start Prometheus `/metrics` HTTP server and fetch locally
- [ ] pyvimeo import and dummy client instantiation works (env-based tokens only)

## Requirements Analysis
- [ ] Poll Vimeo API at interval to obtain secure HLS URL for selected `VIMEO_VIDEO_ID`
- [ ] Validate stream URL via `ffprobe` before playback
- [ ] Fullscreen playback with audio over HDMI
- [ ] Fallback to `HOLDING_IMAGE_PATH` when no stream
- [ ] Fallback to `API_FAIL_IMAGE_PATH` when API unstable/unreachable
- [ ] Self-healing: restart player process on crash/freeze, detect stale output
- [ ] Prometheus metrics: mode, API health, ffprobe success/fail, player uptime, restarts
- [ ] Structured logging to file + stdout
- [ ] Config via `.env` with safe defaults

## Components Affected / To Create
- `vimeo_monitor/config.py`: Load/validate configuration (dotenv + pydantic)
- `vimeo_monitor/client.py`: Vimeo API client wrapper and endpoints
- `vimeo_monitor/stream.py`: Player process management (spawn/kill/switch); supports `cvlc` and `ffplay`
- `vimeo_monitor/health.py`: State machine, counters, API stability tracking
- `vimeo_monitor/metrics.py`: Prometheus metrics server and gauges/counters
- `vimeo_monitor/monitor.py`: Orchestrator main loop with polling and transitions
- `vimeo_monitor/__init__.py`: Package exports/version (exists)

## Implementation Strategy
1. Configuration and Scaffolding
   - [ ] Define `.env` keys: `VIMEO_ACCESS_TOKEN`, `VIMEO_VIDEO_ID`, `HOLDING_IMAGE_PATH`, `API_FAIL_IMAGE_PATH`, `CHECK_INTERVAL`, `LOG_LEVEL`
   - [ ] Implement `config.py` using pydantic for typed config
   - [ ] Add basic logging setup and logs directory
2. Metrics Server
   - [ ] Implement `metrics.py` with `prometheus_client` on port 8000 (configurable)
   - [ ] Expose gauges/counters placeholders
3. Vimeo API Client
   - [ ] Implement `client.py` using `pyvimeo`/`requests` to fetch playback URL
   - [ ] Add retry/backoff and structured error mapping
4. Stream Validation and Playback
   - [ ] Implement `ffprobe` validation utility
   - [ ] Implement `stream.py` with preferred `cvlc` and fallback `ffplay`
   - [ ] Ensure fullscreen and audio flags; detect/handle process death
5. Orchestration Loop
   - [ ] Implement `monitor.py` loop: poll → validate → play/hold → update metrics
   - [ ] Implement self-healing and mode switching logic
6. CLI Entry and Runner
   - [ ] Expose `python -m vimeo_monitor.monitor` entrypoint (works with `uv run`)
7. Basic Tests/Smoke
   - [ ] Run local image display POC
   - [ ] Run metrics endpoint and curl `/metrics`

## Detailed Steps
1. Create modules and wire imports; ensure `pyproject.toml` exports package path
2. Implement `Config` with sensible defaults and `.env` loading
3. Implement metrics registry with counters for modes and failures
4. Implement Vimeo client `get_m3u8_url(video_id)` with error handling
5. Implement `validate_stream(url)` using `ffprobe`
6. Implement `PlayerManager` to spawn `cvlc` or `ffplay` with proper args; monitor subprocess
7. Implement state machine transitions: `stream` ↔ `no_stream` ↔ `api_fail` with hysteresis
8. Integrate everything in `monitor.py` with periodic loop and graceful shutdown

## Dependencies
- System: `ffmpeg` (provides `ffprobe`, `ffplay`), `vlc`
- Python: `pyvimeo`, `requests`, `prometheus-client`, `python-dotenv`, `pydantic`, `watchdog`, `psutil`

## Challenges & Mitigations
- VLC/ffmpeg availability on Raspberry Pi → Pre-flight checks and multiple player support
- API instability → Backoff + hysteresis before switching out of failure modes
- X11/Audio environment issues → Document prerequisites; detect `$DISPLAY` and log actionable errors
- Credentials security → `.env` permissions and example template only
- Process zombie/defunct → Robust subprocess handling and timeouts

## Testing Strategy
- Smoke: local image display and metrics endpoint accessible
- Offline mode simulation: force no stream and API fail paths
- Process crash simulation: kill player and verify auto-restart
- Unit-level: config parsing, small utilities

## Creative Phases Required
- [x] 🏗️ Architecture: Player orchestration - [x] 🏗️ Architecture: Player orchestration & state machine design (options: pure Popen vs supervisor loop; transition thresholds) state machine design (Hybrid Approach with Process Manager selected)
- [ ] 🎨 UI/UX: N/A (headless; optional overlay later)
- [ ] ⚙️ Algorithm: N/A (simple heuristics adequate)

## Status
- [x] Initialization complete
- [x] Planning complete (this document)
- [x] Technology validation complete
- [ ] Implementation started

## NEXT RECOMMENDED MODE
- CREATIVE MODE (to finalize orchestration/state machine design before coding)

# Task: Development Environment Setup (Level 2)

## Description
Implement development environment automation including Dependabot for UV dependency management, GitHub Actions for MkDocs documentation publishing, and a basic CI/CD pipeline suitable for early development phases.

## Complexity
- Level: 2 (Enhancement)
- Type: Development Environment Enhancement

## Technology Stack
- **Dependency Management**: Dependabot with UV support
- **CI/CD**: GitHub Actions
- **Documentation**: MkDocs with GitHub Pages
- **Package Manager**: UV (already configured)

## Requirements Analysis
- [ ] Configure Dependabot for UV dependencies (pip ecosystem)
- [ ] Set up GitHub Actions for automated testing and linting
- [ ] Implement MkDocs documentation publishing workflow
- [ ] Create basic CI/CD pipeline for development workflow
- [ ] Ensure not overly strict for early development phases

## Components Affected / To Create
- `.github/dependabot.yml`: Dependabot configuration for UV
- `.github/workflows/ci.yml`: Main CI pipeline (lint, test, build)
- `.github/workflows/docs.yml`: Documentation publishing workflow
- `.github/workflows/deploy.yml`: Deployment workflow (if needed)

## Implementation Strategy
1. **Dependabot Setup**
   - [ ] Create `.github/dependabot.yml` with UV-compatible configuration
   - [ ] Configure weekly update schedule
   - [ ] Set proper labeling and assignment

2. **GitHub Actions Setup**
   - [ ] Create `.github/workflows/ci.yml` for main CI pipeline
   - [ ] Implement UV setup using official action
   - [ ] Add linting, testing, and build stages
   - [ ] Configure proper job dependencies

3. **Documentation Pipeline**
   - [ ] Create `.github/workflows/docs.yml` for MkDocs publishing
   - [ ] Configure GitHub Pages deployment
   - [ ] Set up proper permissions and concurrency

4. **CI/CD Pipeline**
   - [ ] Start with essential checks (lint, test)
   - [ ] Implement progressive enhancement approach
   - [ ] Ensure not overly strict for early development
   - [ ] Add clear success/failure indicators

## Dependencies
- **Existing**: pyproject.toml, mkdocs.yml, UV configuration
- **New**: GitHub Actions, Dependabot, GitHub Pages

## Challenges & Mitigations
- **UV Integration**: Use pip ecosystem in Dependabot (UV compatible)
- **Complexity Balance**: Start simple, enhance progressively
- **GitHub Pages**: Proper permissions and deployment configuration
- **CI/CD Strictness**: Keep early development friendly

## Testing Strategy
- **Dependabot**: Test with dependency update PRs
- **GitHub Actions**: Test workflows with pushes and PRs
- **Documentation**: Verify MkDocs build and deployment
- **CI/CD**: Test pipeline with various code changes

## Status
- [x] Creative phase complete (environment setup design)
- [ ] Implementation started
- [ ] Dependabot configuration
- [ ] GitHub Actions workflows
- [ ] Documentation pipeline
- [ ] CI/CD pipeline

## NEXT RECOMMENDED MODE
- IMPLEMENT mode (to create the actual configuration files and workflows)
