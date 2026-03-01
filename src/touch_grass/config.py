from __future__ import annotations

import json
import os
from pathlib import Path

import click

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

def _config_dir() -> Path:
    return Path(os.environ.get("TOUCH_GRASS_CONFIG_DIR", Path.home() / ".config" / "touch-grass"))


def _user_thresholds_path() -> Path:
    return _config_dir() / "thresholds.json"


def _apply_thresholds_from_dict(target: dict, source: dict) -> None:
    for key in DEFAULT_THRESHOLDS:
        if key in source:
            target[key] = type(DEFAULT_THRESHOLDS[key])(source[key])


def has_user_thresholds() -> bool:
    path = _user_thresholds_path()
    return path.exists() and path.is_file()


def save_user_thresholds(thresholds: dict) -> None:
    cfg_dir = _config_dir()
    cfg_dir.mkdir(parents=True, exist_ok=True)
    with _user_thresholds_path().open("w") as f:
        json.dump({k: thresholds[k] for k in DEFAULT_THRESHOLDS}, f, indent=2)


def run_first_time_setup() -> dict:
    """Interactive setup for safety thresholds. Returns selected thresholds and persists them."""
    click.echo("\nWelcome to touch-grass setup 🌱")
    click.echo("Set your personal safety thresholds once now.")
    click.echo("Tip: choose 'skip' to keep defaults. You can rerun with --configure.\n")

    if click.confirm("Skip setup and use defaults?", default=False):
        thresholds = dict(DEFAULT_THRESHOLDS)
        save_user_thresholds(thresholds)
        return thresholds

    thresholds = dict(DEFAULT_THRESHOLDS)

    thresholds["temp_min"] = click.prompt("Minimum temperature (°C)", type=float, default=DEFAULT_THRESHOLDS["temp_min"])
    thresholds["temp_max"] = click.prompt("Maximum temperature (°C)", type=float, default=DEFAULT_THRESHOLDS["temp_max"])
    thresholds["uv_max"] = click.prompt("Maximum UV index", type=float, default=DEFAULT_THRESHOLDS["uv_max"])
    thresholds["aqi_max"] = click.prompt("Maximum EU AQI", type=int, default=DEFAULT_THRESHOLDS["aqi_max"])
    thresholds["us_aqi_max"] = click.prompt("Maximum US AQI", type=int, default=DEFAULT_THRESHOLDS["us_aqi_max"])
    thresholds["rain_max"] = click.prompt("Maximum rain (mm)", type=float, default=DEFAULT_THRESHOLDS["rain_max"])
    thresholds["wind_max"] = click.prompt("Maximum wind speed (km/h)", type=float, default=DEFAULT_THRESHOLDS["wind_max"])

    save_user_thresholds(thresholds)
    click.echo("\nSaved. You can change this anytime with: touch-grass --configure\n")
    return thresholds


def load_thresholds(config_path: str | None = None) -> dict:
    """Return merged thresholds: defaults < user config < JSON file < env vars."""
    thresholds = dict(DEFAULT_THRESHOLDS)

    if has_user_thresholds():
        with _user_thresholds_path().open() as f:
            user_data = json.load(f)
        _apply_thresholds_from_dict(thresholds, user_data)

    if config_path is not None:
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        if not path.is_file():
            raise ValueError(f"Config path is not a file: {config_path}")
        with path.open() as f:
            file_data = json.load(f)
        _apply_thresholds_from_dict(thresholds, file_data)

    for env_key, (threshold_key, cast) in _ENV_MAP.items():
        val = os.environ.get(env_key)
        if val is not None:
            try:
                thresholds[threshold_key] = cast(val)
            except ValueError:
                raise ValueError(f"Invalid value for {env_key}: {val!r}")

    return thresholds
