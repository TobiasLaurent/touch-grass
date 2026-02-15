from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import patch

from touch_grass.conditions import (
    _hour_is_safe,
    check_condition,
    evaluate_current,
    find_next_safe_window,
)


# --- check_condition ---


def test_check_condition_none_value():
    safe, reason = check_condition(None, "temperature")
    assert safe is True
    assert "no data" in reason


def test_check_condition_temp_safe():
    safe, reason = check_condition(20, "temperature")
    assert safe is True
    assert "20°C" in reason


def test_check_condition_temp_too_cold():
    safe, reason = check_condition(-5, "temperature")
    assert safe is False
    assert "too cold" in reason


def test_check_condition_temp_too_hot():
    safe, reason = check_condition(40, "temperature")
    assert safe is False
    assert "too hot" in reason


def test_check_condition_uv_safe():
    safe, reason = check_condition(2, "uv_index")
    assert safe is True


def test_check_condition_uv_high():
    safe, reason = check_condition(5, "uv_index")
    assert safe is False
    assert "too high" in reason


def test_check_condition_rain_none():
    safe, reason = check_condition(0, "rain")
    assert safe is True
    assert "No rain" in reason


def test_check_condition_rain_yes():
    safe, reason = check_condition(2.5, "rain")
    assert safe is False
    assert "raining" in reason


def test_check_condition_aqi_good():
    safe, reason = check_condition(30, "air_quality")
    assert safe is True
    assert "good" in reason


def test_check_condition_aqi_poor():
    safe, reason = check_condition(60, "air_quality")
    assert safe is False
    assert "poor" in reason


# --- evaluate_current ---


def _make_data(temp=20, uv=2, rain=0, aqi=30):
    weather = {"current": {"temperature": temp, "uv_index": uv, "rain": rain}}
    air_quality = {"current": {"european_aqi": aqi}}
    return weather, air_quality


def test_evaluate_current_all_safe():
    result = evaluate_current(*_make_data())
    assert result["safe"] is True
    assert len(result["checks"]) == 4


def test_evaluate_current_one_unsafe():
    result = evaluate_current(*_make_data(temp=-5))
    assert result["safe"] is False
    unsafe = [c for c in result["checks"] if not c["safe"]]
    assert len(unsafe) == 1
    assert unsafe[0]["name"] == "temperature"


def test_evaluate_current_multiple_unsafe():
    result = evaluate_current(*_make_data(temp=40, uv=8))
    assert result["safe"] is False
    unsafe = [c for c in result["checks"] if not c["safe"]]
    assert len(unsafe) == 2


# --- _hour_is_safe ---


def _make_weather_hour(temp=20, uv=2, rain=0):
    return {"temperature": temp, "uv_index": uv, "rain": rain}


def _make_aqi_hour(aqi=30):
    return {"european_aqi": aqi}


def test_hour_is_safe_all_good():
    assert _hour_is_safe(_make_weather_hour(), _make_aqi_hour()) is True


def test_hour_is_safe_temp_bad():
    assert _hour_is_safe(_make_weather_hour(temp=-5), _make_aqi_hour()) is False


def test_hour_is_safe_uv_bad():
    assert _hour_is_safe(_make_weather_hour(uv=6), _make_aqi_hour()) is False


def test_hour_is_safe_rain_bad():
    assert _hour_is_safe(_make_weather_hour(rain=3), _make_aqi_hour()) is False


def test_hour_is_safe_aqi_bad():
    assert _hour_is_safe(_make_weather_hour(), _make_aqi_hour(aqi=80)) is False


def test_hour_is_safe_missing_aqi():
    assert _hour_is_safe(_make_weather_hour(), None) is True


def test_hour_is_safe_aqi_none_value():
    assert _hour_is_safe(_make_weather_hour(), {"european_aqi": None}) is True


# --- find_next_safe_window ---


def _make_forecast(hours):
    """Build weather + air_quality dicts from a list of (offset_hours, temp, uv, rain, aqi) tuples."""
    now = datetime.now()
    weather_hourly = []
    aqi_hourly = []
    for offset, temp, uv, rain, aqi in hours:
        t = (now + timedelta(hours=offset)).replace(minute=0, second=0, microsecond=0).isoformat()
        weather_hourly.append({"time": t, "temperature": temp, "uv_index": uv, "rain": rain})
        aqi_hourly.append({"time": t, "european_aqi": aqi})
    weather = {"hourly": weather_hourly}
    air_quality = {"hourly": aqi_hourly}
    return weather, air_quality


def test_find_next_safe_window_found():
    weather, aq = _make_forecast([
        (1, 20, 2, 0, 30),  # safe, 1 hour from now
    ])
    result = find_next_safe_window(weather, aq)
    assert result is not None
    assert ":" in result  # looks like a time string


def test_find_next_safe_window_none_when_all_unsafe():
    weather, aq = _make_forecast([
        (1, 40, 8, 5, 80),
    ])
    result = find_next_safe_window(weather, aq)
    assert result is None


def test_find_next_safe_window_skips_past_hours():
    weather, aq = _make_forecast([
        (-1, 20, 2, 0, 30),  # past: should be skipped
        (1, 40, 8, 5, 80),   # future but unsafe
    ])
    result = find_next_safe_window(weather, aq)
    assert result is None
