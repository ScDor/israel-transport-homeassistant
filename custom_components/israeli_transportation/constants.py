import json
from pathlib import Path

with Path(__file__).with_name("manifest.json").open() as f:
    _mainfest = json.load(f)

INTEGRATION_NAME = _mainfest["name"]
DOMAIN = _mainfest["domain"]
DOMAIN_SENSOR = "sensor"
CONF_BUS_LINES = "bus_lines"
CONF_BUS_STATION_ID = "station_id"
TITLE_BUS_SENSOR = "Bus Sensor"
