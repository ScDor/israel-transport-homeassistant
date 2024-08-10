"""Israeli transportation integration."""

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from loguru import logger

from .constants import (
    CONF_BUS_LINES,
    CONF_BUS_STATION_ID,
    INTEGRATION_NAME,
    SENSOR,
)
from .sensor import BusETASensor


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    sensor = BusETASensor(
        line_numbers=entry.data[CONF_BUS_LINES],
        station_number=entry.data[CONF_BUS_STATION_ID],
        only_real_time=True,  # TODO change
    )
    coordinator = DataUpdateCoordinator(
        hass,
        logger=logger,
        name=INTEGRATION_NAME,
        update_interval=timedelta(seconds=entry.data[CONF_SCAN_INTERVAL]),
        update_method=sensor.async_update,
    )

    await coordinator.async_refresh()
    hass.data.setdefault(INTEGRATION_NAME, {})[entry.entry_id] = coordinator
    hass.async_add_job(hass.config_entries.async_forward_entry_setup(entry, SENSOR))
    return True
