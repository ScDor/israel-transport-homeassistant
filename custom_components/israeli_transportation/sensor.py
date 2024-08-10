from datetime import timedelta
from typing import Any, Callable

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
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
)
from loguru import logger

from .client.client import Client
from .client.models.bus_response import BusArrivalData, BusResponse
from .constants import (
    CONF_BUS_LINES,
    CONF_BUS_STATION_ID,
    CONF_NAME,
    CONF_ONLY_REAL_TIME,
    CONF_STATIONS,
)

logger.add("bus.log")
BUS_ETA_SENSOR_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): str,
        vol.Required(CONF_BUS_STATION_ID): cv.positive_int,
        vol.Required(CONF_BUS_LINES): vol.All(cv.ensure_list),
        vol.Required(CONF_ONLY_REAL_TIME): bool,
    }
)


SCAN_INTERVAL = timedelta(seconds=90)
# TODO not scan when there are no planned trips?

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_STATIONS): vol.All(cv.ensure_list, [BUS_ETA_SENSOR_SCHEMA])}
)


class BusETASensor(SensorEntity):
    device_class = SensorDeviceClass.DURATION

    _attr_name = "Bus ETA"
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        name: str,
        station_number: int,
        line_numbers: list[int | str],
        only_real_time: bool,
    ):
        self._name = name

        self._station_number: int = station_number
        self._bus_lines: list[str] = sorted(set(map(str, line_numbers)))
        self._only_real_time: bool = only_real_time

        self._state: int | None = None
        self._attributes: dict | None = None

    @property
    def line_numbers_string(self) -> str:
        return ",".join(self._bus_lines)

    @property
    def name(self) -> str:
        return self._name

    @property
    def state(self) -> int | None:
        return self._state

    @property
    def device_state_attributes(self) -> dict[str, Any]:
        return self.attributes

    def set_value(self, earliest_arrival: int | None):
        logger.debug(f"previous {self._attr_native_value=}")
        self._attr_native_value = earliest_arrival
        logger.info(f"set {self._attr_native_value=}")

    def clear_state(self):
        self.set_value(None)

    def set_attributes(self, response: BusResponse):
        self.attributes = response.__dict__

    async def async_update(self):
        try:
            response = await Client.get_bus_data(
                station=self._station_number, lines=self._bus_lines
            )
        except Exception:  # noqa: BLE001
            logger.exception("Failed retrieving bus data")
            self.clear_state()  # TODO ?
            return

        if not response.bus_data:
            logger.warning("No bus data received")
            self.clear_state()  # TODO change?

        if not any(
            real_time := tuple(filter(lambda d: d.is_real_time, response.bus_data))
        ):
            message = "Data is not real time"
            if self._only_real_time:
                logger.error(message)
                self.clear_state()
                return
            logger.warning(message)

        self.set_attributes(response)

        earliest_real_time_arrival: BusArrivalData | None = min(
            real_time,
            key=lambda datum: datum.real_time_arrives_in,
            default=None,
        )
        if earliest_real_time_arrival:
            self.set_value(earliest_real_time_arrival.real_time_arrives_in)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: Callable,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    async_add_entities(
        [
            BusETASensor(
                name=entry[CONF_NAME],
                line_numbers=entry[CONF_BUS_LINES],
                station_number=entry[CONF_BUS_STATION_ID],
                only_real_time=entry[CONF_ONLY_REAL_TIME],
            )
            for entry in config[CONF_STATIONS]
        ],
        update_before_add=True,
    )
