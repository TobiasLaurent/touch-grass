# touch-grass

A CLI tool that checks real-time conditions and tells you if it is safe to go outside and touch grass.

## What it checks

Default safety thresholds:

- **Temperature**: between -5°C and 35°C
- **UV index**: below 3
- **Rain**: 0 mm
- **Wind speed**: below 50 km/h
- **Air quality (EU AQI)**: below 50
- **Air quality (US AQI)**: below 100

If it is not safe now, the CLI scans hourly forecast data and suggests the next safe window.

## Install

### Homebrew

```bash
brew tap tobiaslaurent/touch-grass https://github.com/tobiaslaurent/touch-grass
brew install tobiaslaurent/touch-grass/touch-grass
```

### pip (local repo)

```bash
python3 -m pip install .
```

## Update

```bash
brew update
brew upgrade tobiaslaurent/touch-grass/touch-grass
```

If `brew upgrade` says `already installed` but you expect a newer version, refresh the tap metadata and retry:

```bash
brew untap tobiaslaurent/touch-grass
brew tap tobiaslaurent/touch-grass https://github.com/tobiaslaurent/touch-grass
brew update
brew upgrade tobiaslaurent/touch-grass/touch-grass
```

## Usage

```bash
touch-grass
```

Auto-detect location via IP, or provide coordinates:

```bash
touch-grass --lat 45.52 --lon -122.68
```

On first interactive run, touch-grass launches a one-time setup conversation to capture your preferred safety thresholds. You can skip it to use defaults, and rerun anytime with:

```bash
touch-grass --configure
```

For automation/agents, use machine-readable output:

```bash
touch-grass --json
```

Planning mode (next best window):

```bash
touch-grass --plan next-24h
```

Use a JSON config file for custom thresholds:

```bash
touch-grass --config ./thresholds.json
```

Example `thresholds.json`:

```json
{
  "temp_min": -10,
  "temp_max": 32,
  "uv_max": 4,
  "aqi_max": 60,
  "us_aqi_max": 120,
  "rain_max": 0,
  "wind_max": 45
}
```

Environment variables can override thresholds (and take precedence over JSON config):

- `TOUCH_GRASS_TEMP_MIN`
- `TOUCH_GRASS_TEMP_MAX`
- `TOUCH_GRASS_UV_MAX`
- `TOUCH_GRASS_AQI_MAX`
- `TOUCH_GRASS_US_AQI_MAX`
- `TOUCH_GRASS_RAIN_MAX`
- `TOUCH_GRASS_WIND_MAX`

## Development

Install with test dependencies:

```bash
python3 -m pip install -e ".[test]"
```

Run tests:

```bash
python3 -m pytest tests/ -v
```

## How it works

1. Resolves your location via [ipinfo.io](https://ipinfo.io)
2. Fetches weather, UV, and wind from [Open-Meteo Forecast API](https://open-meteo.com)
3. Fetches EU/US AQI from [Open-Meteo Air Quality API](https://air-quality-api.open-meteo.com)
4. Evaluates conditions against configurable thresholds
5. Prints a recommendation with the next safe window when available

## License

MIT
