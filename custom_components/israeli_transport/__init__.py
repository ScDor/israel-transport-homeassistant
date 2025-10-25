"""The Israeli Public Transport integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import IsraeliTransportClient
from .const import DOMAIN
from .coordinator import IsraeliTransportCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Israeli Public Transport from a config entry.

    Args:
        hass: Home Assistant instance.
        entry: The config entry.

    Returns:
        True if setup was successful.
    """
    _LOGGER.debug("Setting up Israeli Transport integration with config: %s", entry.data)

    # Create API client
    session = async_get_clientsession(hass)
    client = IsraeliTransportClient(session)

    # Create coordinator
    coordinator = IsraeliTransportCoordinator(hass, client, dict(entry.data))

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.

    Args:
        hass: Home Assistant instance.
        entry: The config entry.

    Returns:
        True if unload was successful.
    """
    _LOGGER.debug("Unloading Israeli Transport integration")

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Remove coordinator
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
