import requests

from touch_grass.cache import cached_call


def get_weather(latitude: float, longitude: float) -> dict:
    """Fetch current conditions and hourly forecast from Open-Meteo.

    Returns dict with:
        current: {temperature, rain, uv_index, wind_speed}
        hourly: [{time, temperature, rain, uv_index, wind_speed}, ...]
        timezone: str
    """
    key = f"weather:{latitude}:{longitude}"
    return cached_call(key, lambda: _fetch_weather(latitude, longitude))


def _fetch_weather(latitude: float, longitude: float) -> dict:
    resp = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,rain,uv_index,windspeed_10m",
            "hourly": "temperature_2m,rain,uv_index,windspeed_10m",
            "forecast_days": 1,
            "timezone": "auto",
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    current = data["current"]
    hourly = data["hourly"]

    hourly_list = [
        {"time": t, "temperature": temp, "rain": r, "uv_index": uv, "wind_speed": ws}
        for t, temp, r, uv, ws in zip(
            hourly["time"],
            hourly["temperature_2m"],
            hourly["rain"],
            hourly["uv_index"],
            hourly["windspeed_10m"],
        )
    ]

    return {
        "current": {
            "temperature": current["temperature_2m"],
            "rain": current["rain"],
            "uv_index": current["uv_index"],
            "wind_speed": current["windspeed_10m"],
        },
        "hourly": hourly_list,
        "timezone": data.get("timezone", "UTC"),
    }


def get_air_quality(latitude: float, longitude: float) -> dict:
    """Fetch current and hourly air quality from Open-Meteo.

    Returns dict with:
        current: {european_aqi, us_aqi}
        hourly: [{time, european_aqi, us_aqi}, ...]
    """
    key = f"air_quality:{latitude}:{longitude}"
    return cached_call(key, lambda: _fetch_air_quality(latitude, longitude))


def _fetch_air_quality(latitude: float, longitude: float) -> dict:
    resp = requests.get(
        "https://air-quality-api.open-meteo.com/v1/air-quality",
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": "european_aqi,us_aqi",
            "hourly": "european_aqi,us_aqi",
            "forecast_days": 1,
            "timezone": "auto",
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    current_eu_aqi = data["current"].get("european_aqi")
    current_us_aqi = data["current"].get("us_aqi")
    hourly = data["hourly"]

    times = hourly["time"]
    eu_values = hourly.get("european_aqi", [None] * len(times))
    us_values = hourly.get("us_aqi", [None] * len(times))

    hourly_list = [
        {"time": t, "european_aqi": eu, "us_aqi": us}
        for t, eu, us in zip(times, eu_values, us_values)
    ]

    return {
        "current": {"european_aqi": current_eu_aqi, "us_aqi": current_us_aqi},
        "hourly": hourly_list,
    }
