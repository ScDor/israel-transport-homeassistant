"""Sensor platform for Israeli Public Transport."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import BusArrival, BusResponse, TrainArrival, TrainResponse
from .const import (
    ATTR_AGENCY,
    ATTR_ARRIVAL_TIME,
    ATTR_ARRIVALS,
    ATTR_DELAY,
    ATTR_DESTINATION,
    ATTR_LINE_NUMBER,
    ATTR_NEXT_ARRIVAL,
    ATTR_REAL_TIME,
    ATTR_STATION_NAME,
    CONF_BUS_LINES,
    CONF_CREATE_LINE_SENSORS,
    CONF_ONLY_REAL_TIME,
    DOMAIN,
    ICON_BUS,
    ICON_BUS_CLOCK,
    ICON_TRAIN,
    ICON_TRAIN_CLOCK,
    TRANSPORT_TYPE_BUS,
    TRANSPORT_TYPE_TRAIN,
    UNIT_MINUTES,
)
from .coordinator import IsraeliTransportCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform.

    Args:
        hass: Home Assistant instance.
        entry: The config entry.
        async_add_entities: Callback to add entities.
    """
    coordinator: IsraeliTransportCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []

    # Always create a main station/route sensor
    if coordinator.transport_type == TRANSPORT_TYPE_BUS:
        entities.append(BusStationSensor(coordinator, entry))

        # Create individual line sensors if configured
        if entry.data.get(CONF_CREATE_LINE_SENSORS, True):
            for line in entry.data[CONF_BUS_LINES]:
                entities.append(BusLineSensor(coordinator, entry, str(line)))
    else:
        entities.append(TrainRouteSensor(coordinator, entry))

    async_add_entities(entities)


def _format_minutes(seconds: float) -> int | None:
    """Convert seconds to minutes.

    Args:
        seconds: Time in seconds.

    Returns:
        Time in minutes, rounded up, or None if negative.
    """
    if seconds < 0:
        return None
    return int(seconds / 60) + (1 if seconds % 60 > 0 else 0)


class BusStationSensor(CoordinatorEntity[IsraeliTransportCoordinator], SensorEntity):
    """Sensor representing a bus station with all configured lines."""

    _attr_has_entity_name = True
    _attr_icon = ICON_BUS_CLOCK
    _attr_native_unit_of_measurement = UNIT_MINUTES

    def __init__(
        self, coordinator: IsraeliTransportCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor.

        Args:
            coordinator: The data coordinator.
            entry: The config entry.
        """
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_station"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        if isinstance(self.coordinator.data.data, BusResponse):
            station_name = self.coordinator.data.data.station_name
            return f"{station_name}"
        return "Bus Station"

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor (minutes until next arrival)."""
        arrivals = self._get_filtered_arrivals()
        if not arrivals:
            return None

        # Return minutes until the next arrival
        next_arrival = arrivals[0]
        return _format_minutes(next_arrival.real_time_arrives_in)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        arrivals = self._get_filtered_arrivals()

        attributes = {
            ATTR_STATION_NAME: (
                self.coordinator.data.data.station_name
                if isinstance(self.coordinator.data.data, BusResponse)
                else "Unknown"
            ),
            ATTR_ARRIVALS: [
                {
                    ATTR_LINE_NUMBER: arrival.line_number,
                    ATTR_DESTINATION: arrival.destination,
                    ATTR_ARRIVAL_TIME: arrival.real_time_arrives_at.isoformat(),
                    ATTR_REAL_TIME: arrival.is_real_time,
                    ATTR_AGENCY: arrival.agency,
                    ATTR_DELAY: arrival.real_time_arrival_delay,
                    "arrives_in_seconds": arrival.real_time_arrives_in,
                    "arrives_in_minutes": _format_minutes(
                        arrival.real_time_arrives_in
                    ),
                }
                for arrival in arrivals
            ],
        }

        if arrivals:
            next_arrival = arrivals[0]
            attributes[ATTR_NEXT_ARRIVAL] = {
                ATTR_LINE_NUMBER: next_arrival.line_number,
                ATTR_DESTINATION: next_arrival.destination,
                ATTR_ARRIVAL_TIME: next_arrival.real_time_arrives_at.isoformat(),
                "arrives_in_minutes": _format_minutes(
                    next_arrival.real_time_arrives_in
                ),
            }

        return attributes

    def _get_filtered_arrivals(self) -> list[BusArrival]:
        """Get filtered list of bus arrivals.

        Returns:
            List of BusArrival objects, filtered and sorted.
        """
        if not isinstance(self.coordinator.data.data, BusResponse):
            return []

        arrivals = self.coordinator.data.data.bus_data

        # Filter by real-time if configured
        only_real_time = self._entry.data.get(CONF_ONLY_REAL_TIME, False)
        if only_real_time:
            arrivals = [a for a in arrivals if a.is_real_time]

        # Sort by arrival time
        arrivals = sorted(arrivals, key=lambda x: x.real_time_arrives_in)

        return arrivals


class BusLineSensor(CoordinatorEntity[IsraeliTransportCoordinator], SensorEntity):
    """Sensor representing a specific bus line."""

    _attr_has_entity_name = True
    _attr_icon = ICON_BUS
    _attr_native_unit_of_measurement = UNIT_MINUTES

    def __init__(
        self, coordinator: IsraeliTransportCoordinator, entry: ConfigEntry, line: str
    ) -> None:
        """Initialize the sensor.

        Args:
            coordinator: The data coordinator.
            entry: The config entry.
            line: The bus line number.
        """
        super().__init__(coordinator)
        self._entry = entry
        self._line = line
        self._attr_unique_id = f"{entry.entry_id}_line_{line}"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        if isinstance(self.coordinator.data.data, BusResponse):
            station_name = self.coordinator.data.data.station_name
            return f"{station_name} - Line {self._line}"
        return f"Line {self._line}"

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor (minutes until next arrival)."""
        arrivals = self._get_line_arrivals()
        if not arrivals:
            return None

        # Return minutes until the next arrival for this line
        return _format_minutes(arrivals[0].real_time_arrives_in)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        arrivals = self._get_line_arrivals()

        attributes = {
            ATTR_LINE_NUMBER: self._line,
            ATTR_STATION_NAME: (
                self.coordinator.data.data.station_name
                if isinstance(self.coordinator.data.data, BusResponse)
                else "Unknown"
            ),
            ATTR_ARRIVALS: [
                {
                    ATTR_DESTINATION: arrival.destination,
                    ATTR_ARRIVAL_TIME: arrival.real_time_arrives_at.isoformat(),
                    ATTR_REAL_TIME: arrival.is_real_time,
                    ATTR_AGENCY: arrival.agency,
                    ATTR_DELAY: arrival.real_time_arrival_delay,
                    "arrives_in_seconds": arrival.real_time_arrives_in,
                    "arrives_in_minutes": _format_minutes(
                        arrival.real_time_arrives_in
                    ),
                }
                for arrival in arrivals
            ],
        }

        if arrivals:
            attributes[ATTR_DESTINATION] = arrivals[0].destination
            attributes[ATTR_REAL_TIME] = arrivals[0].is_real_time

        return attributes

    def _get_line_arrivals(self) -> list[BusArrival]:
        """Get arrivals for this specific line.

        Returns:
            List of BusArrival objects for this line.
        """
        if not isinstance(self.coordinator.data.data, BusResponse):
            return []

        # Filter arrivals for this line
        arrivals = [
            a
            for a in self.coordinator.data.data.bus_data
            if a.line_number == self._line
        ]

        # Filter by real-time if configured
        only_real_time = self._entry.data.get(CONF_ONLY_REAL_TIME, False)
        if only_real_time:
            arrivals = [a for a in arrivals if a.is_real_time]

        # Sort by arrival time
        arrivals = sorted(arrivals, key=lambda x: x.real_time_arrives_in)

        return arrivals


class TrainRouteSensor(CoordinatorEntity[IsraeliTransportCoordinator], SensorEntity):
    """Sensor representing a train route."""

    _attr_has_entity_name = True
    _attr_icon = ICON_TRAIN_CLOCK
    _attr_native_unit_of_measurement = UNIT_MINUTES

    def __init__(
        self, coordinator: IsraeliTransportCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the sensor.

        Args:
            coordinator: The data coordinator.
            entry: The config entry.
        """
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_train"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return "Train Schedule"

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor (minutes until next train)."""
        arrivals = self._get_upcoming_trains()
        if not arrivals:
            return None

        # Calculate minutes until departure
        now = datetime.now(arrivals[0].departure_time.tzinfo)
        minutes_until = (arrivals[0].departure_time - now).total_seconds() / 60
        return int(minutes_until) if minutes_until >= 0 else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        arrivals = self._get_upcoming_trains()

        attributes = {
            ATTR_ARRIVALS: [
                {
                    "departure_time": arrival.departure_time.isoformat(),
                    "arrival_time": arrival.arrival_time.isoformat(),
                    "platform": arrival.platform,
                    "train_number": arrival.train_number,
                }
                for arrival in arrivals
            ],
        }

        if arrivals:
            next_train = arrivals[0]
            now = datetime.now(next_train.departure_time.tzinfo)
            minutes_until = (next_train.departure_time - now).total_seconds() / 60

            attributes[ATTR_NEXT_ARRIVAL] = {
                "departure_time": next_train.departure_time.isoformat(),
                "arrival_time": next_train.arrival_time.isoformat(),
                "platform": next_train.platform,
                "minutes_until_departure": int(minutes_until)
                if minutes_until >= 0
                else 0,
            }

        return attributes

    def _get_upcoming_trains(self) -> list[TrainArrival]:
        """Get upcoming trains.

        Returns:
            List of TrainArrival objects, sorted by departure time.
        """
        if not isinstance(self.coordinator.data.data, TrainResponse):
            return []

        now = datetime.now()
        upcoming = [
            train
            for train in self.coordinator.data.data.trains
            if train.departure_time.replace(tzinfo=None) > now
        ]

        return sorted(upcoming, key=lambda x: x.departure_time)
