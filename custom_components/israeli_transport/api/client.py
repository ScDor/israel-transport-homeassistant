"""Client for Israeli Public Transport API."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import aiohttp

from ..const import (
    API_BASE_URL,
    API_ENDPOINT_BUS,
    API_ENDPOINT_TRAIN,
    API_TIMEOUT,
    CACHE_TTL,
    MAX_CACHE_ITEMS,
)
from .auth import generate_api_key
from .models import BusResponse, TrainResponse

_LOGGER = logging.getLogger(__name__)


class IsraeliTransportClient:
    """Client for fetching Israeli transportation data."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize the client.

        Args:
            session: aiohttp client session to use for requests.
        """
        self._session = session
        self._cache: dict[str, BusResponse | TrainResponse] = {}
        self._cache_timestamps: dict[str, datetime] = {}

    def _get_cache_key(self, endpoint: str, params: dict[str, Any]) -> str:
        """Generate a cache key from the endpoint and params.

        Args:
            endpoint: The API endpoint.
            params: Request parameters.

        Returns:
            A string cache key.
        """
        # Sort list values to ensure consistent cache keys
        sorted_params = {
            k: ",".join(sorted(str(i) for i in v)) if isinstance(v, list) else str(v)
            for k, v in sorted(params.items())
        }
        param_str = "&".join(f"{k}={v}" for k, v in sorted_params.items())
        return f"{endpoint}?{param_str}"

    def _get_cached_response(
        self, cache_key: str
    ) -> BusResponse | TrainResponse | None:
        """Get a cached response if it exists and is still valid.

        Args:
            cache_key: The cache key to look up.

        Returns:
            The cached response if valid, None otherwise.
        """
        if cache_key not in self._cache:
            return None

        timestamp = self._cache_timestamps.get(cache_key)
        if not timestamp or datetime.now() - timestamp > CACHE_TTL:
            # Clean up expired cache entry
            self._cache.pop(cache_key, None)
            self._cache_timestamps.pop(cache_key, None)
            return None

        _LOGGER.debug("Using cached response for %s", cache_key)
        return self._cache[cache_key]

    def _cache_response(
        self, cache_key: str, response: BusResponse | TrainResponse
    ) -> None:
        """Cache a response and cleanup old entries if needed.

        Args:
            cache_key: The cache key to store under.
            response: The response to cache.
        """
        # Clean up old entries if cache is too large
        if len(self._cache) >= MAX_CACHE_ITEMS:
            # Remove oldest half of entries
            oldest_keys = sorted(
                self._cache_timestamps.keys(),
                key=lambda k: self._cache_timestamps[k],
            )[: len(self._cache) // 2]

            for key in oldest_keys:
                self._cache.pop(key, None)
                self._cache_timestamps.pop(key, None)

        self._cache[cache_key] = response
        self._cache_timestamps[cache_key] = datetime.now()

    async def _make_request(
        self, endpoint: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Make an API request.

        Args:
            endpoint: The API endpoint.
            params: Request parameters.

        Returns:
            The JSON response data.

        Raises:
            aiohttp.ClientError: If the request fails.
        """
        url = f"{API_BASE_URL}{endpoint}"
        headers = {
            "key": generate_api_key(),
            "User-Agent": "israeli-transport-homeassistant/2.0",
            "Content-Type": "application/json",
        }

        _LOGGER.debug("Making request to %s with params: %s", url, params)

        timeout = aiohttp.ClientTimeout(total=API_TIMEOUT)
        async with self._session.get(
            url, params=params, headers=headers, timeout=timeout, raise_for_status=True
        ) as response:
            return await response.json()

    async def get_bus_data(
        self, station_id: str | int, lines: list[str | int]
    ) -> BusResponse:
        """Get bus arrival data for a station and lines.

        Args:
            station_id: The station ID.
            lines: List of bus line numbers.

        Returns:
            BusResponse object containing the arrival data.

        Raises:
            aiohttp.ClientError: If the API request fails.
            ValueError: If the response cannot be parsed.
        """
        station_str = str(station_id)
        line_strings = [str(line) for line in lines]

        params = {"station": station_str, "lines": ",".join(line_strings)}
        cache_key = self._get_cache_key(API_ENDPOINT_BUS, params)

        # Check cache first
        if cached := self._get_cached_response(cache_key):
            if isinstance(cached, BusResponse):
                return cached

        # Make the request
        try:
            data = await self._make_request(API_ENDPOINT_BUS, params)
            result = BusResponse(**data)
        except Exception as ex:
            _LOGGER.exception("Failed to fetch or parse bus data")
            raise ValueError(f"Failed to get bus data: {ex}") from ex

        # Cache the result
        self._cache_response(cache_key, result)
        return result

    async def get_train_data(
        self, from_station: str | int, to_station: str | int
    ) -> TrainResponse:
        """Get train schedule data for a route.

        Args:
            from_station: The departure station ID.
            to_station: The destination station ID.

        Returns:
            TrainResponse object containing the train schedule.

        Raises:
            aiohttp.ClientError: If the API request fails.
            ValueError: If the response cannot be parsed.
        """
        from_station_str = str(from_station)
        to_station_str = str(to_station)

        params = {"fromStation": from_station_str, "toStation": to_station_str}
        cache_key = self._get_cache_key(API_ENDPOINT_TRAIN, params)

        # Check cache first
        if cached := self._get_cached_response(cache_key):
            if isinstance(cached, TrainResponse):
                return cached

        # Make the request
        try:
            data = await self._make_request(API_ENDPOINT_TRAIN, params)
            result = TrainResponse(**data)
        except Exception as ex:
            _LOGGER.exception("Failed to fetch or parse train data")
            raise ValueError(f"Failed to get train data: {ex}") from ex

        # Cache the result
        self._cache_response(cache_key, result)
        return result
