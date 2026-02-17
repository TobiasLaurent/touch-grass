# touch-grass

A CLI tool that checks real-time weather, UV, and air quality conditions to tell you if it's safe to go outside and touch grass.

## What it checks

- **Temperature** — between -5°C and 35°C
- **UV index** — below 4
- **Rain** — none
- **Air quality** — EU AQI below 50 (Good)

If conditions aren't safe right now, it scans the hourly forecast and suggests the next safe window.

## Install

### Homebrew

```
brew tap tobiaslaurent/touch-grass https://github.com/tobiaslaurent/touch-grass
brew install touch-grass
```

Notes:
- First install may take a few minutes because Homebrew installs Python and builds a virtual environment for the CLI.
- Upgrades are usually faster once dependencies are already present.

### pip

```
python3 -m pip install .
```

## Troubleshooting

If Homebrew fails with an old source URL (for example a `files.pythonhosted.org` `touch_grass-0.1.0.tar.gz` error), refresh your tap metadata and reinstall:

```
brew update
brew untap tobiaslaurent/touch-grass
brew tap tobiaslaurent/touch-grass https://github.com/tobiaslaurent/touch-grass
brew reinstall touch-grass
```

## Usage

```
touch-grass
```

The tool auto-detects your location via IP geolocation. To specify coordinates manually:

```
touch-grass --lat 45.52 --lon -122.68
```

## Development

Install with test dependencies:

```
pip install -e ".[test]"
```

Run tests:

```
python3 -m pytest tests/ -v
```

## How it works

1. Resolves your location via [ipinfo.io](https://ipinfo.io)
2. Fetches weather and UV data from [Open-Meteo](https://open-meteo.com)
3. Fetches air quality data from [Open-Meteo Air Quality API](https://air-quality-api.open-meteo.com)
4. Evaluates all conditions against safe thresholds
5. Tells you to go touch grass or keep coding

## License

MIT
