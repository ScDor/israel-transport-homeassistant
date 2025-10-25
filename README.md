# Israeli Public Transport for Home Assistant

A Home Assistant integration for real-time Israeli bus and train arrival information.

## Features

- **Real-time Bus Arrivals**: Monitor bus arrivals at any Israeli bus station
- **Train Schedules**: Track train departures and arrivals
- **Multiple Sensor Types**:
  - Station sensors showing all configured lines
  - Individual line sensors for each bus line
- **Flexible Configuration**:
  - UI-based setup via config flow
  - YAML configuration support
- **Smart Filtering**: Option to show only real-time arrivals
- **Rich Attributes**: Detailed information including delays, agencies, destinations

## Installation

### Manual Installation

1. Copy the `custom_components/israeli_transport` directory to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Add the integration via the UI or YAML

### HACS Installation (if published)

1. Open HACS
2. Go to Integrations
3. Click the three dots menu and select "Custom repositories"
4. Add this repository URL
5. Install "Israeli Public Transport"
6. Restart Home Assistant

## Configuration

### UI Configuration (Recommended)

1. Go to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for "Israeli Public Transport"
4. Follow the configuration wizard:
   - Choose transport type (Bus or Train)
   - For buses: Enter station ID and bus lines
   - For trains: Enter departure and destination station IDs

#### Finding Station IDs

**Bus Stations:**
- Visit [https://xn--4dbclabp0e.co.il/searchStations](https://xn--4dbclabp0e.co.il/searchStations)
- Search for your station
- Copy the station ID number

**Train Stations:**
- Train station IDs typically start with 17***
- See the `silent-bus/train-stations` file for a complete list
- Example: Tel Aviv Hashalom = 17046

### YAML Configuration

While the integration supports config flow (UI setup), you can also configure it via YAML for advanced use cases.

#### Bus Example

```yaml
# This is not yet implemented - config flow only for now
# Future support planned for YAML platform configuration
```

## Sensors

### Bus Station Sensor

A main sensor for the bus station showing the next arrival across all configured lines.

**State**: Minutes until next arrival
**Attributes**:
- `station_name`: Name of the bus station
- `next_arrival`: Details of the next arriving bus
- `arrivals`: List of all upcoming arrivals

### Bus Line Sensors

Individual sensors for each configured bus line (if enabled).

**State**: Minutes until next arrival for this line
**Attributes**:
- `line_number`: Bus line number
- `station_name`: Station name
- `destination`: Where the bus is heading
- `real_time`: Whether arrival time is real-time
- `arrivals`: List of upcoming arrivals for this line

### Train Route Sensor

Sensor showing train schedule for a specific route.

**State**: Minutes until next train departure
**Attributes**:
- `next_arrival`: Details of the next train
- `arrivals`: List of upcoming trains
- `departure_time`: When the train departs
- `arrival_time`: When the train arrives
- `platform`: Platform number (if available)

## Examples

### Lovelace Card Example

```yaml
type: entities
title: Bus 24068
entities:
  - entity: sensor.tel_aviv_savidor_derech_namir
  - entity: sensor.tel_aviv_savidor_derech_namir_line_40
  - entity: sensor.tel_aviv_savidor_derech_namir_line_249
  - entity: sensor.tel_aviv_savidor_derech_namir_line_605
```

### Automation Example

```yaml
automation:
  - alias: "Notify when bus is arriving"
    trigger:
      - platform: numeric_state
        entity_id: sensor.tel_aviv_savidor_derech_namir_line_40
        below: 5
    action:
      - service: notify.mobile_app
        data:
          title: "Bus Arriving Soon"
          message: "Line 40 arriving in {{ states('sensor.tel_aviv_savidor_derech_namir_line_40') }} minutes"
```

## API

This integration uses the silent-bus API (`https://silent-be.onrender.com`) which provides real-time Israeli public transportation data.

### API Endpoints

- **Bus**: `/busv2?station=STATION_ID&lines=LINE1,LINE2`
- **Train**: `/trains?fromStation=FROM_ID&toStation=TO_ID`

### Authentication

The API uses a daily rotating XOR-encrypted key based on the current date. This is handled automatically by the integration.

### Rate Limiting

- Data is cached for 60 seconds
- Automatic updates every 60 seconds
- Maximum 100 cached requests

## Troubleshooting

### Integration not appearing

- Check that you've copied the files to `custom_components/israeli_transport`
- Restart Home Assistant
- Check logs for any errors

### No data or "Unavailable"

- Verify your station ID is correct
- Check that bus lines are valid for that station
- Ensure you have internet connectivity
- Check Home Assistant logs for API errors

### Enable Debug Logging

Add to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.israeli_transport: debug
```

## Credits

This integration is based on the [silent-bus](https://github.com/silentbil/silent-bus) project by @silentbil, which provides a Lovelace card for Israeli public transport.

Special thanks to:
- @silentbil for the original API and frontend card
- The Israeli public transport API providers

## License

MIT License - See LICENSE file for details

## Support

For issues, feature requests, or questions:
- Open an issue on [GitHub](https://github.com/dor/israel-transport-homeassistant/issues)
- Check existing issues for solutions

## Changelog

### Version 2.0.0
- Complete rewrite of the integration
- Added train support
- Implemented config flow (UI setup)
- Added individual line sensors
- Improved error handling and caching
- Better sensor attributes and data structure
