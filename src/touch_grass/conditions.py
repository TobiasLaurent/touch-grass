from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from touch_grass.config import DEFAULT_THRESHOLDS

THRESHOLDS: dict = dict(DEFAULT_THRESHOLDS)


def apply_thresholds(t: dict) -> None:
    """Replace module-level THRESHOLDS (called from CLI after config loading)."""
    global THRESHOLDS
    THRESHOLDS = t


def check_condition(value, name: str) -> tuple[bool, str]:
    """Check a single condition. Returns (is_safe, reason)."""
    if value is None:
        return False, f"{name}: data unavailable"

    if name == "temperature":
        if value < THRESHOLDS["temp_min"]:
            return False, f"Temperature too cold ({value}°C)"
        if value > THRESHOLDS["temp_max"]:
            return False, f"Temperature too hot ({value}°C)"
        return True, f"Temperature is {value}°C"

    if name == "uv_index":
        if value >= THRESHOLDS["uv_max"]:
            return False, f"UV index too high ({value})"
        return True, f"UV index is {value}"

    if name == "rain":
        if value > THRESHOLDS["rain_max"]:
            return False, f"It's raining ({value} mm)"
        return True, "No rain"

    if name == "air_quality":
        if value >= THRESHOLDS["aqi_max"]:
            return False, f"Air quality poor (EU AQI: {value})"
        return True, f"Air quality good (EU AQI: {value})"

    if name == "us_air_quality":
        if value >= THRESHOLDS["us_aqi_max"]:
            return False, f"Air quality poor (US AQI: {value})"
        return True, f"Air quality good (US AQI: {value})"

    if name == "wind_speed":
        if value >= THRESHOLDS["wind_max"]:
            return False, f"Wind too strong ({value} km/h)"
        return True, f"Wind speed is {value} km/h"

    return True, ""


def evaluate_current(weather: dict, air_quality: dict) -> dict:
    """Evaluate current conditions.

    Returns dict with:
        safe: bool
        checks: list of {name, value, safe, reason}
    """
    current = weather["current"]
    eu_aqi = air_quality["current"].get("european_aqi")
    us_aqi = air_quality["current"].get("us_aqi")

    # wind_speed and us_aqi are optional — skip rather than fail when absent
    checks_input = [
        ("temperature", current.get("temperature")),
        ("uv_index", current.get("uv_index")),
        ("rain", current.get("rain")),
        ("wind_speed", current.get("wind_speed")),
        ("air_quality", eu_aqi),
        ("us_air_quality", us_aqi),
    ]

    checks = []
    for name, value in checks_input:
        if value is None and name in ("wind_speed", "us_air_quality"):
            continue
        is_safe, reason = check_condition(value, name)
        checks.append({"name": name, "value": value, "safe": is_safe, "reason": reason})

    all_safe = all(c["safe"] for c in checks)
    return {"safe": all_safe, "checks": checks}


def _hour_is_safe(weather_hour: dict, aqi_hour: dict | None) -> bool:
    """Check if a single hourly slot is safe."""
    temp = weather_hour.get("temperature")
    uv = weather_hour.get("uv_index")
    rain = weather_hour.get("rain")
    wind = weather_hour.get("wind_speed")

    if temp is None or not (THRESHOLDS["temp_min"] <= temp <= THRESHOLDS["temp_max"]):
        return False
    if uv is None or uv >= THRESHOLDS["uv_max"]:
        return False
    if rain is None or rain > THRESHOLDS["rain_max"]:
        return False
    if wind is not None and wind >= THRESHOLDS["wind_max"]:
        return False

    if aqi_hour:
        eu = aqi_hour.get("european_aqi")
        if eu is not None and eu >= THRESHOLDS["aqi_max"]:
            return False
        us = aqi_hour.get("us_aqi")
        if us is not None and us >= THRESHOLDS["us_aqi_max"]:
            return False

    return True


def find_next_safe_window(weather: dict, air_quality: dict) -> str | None:
    """Scan hourly forecast for the next safe window.

    Returns a time string like "4:00 PM" or None if no safe window today.
    """
    tz_str = weather.get("timezone", "UTC")
    tz = ZoneInfo(tz_str)
    now = datetime.now(tz=tz)
    hourly_weather = weather["hourly"]
    hourly_aqi = {h["time"]: h for h in air_quality["hourly"]}

    for hour in hourly_weather:
        hour_time = datetime.fromisoformat(hour["time"]).replace(tzinfo=tz)
        if hour_time <= now:
            continue

        aqi_hour = hourly_aqi.get(hour["time"])
        if _hour_is_safe(hour, aqi_hour):
            return hour_time.strftime("%I:%M %p").lstrip("0")

    return None
