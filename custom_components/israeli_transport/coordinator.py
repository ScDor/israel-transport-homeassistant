"""Data update coordinator for Israeli Public Transport."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BusResponse, IsraeliTransportClient, TrainResponse
from .const import (
    CONF_BUS_LINES,
    CONF_FROM_STATION,
    CONF_STATION_ID,
    CONF_TO_STATION,
    CONF_TRANSPORT_TYPE,
    DOMAIN,
    TRANSPORT_TYPE_BUS,
    TRANSPORT_TYPE_TRAIN,
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class TransportData:
    """Data class for transport information."""

    transport_type: str
    data: BusResponse | TrainResponse
    config: dict[str, Any]


class IsraeliTransportCoordinator(DataUpdateCoordinator[TransportData]):
    """Coordinator to manage data updates for Israeli Transport."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: IsraeliTransportClient,
        config: dict[str, Any],
    ) -> None:
        """Initialize the coordinator.

        Args:
            hass: Home Assistant instance.
            client: The API client.
            config: Configuration dictionary.
        """
        self.client = client
        self.config = config
        self.transport_type = config.get(CONF_TRANSPORT_TYPE, TRANSPORT_TYPE_BUS)

        # Create a unique name for this coordinator
        if self.transport_type == TRANSPORT_TYPE_BUS:
            station_id = config[CONF_STATION_ID]
            name = f"{DOMAIN}_bus_{station_id}"
        else:
            from_station = config[CONF_FROM_STATION]
            to_station = config[CONF_TO_STATION]
            name = f"{DOMAIN}_train_{from_station}_{to_station}"

        super().__init__(
            hass,
            _LOGGER,
            name=name,
            update_interval=UPDATE_INTERVAL,
        )

    async def _async_update_data(self) -> TransportData:
        """Fetch data from API.

        Returns:
            TransportData object with the latest data.

        Raises:
            UpdateFailed: If the update fails.
        """
        try:
            if self.transport_type == TRANSPORT_TYPE_BUS:
                data = await self._fetch_bus_data()
            else:
                data = await self._fetch_train_data()

            return TransportData(
                transport_type=self.transport_type,
                data=data,
                config=self.config,
            )
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    async def _fetch_bus_data(self) -> BusResponse:
        """Fetch bus data from the API.

        Returns:
            BusResponse object.
        """
        station_id = self.config[CONF_STATION_ID]
        lines = self.config[CONF_BUS_LINES]

        _LOGGER.debug("Fetching bus data for station %s, lines %s", station_id, lines)
        return await self.client.get_bus_data(station_id, lines)

    async def _fetch_train_data(self) -> TrainResponse:
        """Fetch train data from the API.

        Returns:
            TrainResponse object.
        """
        from_station = self.config[CONF_FROM_STATION]
        to_station = self.config[CONF_TO_STATION]

        _LOGGER.debug(
            "Fetching train data from %s to %s", from_station, to_station
        )
        return await self.client.get_train_data(from_station, to_station)
