from client.client import Client
from client.models.bus_response import BusArrivalData, BusResponse
from homeassistant.components.sensor import SensorEntity
from loguru import logger


class BusArrivalSensor(SensorEntity):
    def __init__(
        self, station_number: int, line_numbers: list[int], only_real_time: bool
    ):
        self._station_number: int = station_number
        self._bus_lines: list[int] = line_numbers
        self._only_real_time: bool = only_real_time

        self._state: int | None = None
        self._attributes: dict | None = None

    @property
    def line_numbers_string(self) -> str:
        return ",".join(sorted(map(str, self._bus_lines)))

    @property
    def name(self) -> str:
        line_word = "line" if len(self._bus_lines) == 1 else "lines"
        return f"{line_word} {self.line_numbers_string} ETA in stop #{self._station_number}"

    @property
    def state(self) -> int | None:
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
        try:
            response = await Client.get_bus_data(
                station=self._station_number, lines=self._bus_lines
            )
        except Exception:  # noqa: BLE001
            logger.exception()
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
            self.set_state(earliest_real_time_arrival.real_time_arrives_in)
