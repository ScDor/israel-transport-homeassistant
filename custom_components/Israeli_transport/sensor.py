"""Support for Israeli public transportation data."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import Throttle

from .client.client import Client
from .client.models.bus_response import BusResponse
from .constants import (
    CONF_BUS_LINES,
    CONF_BUS_STATION_ID,
    CONF_NAME,
    CONF_ONLY_REAL_TIME,
    CONF_STATIONS,
)

_LOGGER = logging.getLogger(__name__)

# Update interval - will be dynamically adjusted based on next arrival
SCAN_INTERVAL = timedelta(seconds=90)

ATTR_STATION_ID = "station_id"
ATTR_BUS_LINES = "bus_lines"
ATTR_NEXT_BUSES = "next_buses"
ATTR_REAL_TIME_DATA = "real_time_data"

BUS_ETA_SENSOR_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): str,
        vol.Required(CONF_BUS_STATION_ID): cv.positive_int,
        vol.Required(CONF_BUS_LINES): vol.All(cv.ensure_list),
        vol.Required(CONF_ONLY_REAL_TIME): bool,
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_STATIONS): vol.All(cv.ensure_list, [BUS_ETA_SENSOR_SCHEMA])}
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Israeli Transportation sensor."""
    client = Client(hass)

    sensors = [
        IsraeliTransportSensor(
            client=client,
            name=entry[CONF_NAME],
            line_numbers=entry[CONF_BUS_LINES],
            station_number=entry[CONF_BUS_STATION_ID],
            only_real_time=entry[CONF_ONLY_REAL_TIME],
        )
        for entry in config[CONF_STATIONS]
    ]

    async_add_entities(sensors, True)


class IsraeliTransportSensor(SensorEntity):
    """Implementation of an Israeli public transport sensor."""

    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:bus-clock"
    _attr_has_entity_name = True

    def __init__(
        self,
        client: Client,
        name: str,
        station_number: int,
        line_numbers: list[int | str],
        only_real_time: bool,
    ) -> None:
        """Initialize the sensor."""
        self._client = client
        self._attr_name = name
        self._station_number = station_number
        self._bus_lines = sorted(set(map(str, line_numbers)))
        self._only_real_time = only_real_time
        self._attr_native_value = None
        self._attr_extra_state_attributes: dict[str, Any] = {}
        self._available = True

        # Set unique ID
        self._attr_unique_id = (
            f"israeli_transport_bus_{station_number}_{'_'.join(self._bus_lines)}"
        )

        # Set device info
        self._attr_device_info = {
            "identifiers": {("Israeli_transport", str(station_number))},
            "name": f"Bus Station {station_number}",
            "manufacturer": "Israeli Ministry of Transportation",
            "model": "Bus Station",
            "sw_version": "1.0",
        }

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @Throttle(SCAN_INTERVAL)
    async def async_update(self) -> None:
        """Get the latest data from transportation API."""
        try:
            response = await self._client.get_bus_data(
                station=self._station_number, lines=self._bus_lines
            )
        except Exception as ex:
            _LOGGER.exception("Failed retrieving bus data")
            self._available = False
            self._attr_native_value = None
            self._attr_extra_state_attributes = {
                "error": str(ex),
                ATTR_STATION_ID: self._station_number,
                ATTR_BUS_LINES: self._bus_lines,
            }
            return

        self._available = True
        self._process_data(response)

    def _process_data(self, response: BusResponse) -> None:
        """Process the received bus data."""
        if not response.bus_data:
            _LOGGER.warning("No bus data received")
            self._attr_native_value = None
            self._attr_extra_state_attributes = {
                ATTR_STATION_ID: self._station_number,
                ATTR_BUS_LINES: self._bus_lines,
                ATTR_NEXT_BUSES: [],
                ATTR_REAL_TIME_DATA: False,
            }
            return

        real_time_arrivals = [d for d in response.bus_data if d.is_real_time]

        if not real_time_arrivals and self._only_real_time:
            _LOGGER.warning("No real-time data available and only_real_time is set")
            self._attr_native_value = None
        else:
            arrivals_to_use = (
                real_time_arrivals if real_time_arrivals else response.bus_data
            )
            if arrivals_to_use:
                # Convert seconds to minutes and round
                earliest_arrival = min(
                    arrivals_to_use,
                    key=lambda x: x.real_time_arrives_in
                    if x.is_real_time
                    else x.planned_time_arrives_in,
                )
                arrival_time = (
                    earliest_arrival.real_time_arrives_in
                    if earliest_arrival.is_real_time
                    else earliest_arrival.planned_time_arrives_in
                )
                self._attr_native_value = round(arrival_time / 60)
                _LOGGER.debug(
                    "Updated arrival time: %d minutes for station %d",
                    self._attr_native_value,
                    self._station_number,
                )

        # Update attributes with detailed information
        next_buses = []
        for bus in response.bus_data:
            next_buses.append(
                {
                    "line": bus.line_number,
                    "real_time": bus.is_real_time,
                    "eta_minutes": round(
                        (
                            bus.real_time_arrives_in
                            if bus.is_real_time
                            else bus.planned_time_arrives_in
                        )
                        / 60
                    ),
                    "destination": bus.destination,
                }
            )

        self._attr_extra_state_attributes = {
            ATTR_STATION_ID: self._station_number,
            ATTR_BUS_LINES: self._bus_lines,
            ATTR_NEXT_BUSES: next_buses,
            ATTR_REAL_TIME_DATA: bool(real_time_arrivals),
        }
