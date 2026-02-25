from __future__ import annotations

import json
import os
from pathlib import Path

DEFAULT_THRESHOLDS = {
    "temp_min": -5,      # °C
    "temp_max": 35,      # °C
    "uv_max": 3,         # UV index
    "aqi_max": 50,       # EU AQI (Good)
    "us_aqi_max": 100,   # US AQI (Moderate threshold)
    "rain_max": 0,       # mm
    "wind_max": 50,      # km/h (Beaufort 7 near-gale)
}

_ENV_MAP = {
    "TOUCH_GRASS_TEMP_MIN": ("temp_min", float),
    "TOUCH_GRASS_TEMP_MAX": ("temp_max", float),
    "TOUCH_GRASS_UV_MAX": ("uv_max", float),
    "TOUCH_GRASS_AQI_MAX": ("aqi_max", int),
    "TOUCH_GRASS_US_AQI_MAX": ("us_aqi_max", int),
    "TOUCH_GRASS_RAIN_MAX": ("rain_max", float),
    "TOUCH_GRASS_WIND_MAX": ("wind_max", float),
}


def load_thresholds(config_path: str | None = None) -> dict:
    """Return merged thresholds: defaults < JSON file < env vars."""
    thresholds = dict(DEFAULT_THRESHOLDS)

    if config_path is not None:
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        with path.open() as f:
            file_data = json.load(f)
        for key in DEFAULT_THRESHOLDS:
            if key in file_data:
                thresholds[key] = type(DEFAULT_THRESHOLDS[key])(file_data[key])

    for env_key, (threshold_key, cast) in _ENV_MAP.items():
        val = os.environ.get(env_key)
        if val is not None:
            try:
                thresholds[threshold_key] = cast(val)
            except ValueError:
                raise ValueError(f"Invalid value for {env_key}: {val!r}")

    return thresholds
