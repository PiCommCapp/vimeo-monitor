#!/usr/bin/env python3
"""
Logging module for Vimeo Monitor.

This module provides structured logging with rotation capabilities.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional
from .config import Config


class Logger:
    """Logger class for Vimeo Monitor with rotation support."""
    
    def __init__(self, config: Config):
        """Initialize logger with configuration."""
        self.config = config
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Set up the logger with file rotation and console output."""
        logger = logging.getLogger('vimeo_monitor')
        logger.setLevel(getattr(logging, self.config.log_level.upper()))
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(self.config.log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
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
        """Log info message."""
        self.logger.info(message, extra=kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self.logger.error(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(message, extra=kwargs)
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        self.logger.critical(message, extra=kwargs)


class LoggingContext:
    """Context-aware logger for different components."""
    
    def __init__(self, logger: Logger, context: str):
        """Initialize logging context."""
        self.logger = logger
        self.context = context
    
    def info(self, message: str) -> None:
        """Log info message with context."""
        self.logger.info(f"[{self.context}] {message}")
    
    def error(self, message: str) -> None:
        """Log error message with context."""
        self.logger.error(f"[{self.context}] {message}")
    
    def warning(self, message: str) -> None:
        """Log warning message with context."""
        self.logger.warning(f"[{self.context}] {message}")
    
    def debug(self, message: str) -> None:
        """Log debug message with context."""
        self.logger.debug(f"[{self.context}] {message}")
    
    def critical(self, message: str) -> None:
        """Log critical message with context."""
        self.logger.critical(f"[{self.context}] {message}")


# Global logger instance (will be initialized with config)
logger: Optional[Logger] = None


def get_logger(config: Config) -> Logger:
    """Get or create the global logger instance."""
    global logger
    if logger is None:
        logger = Logger(config)
    return logger
