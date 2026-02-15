import requests


def get_weather(latitude: float, longitude: float) -> dict:
    """Fetch current conditions and hourly forecast from Open-Meteo.

    Returns dict with:
        current: {temperature, rain, uv_index}
        hourly: [{time, temperature, rain, uv_index}, ...]
    """
    resp = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,rain,uv_index",
            "hourly": "temperature_2m,rain,uv_index",
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
        {"time": t, "temperature": temp, "rain": r, "uv_index": uv}
        for t, temp, r, uv in zip(
            hourly["time"], hourly["temperature_2m"], hourly["rain"], hourly["uv_index"]
        )
    ]

    return {
        "current": {
            "temperature": current["temperature_2m"],
            "rain": current["rain"],
            "uv_index": current["uv_index"],
        },
        "hourly": hourly_list,
        "timezone": data.get("timezone", "UTC"),
    }


def get_air_quality(latitude: float, longitude: float) -> dict:
    """Fetch current and hourly air quality from Open-Meteo.

    Returns dict with:
        current: {european_aqi}
        hourly: [{time, european_aqi}, ...]
    """
    resp = requests.get(
        "https://air-quality-api.open-meteo.com/v1/air-quality",
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": "european_aqi",
            "hourly": "european_aqi",
            "forecast_days": 1,
            "timezone": "auto",
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    current_aqi = data["current"]["european_aqi"]
    hourly = data["hourly"]

    hourly_list = [
        {"time": t, "european_aqi": aqi}
        for t, aqi in zip(hourly["time"], hourly["european_aqi"])
    ]

    return {
        "current": {"european_aqi": current_aqi},
        "hourly": hourly_list,
    }
