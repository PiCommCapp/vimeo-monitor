# Vimeo Monitor Design Patterns

## OVERVIEW

This document outlines the design patterns and architectural principles used in the Vimeo Monitor refactoring project. These patterns ensure maintainability, testability, and reliability while keeping the system simple and focused.

## CORE DESIGN PRINCIPLES

### 1. Single Responsibility Principle
Each module has one clear responsibility:
- **config.py**: Configuration management only
- **logger.py**: Logging and log rotation only
- **process_manager.py**: Process lifecycle management only
- **monitor.py**: Vimeo API monitoring only
- **main.py**: Orchestration and coordination only

### 2. Dependency Injection
Configuration and dependencies are injected rather than hardcoded:
```python
# Good: Dependency injection
def __init__(self, config: Config, logger: Logger):
    self.config = config
    self.logger = logger

# Bad: Hardcoded dependencies
def __init__(self):
    self.config = Config()  # Hardcoded
    self.logger = Logger()  # Hardcoded
```

### 3. Interface Segregation
Modules expose only the interfaces they need:
```python
# Good: Specific interface
class ProcessManager:
    def start_process(self, command: List[str]) -> subprocess.Popen
    def stop_process(self, process: subprocess.Popen) -> None
    def is_process_running(self, process: subprocess.Popen) -> bool

# Bad: Generic interface
class ProcessManager:
    def do_everything(self, *args, **kwargs) -> Any
```

### 4. Open/Closed Principle
Modules are open for extension but closed for modification:
```python
# Good: Extensible design
class Monitor:
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
    
    def check_stream_status(self) -> StreamStatus:
        # Can be extended with different API clients
        pass
```

## CONFIGURATION PATTERN

### Environment Variable Configuration
```python
class Config:
    def __init__(self):
        self.vimeo_token = os.getenv('VIMEO_TOKEN')
        self.vimeo_key = os.getenv('VIMEO_KEY')
        self.vimeo_secret = os.getenv('VIMEO_SECRET')
        self.stream_selection = int(os.getenv('STREAM_SELECTION', '1'))
        self.static_image_path = os.getenv('STATIC_IMAGE_PATH')
        self.log_file = os.getenv('LOG_FILE', '/home/admin/code/stream_monitor.log')
        self.check_interval = int(os.getenv('CHECK_INTERVAL', '10'))
    
    def validate(self) -> None:
        """Validate all required configuration"""
        required_vars = ['VIMEO_TOKEN', 'VIMEO_KEY', 'VIMEO_SECRET']
        for var in required_vars:
            if not getattr(self, var.lower().replace('_', '_')):
                raise ValueError(f"Required environment variable {var} not set")
```

### Configuration Validation Pattern
```python
def validate_config(config: Config) -> None:
    """Validate configuration and provide helpful error messages"""
    if not os.path.exists(config.static_image_path):
        raise FileNotFoundError(f"Static image not found: {config.static_image_path}")
    
    if config.check_interval < 1:
        raise ValueError("Check interval must be at least 1 second")
    
    if config.stream_selection not in range(1, 7):
        raise ValueError("Stream selection must be between 1 and 6")
```

## LOGGING PATTERN

### Structured Logging
```python
class Logger:
    def __init__(self, config: Config):
        self.config = config
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('vimeo_monitor')
        logger.setLevel(getattr(logging, self.config.log_level))
        
        # File handler with rotation
        file_handler = RotatingFileHandler(
            self.config.log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=self.config.log_rotation_days
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def info(self, message: str, **kwargs) -> None:
        self.logger.info(message, extra=kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        self.logger.error(message, extra=kwargs)
    
    def debug(self, message: str, **kwargs) -> None:
        self.logger.debug(message, extra=kwargs)
```

### Logging Context Pattern
```python
class LoggingContext:
    def __init__(self, logger: Logger, context: str):
        self.logger = logger
        self.context = context
    
    def info(self, message: str) -> None:
        self.logger.info(f"[{self.context}] {message}")
    
    def error(self, message: str) -> None:
        self.logger.error(f"[{self.context}] {message}")
    
    def debug(self, message: str) -> None:
        self.logger.debug(f"[{self.context}] {message}")

# Usage
monitor_logger = LoggingContext(logger, "MONITOR")
process_logger = LoggingContext(logger, "PROCESS")
```

## PROCESS MANAGEMENT PATTERN

### Process Lifecycle Management
```python
class ProcessManager:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.current_process: Optional[subprocess.Popen] = None
        self.current_mode: Optional[str] = None
    
    def start_stream_process(self, video_url: str) -> None:
        """Start VLC process for live stream"""
        if self.current_mode == "stream":
            return  # Already running
        
        self._stop_current_process()
        
        command = ["cvlc", "-f", video_url]
        self.logger.info(f"Starting stream process: {' '.join(command)}")
        
        try:
            self.current_process = subprocess.Popen(command)
            self.current_mode = "stream"
            self.logger.info("Stream process started successfully")
        except Exception as e:
            self.logger.error(f"Failed to start stream process: {e}")
            raise
    
    def start_image_process(self, image_path: str) -> None:
        """Start FFmpeg process for static image"""
        if self.current_mode == "image":
            return  # Already running
        
        self._stop_current_process()
        
        command = ["ffplay", "-fs", "-loop", "1", image_path]
        self.logger.info(f"Starting image process: {' '.join(command)}")
        
        try:
            self.current_process = subprocess.Popen(command)
            self.current_mode = "image"
            self.logger.info("Image process started successfully")
        except Exception as e:
            self.logger.error(f"Failed to start image process: {e}")
            raise
    
    def _stop_current_process(self) -> None:
        """Stop current process if running"""
        if self.current_process and self.current_process.poll() is None:
            self.logger.info("Stopping current process")
            self.current_process.terminate()
            try:
                self.current_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.logger.warning("Process didn't terminate, killing")
                self.current_process.kill()
                self.current_process.wait()
        
        self.current_process = None
        self.current_mode = None
    
    def is_process_running(self) -> bool:
        """Check if current process is running"""
        return (self.current_process is not None and 
                self.current_process.poll() is None)
    
    def cleanup(self) -> None:
        """Clean up on shutdown"""
        self._stop_current_process()
        self.logger.info("Process manager cleaned up")
```

## MONITORING PATTERN

### API Monitoring with Retry Logic
```python
class Monitor:
    def __init__(self, config: Config, logger: Logger, process_manager: ProcessManager):
        self.config = config
        self.logger = logger
        self.process_manager = process_manager
        self.api_client = VimeoClient(
            token=config.vimeo_token,
            key=config.vimeo_key,
            secret=config.vimeo_secret
        )
        self.stream_id = self._get_stream_id()
    
    def _get_stream_id(self) -> str:
        """Get stream ID for selected stream"""
        streams = {
            1: "4797083", 2: "4797121", 3: "4898539",
            4: "4797153", 5: "4797202", 6: "4797207"
        }
        return streams.get(self.config.stream_selection)
    
    def check_stream_status(self) -> StreamStatus:
        """Check if stream is live with retry logic"""
        for attempt in range(self.config.max_retries):
            try:
                stream_url = f"https://api.vimeo.com/me/live_events/{self.stream_id}/m3u8_playback"
                response = self.api_client.get(stream_url)
                response_data = response.json()
                
                if "m3u8_playback_url" in response_data:
                    return StreamStatus.LIVE, response_data["m3u8_playback_url"]
                else:
                    return StreamStatus.OFFLINE, None
                    
            except RequestException as e:
                self.logger.error(f"API request failed (attempt {attempt + 1}): {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise
        
        return StreamStatus.ERROR, None
    
    def update_display(self, status: StreamStatus, video_url: Optional[str] = None) -> None:
        """Update display based on stream status"""
        if status == StreamStatus.LIVE and video_url:
            self.process_manager.start_stream_process(video_url)
        elif status == StreamStatus.OFFLINE:
            self.process_manager.start_image_process(self.config.static_image_path)
        else:
            self.logger.error("Unknown stream status or missing video URL")
```

## ERROR HANDLING PATTERN

### Graceful Error Handling
```python
class ErrorHandler:
    def __init__(self, logger: Logger):
        self.logger = logger
    
    def handle_api_error(self, error: RequestException) -> None:
        """Handle API errors with appropriate logging"""
        if hasattr(error, 'response') and error.response is not None:
            status_code = error.response.status_code
            if status_code == 401:
                self.logger.error("API authentication failed - check credentials")
            elif status_code == 429:
                self.logger.warning("API rate limit exceeded - backing off")
            elif status_code >= 500:
                self.logger.error(f"API server error: {status_code}")
            else:
                self.logger.error(f"API error: {status_code} - {error}")
        else:
            self.logger.error(f"Network error: {error}")
    
    def handle_process_error(self, error: subprocess.SubprocessError) -> None:
        """Handle process errors with appropriate logging"""
        self.logger.error(f"Process error: {error}")
    
    def handle_config_error(self, error: ValueError) -> None:
        """Handle configuration errors with helpful messages"""
        self.logger.error(f"Configuration error: {error}")
        self.logger.info("Please check your .env file and ensure all required variables are set")
```

## MAIN ORCHESTRATOR PATTERN

### Simple Orchestrator
```python
class MainOrchestrator:
    def __init__(self):
        self.config = Config()
        self.logger = Logger(self.config)
        self.process_manager = ProcessManager(self.logger)
        self.monitor = Monitor(self.config, self.logger, self.process_manager)
        self.error_handler = ErrorHandler(self.logger)
        self.running = False
    
    def start(self) -> None:
        """Start the monitoring system"""
        try:
            self.config.validate()
            self.logger.info("Starting Vimeo Monitor")
            self.running = True
            
            while self.running:
                try:
                    status, video_url = self.monitor.check_stream_status()
                    self.monitor.update_display(status, video_url)
                    time.sleep(self.config.check_interval)
                    
                except RequestException as e:
                    self.error_handler.handle_api_error(e)
                    time.sleep(self.config.check_interval)
                    
                except subprocess.SubprocessError as e:
                    self.error_handler.handle_process_error(e)
                    time.sleep(self.config.check_interval)
                    
        except ValueError as e:
            self.error_handler.handle_config_error(e)
            raise
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        finally:
            self.shutdown()
    
    def shutdown(self) -> None:
        """Graceful shutdown"""
        self.logger.info("Shutting down Vimeo Monitor")
        self.running = False
        self.process_manager.cleanup()
        self.logger.info("Shutdown complete")

# Entry point
if __name__ == "__main__":
    orchestrator = MainOrchestrator()
    orchestrator.start()
```

## TESTING PATTERNS

### Dependency Injection for Testing
```python
class TestableMonitor:
    def __init__(self, config: Config, logger: Logger, 
                 process_manager: ProcessManager, api_client: VimeoClient):
        self.config = config
        self.logger = logger
        self.process_manager = process_manager
        self.api_client = api_client
    
    def check_stream_status(self) -> StreamStatus:
        # Testable with mock API client
        pass

# Test
def test_monitor_with_mock_api():
    config = Config()
    logger = MockLogger()
    process_manager = MockProcessManager()
    api_client = MockVimeoClient()
    
    monitor = TestableMonitor(config, logger, process_manager, api_client)
    # Test with mock
```

### Configuration Testing
```python
def test_config_validation():
    # Test valid configuration
    config = Config()
    config.vimeo_token = "test_token"
    config.vimeo_key = "test_key"
    config.vimeo_secret = "test_secret"
    config.static_image_path = "/path/to/image.png"
    
    # Should not raise
    config.validate()
    
    # Test invalid configuration
    config.vimeo_token = None
    with pytest.raises(ValueError):
        config.validate()
```

## SUMMARY

These design patterns ensure:
- **Maintainability**: Clear separation of concerns
- **Testability**: Dependency injection and mocking
- **Reliability**: Comprehensive error handling
- **Simplicity**: Focused, single-purpose modules
- **Extensibility**: Open/closed principle
- **Configuration**: Externalized and validated settings

The patterns follow Python best practices and maintain the principle of "simple wins the day" while providing a solid foundation for future enhancements.

---

**Status**: Design patterns documented  
**Next Action**: Use these patterns in implementation  
**Priority**: High - Essential for consistent implementation
