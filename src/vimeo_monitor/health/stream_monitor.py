#!/usr/bin/env python3
"""
Stream health monitor for Vimeo Monitor.

This module monitors the health of media streams using FFprobe.
"""

import json
import shlex
import subprocess
import time
from typing import Dict, List, Optional

try:
    from prometheus_client import Gauge
except ImportError:
    # Define dummy classes for type checking when prometheus_client is not available
    class Gauge:
        def set(self, value): pass
        def __init__(self, *args, **kwargs): pass

from ..config import Config
from ..logger import Logger, LoggingContext
from ..process_manager import ProcessManager


class StreamMonitor:
    """Monitors stream health using FFprobe."""

    def __init__(
        self,
        config: Config,
        logger: Logger,
        monitor=None,
        process_manager: Optional[ProcessManager] = None,
        registry=None
    ):
        """Initialize stream monitor.
        
        Args:
            config: Application configuration
            logger: Application logger
            monitor: Optional monitor instance for getting stream URL
            process_manager: Optional process manager for getting stream URL
            registry: Prometheus registry
        """
        self.config = config
        self.logger = logger
        self.stream_logger = LoggingContext(logger, "STREAM_HEALTH")
        self.monitor = monitor
        self.process_manager = process_manager
        self.registry = registry
        
        # Check if ffprobe is available
        if not self._is_ffprobe_available():
            self.stream_logger.error(
                "ffprobe not found. Please install ffmpeg/ffprobe."
            )
            raise ImportError("ffprobe not found")
        
        # FFprobe timeout
        self.ffprobe_timeout = getattr(self.config, "health_stream_ffprobe_timeout", 15)
        
        # Last check time
        self.last_check_time = time.time()
        
        # Initialize metrics
        self._setup_metrics()
    
    def _is_ffprobe_available(self) -> bool:
        """Check if ffprobe is available.
        
        Returns:
            True if ffprobe is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["ffprobe", "-version"],
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def _setup_metrics(self):
        """Set up stream health metrics."""
        # Stream availability
        self.stream_availability = Gauge(
            'vimeo_monitor_stream_availability',
            'Stream availability (1=available, 0=unavailable)',
            registry=self.registry
        )
        
        # Stream bitrate
        self.stream_bitrate = Gauge(
            'vimeo_monitor_stream_bitrate_kbps',
            'Stream bitrate in kbps',
            registry=self.registry
        )
        
        # Stream resolution
        self.stream_width = Gauge(
            'vimeo_monitor_stream_width_pixels',
            'Stream width in pixels',
            registry=self.registry
        )
        
        self.stream_height = Gauge(
            'vimeo_monitor_stream_height_pixels',
            'Stream height in pixels',
            registry=self.registry
        )
        
        # Stream framerate
        self.stream_framerate = Gauge(
            'vimeo_monitor_stream_framerate_fps',
            'Stream framerate in fps',
            registry=self.registry
        )
        
        # Audio channels
        self.stream_audio_channels = Gauge(
            'vimeo_monitor_stream_audio_channels',
            'Number of audio channels',
            registry=self.registry
        )
        
        # Audio sample rate
        self.stream_audio_sample_rate = Gauge(
            'vimeo_monitor_stream_audio_sample_rate_hz',
            'Audio sample rate in Hz',
            registry=self.registry
        )
        
        # Stream analysis time
        self.stream_analysis_time = Gauge(
            'vimeo_monitor_stream_analysis_time_seconds',
            'Time taken to analyze stream in seconds',
            registry=self.registry
        )
    
    def update_metrics(self):
        """Update stream health metrics."""
        try:
            # Get current stream URL
            stream_url = self._get_current_stream_url()
            
            if not stream_url:
                self.stream_logger.debug("No active stream URL found")
                self.stream_availability.set(0)
                # Reset all stream metrics to 0 when no stream
                self._reset_stream_metrics()
                return
            
            # Check if we have a new stream URL (different from last analysis)
            if stream_url != getattr(self, '_last_analyzed_url', None):
                self.stream_logger.info(f"New stream URL detected, analyzing: {stream_url[:50]}...")
                self._last_analyzed_url = stream_url
                
                # Analyze stream immediately
                start_time = time.time()
                stream_info = self._analyze_stream(stream_url)
                analysis_time = time.time() - start_time
                
                # Set analysis time metric
                self.stream_analysis_time.set(analysis_time)
                
                if stream_info:
                    self.stream_availability.set(1)
                    self._update_stream_metrics(stream_info)
                    self.stream_logger.info(f"Stream analysis successful: {stream_info.get('format_name', 'unknown')} format")
                else:
                    self.stream_availability.set(0)
                    self.stream_logger.warning(f"Stream analysis failed (URL may have expired): {stream_url[:50]}...")
                    # Keep previous metrics for a while in case of temporary issues
            else:
                # Same URL, just update availability
                self.stream_availability.set(1)
                self.stream_logger.debug("Stream URL unchanged, maintaining current metrics")
            
            self.last_check_time = time.time()
        except Exception as e:
            self.stream_logger.error(f"Failed to update stream health metrics: {e}")
            self.stream_availability.set(0)
    
    def _get_current_stream_url(self) -> Optional[str]:
        """Get current stream URL.
        
        Returns:
            Stream URL or None if not available
        """
        # Try to get URL from process manager
        if self.process_manager:
            try:
                process_info = self.process_manager.get_process_status()
                if process_info and "url" in process_info:
                    self.stream_logger.debug(f"Got stream URL from process manager: {process_info['url']}")
                    return process_info["url"]
            except Exception as e:
                self.stream_logger.error(f"Failed to get stream URL from process manager: {e}")
        
        # Try to get URL from monitor
        if self.monitor and hasattr(self.monitor, "get_stream_url"):
            try:
                url = self.monitor.get_stream_url()
                if url:
                    self.stream_logger.debug(f"Got stream URL from monitor: {url}")
                else:
                    self.stream_logger.debug("Monitor returned None for stream URL")
                return url
            except Exception as e:
                self.stream_logger.error(f"Failed to get stream URL from monitor: {e}")
        
        self.stream_logger.debug("No stream URL found from any source")
        return None
    
    def _analyze_stream(self, url: str) -> Optional[Dict]:
        """Analyze stream using ffprobe.
        
        Args:
            url: Stream URL
            
        Returns:
            Stream information dictionary or None if stream is unavailable
        """
        try:
            # Prepare ffprobe command with shorter timeout for security tokens
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                "-timeout", "5000000",  # 5 seconds in microseconds
                url
            ]
            
            # Run ffprobe with timeout
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            try:
                # Use shorter timeout for security token URLs
                timeout = min(self.ffprobe_timeout, 10)  # Max 10 seconds
                stdout, stderr = process.communicate(timeout=timeout)
                
                if process.returncode != 0:
                    self.stream_logger.error(f"ffprobe failed with return code {process.returncode}: {stderr}")
                    return None
                
                # Parse JSON output
                try:
                    stream_info = json.loads(stdout)
                    return stream_info
                except json.JSONDecodeError as e:
                    self.stream_logger.error(f"Failed to parse ffprobe output: {e}")
                    return None
            except subprocess.TimeoutExpired:
                process.kill()
                self.stream_logger.error(f"ffprobe timed out after {self.ffprobe_timeout} seconds")
                return None
        except Exception as e:
            self.stream_logger.error(f"Error running ffprobe: {e}")
            return None
    
    def _update_stream_metrics(self, stream_info: Dict):
        """Update stream metrics from ffprobe output.
        
        Args:
            stream_info: Stream information dictionary from ffprobe
        """
        try:
            # Extract video stream info
            video_stream = None
            audio_stream = None
            
            if "streams" in stream_info:
                for stream in stream_info["streams"]:
                    if stream.get("codec_type") == "video" and not video_stream:
                        video_stream = stream
                    elif stream.get("codec_type") == "audio" and not audio_stream:
                        audio_stream = stream
            
            # Update video metrics
            if video_stream:
                # Resolution
                if "width" in video_stream:
                    self.stream_width.set(video_stream["width"])
                
                if "height" in video_stream:
                    self.stream_height.set(video_stream["height"])
                
                # Framerate
                if "avg_frame_rate" in video_stream:
                    try:
                        num, den = map(int, video_stream["avg_frame_rate"].split("/"))
                        if den != 0:
                            framerate = num / den
                            self.stream_framerate.set(framerate)
                    except (ValueError, ZeroDivisionError):
                        pass
            
            # Update audio metrics
            if audio_stream:
                # Audio channels
                if "channels" in audio_stream:
                    self.stream_audio_channels.set(audio_stream["channels"])
                
                # Audio sample rate
                if "sample_rate" in audio_stream:
                    try:
                        sample_rate = int(audio_stream["sample_rate"])
                        self.stream_audio_sample_rate.set(sample_rate)
                    except ValueError:
                        pass
    
    def _reset_stream_metrics(self):
        """Reset all stream metrics to zero."""
        self.stream_bitrate.set(0)
        self.stream_width.set(0)
        self.stream_height.set(0)
        self.stream_framerate.set(0)
        self.stream_audio_channels.set(0)
        self.stream_audio_sample_rate.set(0)
        self.stream_analysis_time.set(0)
