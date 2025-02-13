"""Client for fetching Israeli transportation data."""

import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .models.bus_response import BusResponse
from .utils import encrypt_key

_LOGGER = logging.getLogger(__name__)

BASE_URL = "https://silent-be.onrender.com"
CACHE_TTL = timedelta(seconds=60)
REQUEST_TIMEOUT = 10  # seconds
MAX_CACHE_ITEMS = 100


class Client:
    """Client for fetching Israeli transportation data."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the client."""
        self._hass = hass
        self._session = async_get_clientsession(hass)
        self._cache: dict[str, BusResponse] = {}
        self._cache_timestamps: dict[str, datetime] = {}

    def _get_cache_key(self, endpoint: str, params: dict[str, Any]) -> str:
        """Generate a cache key from the endpoint and params."""
        # Sort list values to ensure consistent cache keys
        sorted_params = {
            k: sorted(v) if isinstance(v, list) else v
            for k, v in sorted(params.items())
        }
        param_str = "&".join(f"{k}={v}" for k, v in sorted_params.items())
        return f"{endpoint}?{param_str}"

    def _get_cached_response(self, cache_key: str) -> BusResponse | None:
        """Get a cached response if it exists and is still valid."""
        if cache_key not in self._cache:
            return None

        timestamp = self._cache_timestamps.get(cache_key)
        if not timestamp or datetime.now() - timestamp > CACHE_TTL:
            # Clean up expired cache entry
            self._cache.pop(cache_key, None)
            self._cache_timestamps.pop(cache_key, None)
            return None

        return self._cache[cache_key]

    def _cache_response(self, cache_key: str, response: BusResponse) -> None:
        """Cache a response and cleanup old entries if needed."""
        # Clean up old entries if cache is too large
        if len(self._cache) >= MAX_CACHE_ITEMS:
            # Remove oldest entries
            oldest_keys = sorted(
                self._cache_timestamps.keys(),
                key=lambda k: self._cache_timestamps[k],
            )[: len(self._cache) // 2]  # Remove half of the oldest entries

            for key in oldest_keys:
                self._cache.pop(key, None)
                self._cache_timestamps.pop(key, None)

        self._cache[cache_key] = response
        self._cache_timestamps[cache_key] = datetime.now()

    async def get_bus_data(
        self, station: str | int, lines: list[str | int]
    ) -> BusResponse:
        """Get bus arrival data for a station and lines.

        Args:
            station: The station ID (can be string or integer)
            lines: List of line numbers (can be strings or integers)

        Returns:
            BusResponse object containing the arrival data

        Raises:
            Exception: If the API request fails or response parsing fails
        """
        # Convert all values to strings for consistency
        station_str = str(station)
        line_strings = [str(line) for line in lines]

        params = {"station": station_str, "lines": ",".join(line_strings)}
        cache_key = self._get_cache_key("busv2", params)

        # Check cache first
        if cached := self._get_cached_response(cache_key):
            _LOGGER.debug("Using cached response for %s", cache_key)
            return cached

        # Make the request
        _LOGGER.debug(
            "Getting info for station=%s, lines=%s", station_str, line_strings
        )
        try:
            async with self._session.get(
                f"{BASE_URL}/busv2",
                params=params,
                headers={
                    "key": encrypt_key(),
                    "User-Agent": "israel-transport-homeassistant",
                },
                raise_for_status=True,
                timeout=REQUEST_TIMEOUT,
            ) as response:
                data = await response.json()
        except TimeoutError as ex:
            _LOGGER.error("Request timed out after %d seconds", REQUEST_TIMEOUT)
            raise Exception(f"Request timed out: {ex!s}") from ex
        except aiohttp.ClientError as ex:
            _LOGGER.exception("Failed getting API data")
            raise Exception(f"API request failed: {ex!s}") from ex

        try:
            result = BusResponse(**data)
        except Exception as ex:
            _LOGGER.exception(
                "Failed parsing response: status=%s, content=%s",
                response.status,
                await response.text(),
            )
            raise Exception(f"Failed to parse API response: {ex!s}") from ex

        # Cache the result
        self._cache_response(cache_key, result)
        return result
