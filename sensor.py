import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import Entity
import voluptuous as vol

from loguru import logger
from client import Client
from models.bus_response import BusArrivalData, BusResponse

# Schema for configuration
PLATFORM_SCHEMA = cv.PLATFORM_SCHEMA.extend(
    {
        vol.Required("station_number"): cv.string,
        vol.Required("bus_line_numbers"): vol.All(cv.ensure_list, [cv.string]),
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    station_number = config["station_number"]
    bus_line_numbers = config["bus_line_numbers"]
    sensors = [BusArrivalSensor(station_number, line) for line in bus_line_numbers]
    async_add_entities(sensors)


class BusArrivalSensor(SensorEntity):
    def __init__(
        self,
        station_number: int,
        line_numbers: list[int],
        only_real_time: bool,
    ):
        self._station_number = station_number
        self._bus_lines = line_numbers
        self._only_real_time = only_real_time

        self._state = None
        self._attributes = None

    @property
    def line_numbers_string(self) -> str:
        return ",".join(sorted(self._bus_lines))

    @property
    def name(self):
        line_word = "line" if len(self._bus_lines) == 1 else "lines"
        return f"ETA for bus {line_word} {self.line_numbers_string} ETA in station #{self._station_number}"

    @property
    def state(self):
        return self._state

    def set_state(self, earliest_arrival: int | None):
        logger.debug(f"previous {self.state=}")
        self._state = earliest_arrival
        logger.info(f"set {self.state=}")

    def clear_state(self):
        self.set_state(None)

    def set_attributes(self, response: BusResponse):
        self._attributes = response.__dict__

    async def async_update(self):
        response = await Client.get_bus_data(
            station=self._station_number, lines=self._bus_lines
        )
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
            else:
                logger.warning(message)

        self.set_attributes(response)

        earliest_real_time_arrival: BusArrivalData | None = min(
            real_time,
            key=lambda datum: datum.real_time_arrives_in,
            default=None,
        )
        if earliest_real_time_arrival:
            self.set_state(earliest_real_time_arrival.real_time_arrives_in)
