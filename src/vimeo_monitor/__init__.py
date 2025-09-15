"""
Vimeo Monitor Package

A modular system for monitoring Vimeo live streams and displaying them
on a Raspberry Pi with proper configuration management and logging.
"""

__version__ = "0.0.2"
__author__ = "Dom Capparelli"
__email__ = "web@Capparelli.ie"

from .config import Config, config
from .logger import Logger, LoggingContext, get_logger

__all__ = [
    "Config",
    "config", 
    "Logger",
    "LoggingContext",
    "get_logger"
]
