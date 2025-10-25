"""Constants for the Israeli Public Transport integration."""
from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "israeli_transport"

# API Configuration
API_BASE_URL: Final = "https://silent-be.onrender.com"
API_ENDPOINT_BUS: Final = "/busv2"
API_ENDPOINT_TRAIN: Final = "/trains"
API_TIMEOUT: Final = 10  # seconds
API_KEY_SEED: Final = "natan"

# Update Configuration
UPDATE_INTERVAL: Final = timedelta(seconds=60)
CACHE_TTL: Final = timedelta(seconds=60)
MAX_CACHE_ITEMS: Final = 100

# Configuration Keys
CONF_STATION_ID: Final = "station_id"
CONF_BUS_LINES: Final = "bus_lines"
CONF_TRANSPORT_TYPE: Final = "transport_type"
CONF_FROM_STATION: Final = "from_station"
CONF_TO_STATION: Final = "to_station"
CONF_ONLY_REAL_TIME: Final = "only_real_time"
CONF_CREATE_LINE_SENSORS: Final = "create_line_sensors"

# Transport Types
TRANSPORT_TYPE_BUS: Final = "bus"
TRANSPORT_TYPE_TRAIN: Final = "train"

# Sensor Configuration
ATTR_STATION_NAME: Final = "station_name"
ATTR_LINE_NUMBER: Final = "line_number"
ATTR_DESTINATION: Final = "destination"
ATTR_AGENCY: Final = "agency"
ATTR_REAL_TIME: Final = "real_time"
ATTR_DELAY: Final = "delay"
ATTR_ARRIVAL_TIME: Final = "arrival_time"
ATTR_ARRIVALS: Final = "arrivals"
ATTR_NEXT_ARRIVAL: Final = "next_arrival"

# Icons
ICON_BUS: Final = "mdi:bus"
ICON_TRAIN: Final = "mdi:train"
ICON_BUS_CLOCK: Final = "mdi:bus-clock"
ICON_TRAIN_CLOCK: Final = "mdi:train-clock"

# Device Classes & Units
UNIT_MINUTES: Final = "min"
