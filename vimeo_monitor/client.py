#!/usr/bin/env python3

"""Vimeo API client with comprehensive error handling and response validation."""

import logging
import time
from typing import Any

from requests.exceptions import (
    ChunkedEncodingError,
    ConnectionError,
    HTTPError,
    RequestException,
    Timeout,
    TooManyRedirects,
)
from vimeo import VimeoClient  # type: ignore[import-untyped]

from vimeo_monitor.config import ConfigManager
from vimeo_monitor.health import HealthMonitor


class VimeoAPIClient:
    """Vimeo API client with comprehensive error handling and health tracking."""

    def __init__(
        self, config: ConfigManager, health_monitor: HealthMonitor, performance_optimizer: Any | None = None
    ) -> None:
        """Initialize Vimeo API client.

        Args:
            config: Configuration manager instance
            health_monitor: Health monitor instance for tracking API health
            performance_optimizer: Optional performance optimizer for caching and monitoring
        """
        self.config = config
        self.health_monitor = health_monitor
        self.performance_optimizer = performance_optimizer

        # Initialize Vimeo client
        self.client = VimeoClient(
            token=config.vimeo_token,
            key=config.vimeo_key,
            secret=config.vimeo_secret,
        )

        # Cache settings
        self.cache_enabled = getattr(config, "enable_api_caching", True)
        self.cache_ttl = getattr(config, "api_cache_ttl", 60.0)  # 1 minute default

        logging.debug("Vimeo API client initialized (caching=%s)", self.cache_enabled)

    def get_stream_data(self) -> dict[str, Any] | None:
        """Fetch stream data from Vimeo API with optional caching.

        Returns:
            Stream data dictionary or None if failed
        """
        if not self.config.vimeo_stream_id:
            logging.error("No valid stream ID found: %s", self.config.vimeo_stream_id)
            return None

        # Use caching if performance optimizer is available and enabled
        if self.performance_optimizer and self.cache_enabled:
            cache_key = f"stream_data_{self.config.vimeo_stream_id}"
            return self.performance_optimizer.cached_api_call(
                cache_key=cache_key,
                api_function=self._fetch_stream_data_uncached,
                ttl=self.cache_ttl,
                endpoint="stream_data",
            )
        else:
            return self._fetch_stream_data_uncached()

    def _fetch_stream_data_uncached(self) -> dict[str, Any] | None:
        """Internal method to fetch stream data without caching."""
        # Build the Vimeo API request URL
        stream_url = f"https://api.vimeo.com/me/live_events/{self.config.vimeo_stream_id}/m3u8_playbook"

        start_time = time.time()

        try:
            # Request JSON data using VimeoClient
            response = self.client.get(stream_url)  # type: ignore[misc]

            # Calculate response time
            response_time = time.time() - start_time

            # Check for HTTP errors (4xx, 5xx status codes)
            if hasattr(response, "status_code"):
                if response.status_code == 401:
                    self.health_monitor.handle_api_failure(
                        "authentication", "Authentication failed (401): Check API credentials"
                    )
                    return None
                elif response.status_code == 403:
                    self.health_monitor.handle_api_failure(
                        "authorization", "Access forbidden (403): Check API permissions"
                    )
                    return None
                elif response.status_code == 404:
                    self.health_monitor.handle_api_failure(
                        "not_found", f"Stream not found (404): Check stream ID {self.config.vimeo_stream_id}"
                    )
                    return None
                elif response.status_code == 429:
                    self.health_monitor.handle_api_failure("rate_limit", "Rate limit exceeded (429): Too many requests")
                    return None
                elif response.status_code >= 500:
                    self.health_monitor.handle_api_failure(
                        "server_error", f"Server error ({response.status_code}): Vimeo API issues"
                    )
                    return None
                elif response.status_code >= 400:
                    self.health_monitor.handle_api_failure(
                        "client_error", f"Client error ({response.status_code}): Check API request"
                    )
                    return None

            response_data = response.json()

            # Validate response structure
            if not isinstance(response_data, dict):
                self.health_monitor.handle_api_failure("invalid_response", "API response is not a valid JSON object")
                return None

            # Add debug logging for the API response
            logging.debug("Vimeo API Response status: %s", "success" if response_data else "empty")

            # Record performance metrics directly if no optimizer
            if not self.performance_optimizer and hasattr(self.health_monitor, "performance_optimizer"):
                if hasattr(self.health_monitor.performance_optimizer, "monitor"):
                    self.health_monitor.performance_optimizer.monitor.record_api_response_time(response_time)

            self.health_monitor.handle_api_success(response_time)
            return response_data

        except ConnectionError as e:
            self.health_monitor.handle_api_failure("connection", f"Network connection failed: {e!s}")
            logging.debug("Connection error details:", exc_info=True)
        except Timeout as e:
            self.health_monitor.handle_api_failure("timeout", f"Request timed out: {e!s}")
            logging.debug("Timeout error details:", exc_info=True)
        except HTTPError as e:
            self.health_monitor.handle_api_failure("http_error", f"HTTP error occurred: {e!s}")
            logging.debug("HTTP error details:", exc_info=True)
        except TooManyRedirects as e:
            self.health_monitor.handle_api_failure("redirect_error", f"Too many redirects: {e!s}")
            logging.debug("Redirect error details:", exc_info=True)
        except ChunkedEncodingError as e:
            self.health_monitor.handle_api_failure("encoding_error", f"Chunked encoding error: {e!s}")
            logging.debug("Encoding error details:", exc_info=True)
        except ValueError as e:
            self.health_monitor.handle_api_failure("json_error", f"Failed to parse JSON response: {e!s}")
            logging.debug("JSON parsing error details:", exc_info=True)
        except RequestException as e:
            self.health_monitor.handle_api_failure("request_error", f"General request error: {e!s}")
            logging.debug("Request error details:", exc_info=True)
        except Exception as e:
            self.health_monitor.handle_api_failure("unknown", f"Unexpected error: {e!s}")
            logging.exception("Unexpected error:")

        return None

    def is_stream_active(self, response_data: dict[str, Any] | None) -> bool:
        """Check if stream is active based on API response.

        Args:
            response_data: API response data

        Returns:
            True if stream is active, False otherwise
        """
        if not response_data:
            return False

        has_playbook_url = "m3u8_playbook_url" in response_data

        if has_playbook_url:
            logging.debug("Found m3u8_playbook_url in response")
        else:
            logging.debug("No m3u8_playbook_url found in response. Full response: %s", response_data)

        return has_playbook_url

    def get_stream_url(self, response_data: dict[str, Any] | None) -> str | None:
        """Extract stream URL from API response.

        Args:
            response_data: API response data

        Returns:
            Stream URL or None if not available
        """
        if not response_data or not self.is_stream_active(response_data):
            return None

        return response_data.get("m3u8_playbook_url")

    def validate_configuration(self) -> bool:
        """Validate API configuration.

        Returns:
            True if configuration is valid, False otherwise
        """
        required_config = [
            self.config.vimeo_token,
            self.config.vimeo_key,
            self.config.vimeo_secret,
            self.config.vimeo_stream_id,
        ]

        return all(config is not None for config in required_config)

    def get_api_info(self) -> dict[str, Any]:
        """Get API configuration information for logging.

        Returns:
            API configuration info dictionary
        """
        return {
            "stream_id": self.config.vimeo_stream_id,
            "has_token": bool(self.config.vimeo_token),
            "has_key": bool(self.config.vimeo_key),
            "has_secret": bool(self.config.vimeo_secret),
            "caching_enabled": self.cache_enabled,
            "cache_ttl": self.cache_ttl,
        }

    def clear_cache(self) -> None:
        """Clear API response cache if available."""
        if self.performance_optimizer:
            self.performance_optimizer.cache.clear()
            logging.info("API response cache cleared")
        else:
            logging.debug("No performance optimizer available for cache clearing")

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics if available."""
        if self.performance_optimizer:
            return self.performance_optimizer.cache.get_stats()
        return {"error": "No performance optimizer available"}
