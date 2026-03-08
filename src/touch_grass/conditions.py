from __future__ import annotations

from collections import Counter
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


def forecast_days(weather: dict, air_quality: dict, days: int) -> list[dict]:
    """Return a compact day-by-day forecast evaluation for the next N days."""
    tz_str = weather.get("timezone", "UTC")
    tz = ZoneInfo(tz_str)
    hourly_weather = weather["hourly"]
    hourly_aqi = {h["time"]: h for h in air_quality["hourly"]}

    by_day: dict[str, list[tuple[dict, dict | None]]] = {}
    for hour in hourly_weather:
        day_key = hour["time"].split("T", 1)[0]
        by_day.setdefault(day_key, []).append((hour, hourly_aqi.get(hour["time"])))

    summaries: list[dict] = []
    for day_key in sorted(by_day.keys())[:days]:
        rows = by_day[day_key]
        safe_hours = []
        blocker_counts: Counter[str] = Counter()
        representative = rows[0][0]
        peak_uv = max((row[0].get("uv_index") or 0) for row in rows)
        max_temp = max((row[0].get("temperature") for row in rows if row[0].get("temperature") is not None), default=None)
        min_temp = min((row[0].get("temperature") for row in rows if row[0].get("temperature") is not None), default=None)
        max_rain = max((row[0].get("rain") or 0) for row in rows)
        max_wind = max((row[0].get("wind_speed") or 0) for row in rows)
        peak_eu_aqi = max((aq.get("european_aqi") for _, aq in rows if aq and aq.get("european_aqi") is not None), default=None)
        peak_us_aqi = max((aq.get("us_aqi") for _, aq in rows if aq and aq.get("us_aqi") is not None), default=None)

        for hour, aqi in rows:
            if _hour_is_safe(hour, aqi):
                safe_hours.append(hour["time"])
            else:
                if hour.get("temperature") is None or not (THRESHOLDS["temp_min"] <= hour.get("temperature") <= THRESHOLDS["temp_max"]):
                    blocker_counts["temperature"] += 1
                if hour.get("uv_index") is None or hour.get("uv_index") >= THRESHOLDS["uv_max"]:
                    blocker_counts["uv_index"] += 1
                if hour.get("rain") is None or hour.get("rain") > THRESHOLDS["rain_max"]:
                    blocker_counts["rain"] += 1
                if hour.get("wind_speed") is not None and hour.get("wind_speed") >= THRESHOLDS["wind_max"]:
                    blocker_counts["wind_speed"] += 1
                if aqi and aqi.get("european_aqi") is not None and aqi.get("european_aqi") >= THRESHOLDS["aqi_max"]:
                    blocker_counts["air_quality"] += 1
                if aqi and aqi.get("us_aqi") is not None and aqi.get("us_aqi") >= THRESHOLDS["us_aqi_max"]:
                    blocker_counts["us_air_quality"] += 1

        dt = datetime.fromisoformat(f"{day_key}T00:00:00").replace(tzinfo=tz)
        best_window = None
        if safe_hours:
            best_window = datetime.fromisoformat(safe_hours[0]).replace(tzinfo=tz).strftime("%I:%M %p").lstrip("0")

        summaries.append({
            "date": day_key,
            "weekday": dt.strftime("%A"),
            "safe": len(safe_hours) > 0,
            "best_window": best_window,
            "safe_hour_count": len(safe_hours),
            "primary_blockers": [name for name, _ in blocker_counts.most_common(2)],
            "metrics": {
                "min_temp": min_temp,
                "max_temp": max_temp,
                "peak_uv": peak_uv,
                "max_rain": max_rain,
                "max_wind": max_wind,
                "peak_eu_aqi": peak_eu_aqi,
                "peak_us_aqi": peak_us_aqi,
            },
        })

    return summaries


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
