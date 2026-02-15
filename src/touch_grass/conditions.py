from __future__ import annotations

from datetime import datetime

THRESHOLDS = {
    "temp_min": -5,      # °C
    "temp_max": 35,      # °C
    "uv_max": 4,         # UV index
    "aqi_max": 50,       # EU AQI (Good)
    "rain_max": 0,       # mm
}


def check_condition(value, name: str) -> tuple[bool, str]:
    """Check a single condition. Returns (is_safe, reason)."""
    if value is None:
        return True, f"{name}: no data available"

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

    return True, ""


def evaluate_current(weather: dict, air_quality: dict) -> dict:
    """Evaluate current conditions.

    Returns dict with:
        safe: bool
        checks: list of {name, value, safe, reason}
    """
    current = weather["current"]
    aqi = air_quality["current"]["european_aqi"]

    checks = []
    for name, value in [
        ("temperature", current["temperature"]),
        ("uv_index", current["uv_index"]),
        ("rain", current["rain"]),
        ("air_quality", aqi),
    ]:
        is_safe, reason = check_condition(value, name)
        checks.append({"name": name, "value": value, "safe": is_safe, "reason": reason})

    all_safe = all(c["safe"] for c in checks)
    return {"safe": all_safe, "checks": checks}


def _hour_is_safe(weather_hour: dict, aqi_hour: dict | None) -> bool:
    """Check if a single hourly slot is safe."""
    temp = weather_hour["temperature"]
    uv = weather_hour["uv_index"]
    rain = weather_hour["rain"]

    if not (THRESHOLDS["temp_min"] <= temp <= THRESHOLDS["temp_max"]):
        return False
    if uv >= THRESHOLDS["uv_max"]:
        return False
    if rain > THRESHOLDS["rain_max"]:
        return False
    if aqi_hour and aqi_hour["european_aqi"] is not None:
        if aqi_hour["european_aqi"] >= THRESHOLDS["aqi_max"]:
            return False
    return True


def find_next_safe_window(weather: dict, air_quality: dict) -> str | None:
    """Scan hourly forecast for the next safe window.

    Returns a time string like "4:00 PM" or None if no safe window today.
    """
    now = datetime.now()
    hourly_weather = weather["hourly"]
    hourly_aqi = {h["time"]: h for h in air_quality["hourly"]}

    for hour in hourly_weather:
        hour_time = datetime.fromisoformat(hour["time"])
        if hour_time <= now:
            continue

        aqi_hour = hourly_aqi.get(hour["time"])
        if _hour_is_safe(hour, aqi_hour):
            return hour_time.strftime("%I:%M %p").lstrip("0")

    return None
