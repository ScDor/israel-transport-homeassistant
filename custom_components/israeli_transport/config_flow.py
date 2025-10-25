"""Config flow for Israeli Public Transport integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import IsraeliTransportClient
from .const import (
    CONF_BUS_LINES,
    CONF_CREATE_LINE_SENSORS,
    CONF_FROM_STATION,
    CONF_ONLY_REAL_TIME,
    CONF_STATION_ID,
    CONF_TO_STATION,
    CONF_TRANSPORT_TYPE,
    DOMAIN,
    TRANSPORT_TYPE_BUS,
    TRANSPORT_TYPE_TRAIN,
)

_LOGGER = logging.getLogger(__name__)


async def validate_bus_config(
    hass: HomeAssistant, station_id: str, lines: list[str]
) -> dict[str, str]:
    """Validate bus configuration by testing API call.

    Args:
        hass: Home Assistant instance.
        station_id: The station ID.
        lines: List of bus line numbers.

    Returns:
        Dict with station name if successful.

    Raises:
        Exception: If validation fails.
    """
    session = async_get_clientsession(hass)
    client = IsraeliTransportClient(session)

    try:
        response = await client.get_bus_data(station_id, lines)
        return {"station_name": response.station_name}
    except Exception as err:
        _LOGGER.error("Validation failed: %s", err)
        raise


async def validate_train_config(
    hass: HomeAssistant, from_station: str, to_station: str
) -> dict[str, str]:
    """Validate train configuration by testing API call.

    Args:
        hass: Home Assistant instance.
        from_station: Departure station ID.
        to_station: Destination station ID.

    Returns:
        Dict with route info if successful.

    Raises:
        Exception: If validation fails.
    """
    session = async_get_clientsession(hass)
    client = IsraeliTransportClient(session)

    try:
        await client.get_train_data(from_station, to_station)
        return {"route": f"{from_station} -> {to_station}"}
    except Exception as err:
        _LOGGER.error("Validation failed: %s", err)
        raise


class IsraeliTransportConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Israeli Public Transport."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._transport_type: str | None = None
        self._config_data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - choose transport type.

        Args:
            user_input: User input data.

        Returns:
            FlowResult for the next step.
        """
        if user_input is not None:
            self._transport_type = user_input[CONF_TRANSPORT_TYPE]

            if self._transport_type == TRANSPORT_TYPE_BUS:
                return await self.async_step_bus()
            return await self.async_step_train()

        data_schema = vol.Schema(
            {
                vol.Required(CONF_TRANSPORT_TYPE, default=TRANSPORT_TYPE_BUS): vol.In(
                    {
                        TRANSPORT_TYPE_BUS: "Bus",
                        TRANSPORT_TYPE_TRAIN: "Train",
                    }
                ),
            }
        )

        return self.async_show_form(step_id="user", data_schema=data_schema)

    async def async_step_bus(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle bus configuration step.

        Args:
            user_input: User input data.

        Returns:
            FlowResult for creation or error.
        """
        errors = {}

        if user_input is not None:
            station_id = user_input[CONF_STATION_ID]
            lines_str = user_input[CONF_BUS_LINES]

            # Parse bus lines (comma-separated)
            try:
                lines = [line.strip() for line in lines_str.split(",")]
                if not lines:
                    errors["base"] = "no_lines"
                else:
                    # Validate configuration
                    try:
                        info = await validate_bus_config(self.hass, station_id, lines)

                        # Create unique ID
                        await self.async_set_unique_id(f"bus_{station_id}")
                        self._abort_if_unique_id_configured()

                        # Prepare configuration data
                        config_data = {
                            CONF_TRANSPORT_TYPE: TRANSPORT_TYPE_BUS,
                            CONF_STATION_ID: station_id,
                            CONF_BUS_LINES: lines,
                            CONF_ONLY_REAL_TIME: user_input.get(
                                CONF_ONLY_REAL_TIME, False
                            ),
                            CONF_CREATE_LINE_SENSORS: user_input.get(
                                CONF_CREATE_LINE_SENSORS, True
                            ),
                        }

                        return self.async_create_entry(
                            title=f"{info['station_name']} - Lines {', '.join(lines)}",
                            data=config_data,
                        )
                    except Exception:  # noqa: BLE001
                        _LOGGER.exception("Failed to validate bus configuration")
                        errors["base"] = "cannot_connect"
            except ValueError:
                errors["base"] = "invalid_lines"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_STATION_ID): str,
                vol.Required(CONF_BUS_LINES): str,
                vol.Optional(CONF_ONLY_REAL_TIME, default=False): bool,
                vol.Optional(CONF_CREATE_LINE_SENSORS, default=True): bool,
            }
        )

        return self.async_show_form(
            step_id="bus", data_schema=data_schema, errors=errors
        )

    async def async_step_train(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle train configuration step.

        Args:
            user_input: User input data.

        Returns:
            FlowResult for creation or error.
        """
        errors = {}

        if user_input is not None:
            from_station = user_input[CONF_FROM_STATION]
            to_station = user_input[CONF_TO_STATION]

            # Validate configuration
            try:
                await validate_train_config(self.hass, from_station, to_station)

                # Create unique ID
                await self.async_set_unique_id(f"train_{from_station}_{to_station}")
                self._abort_if_unique_id_configured()

                # Prepare configuration data
                config_data = {
                    CONF_TRANSPORT_TYPE: TRANSPORT_TYPE_TRAIN,
                    CONF_FROM_STATION: from_station,
                    CONF_TO_STATION: to_station,
                }

                return self.async_create_entry(
                    title=f"Train {from_station} → {to_station}",
                    data=config_data,
                )
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Failed to validate train configuration")
                errors["base"] = "cannot_connect"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_FROM_STATION): str,
                vol.Required(CONF_TO_STATION): str,
            }
        )

        return self.async_show_form(
            step_id="train", data_schema=data_schema, errors=errors
        )
