import homeassistant.helpers.config_validation as cv
from homeassistant import config_entries
from homeassistant.const import CONF_SCAN_INTERVAL

from .constants import CONF_BUS_LINES, CONF_BUS_STATION_ID, DOMAIN, TITLE_BUS_SENSOR


class BusSensorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input: dict | None = None):
        if user_input is not None:
            return self.async_create_entry(
                title=user_input.get("title", TITLE_BUS_SENSOR), data=user_input
            )

        return self.async_show_form(
            step_id="user",
            # data_schema=vol.Schema(
            #     {
            #         vol.Optional("title", default=TITLE_BUS_SENSOR): str,
            #         vol.Required(CONF_SCAN_INTERVAL, default=90): cv.positive_int,
            #         vol.Required(CONF_BUS_STATION_ID): str,
            #         vol.Required(CONF_BUS_LINES): cv.ensure_list,
            #     }
            ),
        )
