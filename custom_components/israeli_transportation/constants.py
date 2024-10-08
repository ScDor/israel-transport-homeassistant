import json
from pathlib import Path

integration_folder = Path(__file__).parent

with (integration_folder / "manifest.json").open() as f:
    _mainfest = json.load(f)

DOMAIN = integration_folder.name
INTEGRATION_NAME = _mainfest["name"]
SENSOR = "sensor"
CONF_BUS_LINES = "bus_lines"
CONF_NAME = "name"
CONF_BUS_STATION_ID = "station_id"
CONF_ONLY_REAL_TIME = "only_real_time"
CONF_STATIONS = "stations"
TITLE_BUS_SENSOR = "Bus ETA Sensor"
