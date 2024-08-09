"""Israeli transportation integration."""

from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_SCAN_INTERVAL

from .sensor import BusArrivalSensor


def validate_bus_lines(value: Any):
    if not (
        isinstance(value, list)
        and (all(isinstance(list_item, (int, str)) for list_item in value))
    ):
        raise vol.Invalid("bus_lines must be a list of numbers or strings")


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required("station_id"): cv.positive_int,
        vol.Required("bus_lines"): validate_bus_lines,
        vol.Required(CONF_SCAN_INTERVAL, default=90): cv.positive_int,
    }
)


async def async_setup_platform(
    hass,  # noqa: ARG001
    config,
    async_add_entities,
    discovery_info=None,  # noqa: ARG001
):
    config = PLATFORM_SCHEMA(config)
    await async_add_entities(
        [
            BusArrivalSensor(station_number=config["station_id"], line_numbers=lines)
            for lines in config["bus_lines"]
        ]
    )
