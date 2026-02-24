from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from touch_grass.conditions import (
    _hour_is_safe,
    check_condition,
    evaluate_current,
    find_next_safe_window,
)


# --- check_condition ---


def test_check_condition_none_value():
    safe, reason = check_condition(None, "temperature")
    assert safe is False
    assert "unavailable" in reason


def test_check_condition_none_uv():
    safe, reason = check_condition(None, "uv_index")
    assert safe is False
    assert "unavailable" in reason


def test_check_condition_none_rain():
    safe, reason = check_condition(None, "rain")
    assert safe is False
    assert "unavailable" in reason


def test_check_condition_none_aqi():
    safe, reason = check_condition(None, "air_quality")
    assert safe is False
    assert "unavailable" in reason


def test_check_condition_temp_safe():
    safe, reason = check_condition(20, "temperature")
    assert safe is True
    assert "20°C" in reason


def test_check_condition_temp_too_cold():
    safe, reason = check_condition(-10, "temperature")
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


def test_check_condition_us_aqi_good():
    safe, reason = check_condition(80, "us_air_quality")
    assert safe is True
    assert "US AQI" in reason


def test_check_condition_us_aqi_poor():
    safe, reason = check_condition(120, "us_air_quality")
    assert safe is False
    assert "US AQI" in reason


def test_check_condition_wind_safe():
    safe, reason = check_condition(20, "wind_speed")
    assert safe is True
    assert "20 km/h" in reason


def test_check_condition_wind_too_strong():
    safe, reason = check_condition(60, "wind_speed")
    assert safe is False
    assert "too strong" in reason


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
    result = evaluate_current(*_make_data(temp=-10))
    assert result["safe"] is False
    unsafe = [c for c in result["checks"] if not c["safe"]]
    assert len(unsafe) == 1
    assert unsafe[0]["name"] == "temperature"


def test_evaluate_current_multiple_unsafe():
    result = evaluate_current(*_make_data(temp=40, uv=8))
    assert result["safe"] is False
    unsafe = [c for c in result["checks"] if not c["safe"]]
    assert len(unsafe) == 2


def test_evaluate_current_includes_wind_and_us_aqi():
    weather = {"current": {"temperature": 20, "uv_index": 2, "rain": 0, "wind_speed": 10}}
    air_quality = {"current": {"european_aqi": 30, "us_aqi": 60}}
    result = evaluate_current(weather, air_quality)
    assert result["safe"] is True
    assert len(result["checks"]) == 6


def test_evaluate_current_wind_unsafe():
    weather = {"current": {"temperature": 20, "uv_index": 2, "rain": 0, "wind_speed": 70}}
    air_quality = {"current": {"european_aqi": 30}}
    result = evaluate_current(weather, air_quality)
    assert result["safe"] is False
    unsafe = [c for c in result["checks"] if not c["safe"]]
    assert any(c["name"] == "wind_speed" for c in unsafe)


def test_evaluate_current_us_aqi_unsafe():
    weather = {"current": {"temperature": 20, "uv_index": 2, "rain": 0}}
    air_quality = {"current": {"european_aqi": 30, "us_aqi": 150}}
    result = evaluate_current(weather, air_quality)
    assert result["safe"] is False
    unsafe = [c for c in result["checks"] if not c["safe"]]
    assert any(c["name"] == "us_air_quality" for c in unsafe)


# --- _hour_is_safe ---


def _make_weather_hour(temp=20, uv=2, rain=0, wind_speed=None):
    hour = {"temperature": temp, "uv_index": uv, "rain": rain}
    if wind_speed is not None:
        hour["wind_speed"] = wind_speed
    return hour


def _make_aqi_hour(aqi=30, us_aqi=None):
    hour = {"european_aqi": aqi}
    if us_aqi is not None:
        hour["us_aqi"] = us_aqi
    return hour


def test_hour_is_safe_all_good():
    assert _hour_is_safe(_make_weather_hour(), _make_aqi_hour()) is True


def test_hour_is_safe_temp_bad():
    assert _hour_is_safe(_make_weather_hour(temp=-10), _make_aqi_hour()) is False


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


def test_hour_is_safe_wind_bad():
    assert _hour_is_safe(_make_weather_hour(wind_speed=60), _make_aqi_hour()) is False


def test_hour_is_safe_wind_ok():
    assert _hour_is_safe(_make_weather_hour(wind_speed=20), _make_aqi_hour()) is True


def test_hour_is_safe_us_aqi_bad():
    assert _hour_is_safe(_make_weather_hour(), _make_aqi_hour(us_aqi=150)) is False


def test_hour_is_safe_missing_temperature_key():
    assert _hour_is_safe({"uv_index": 2, "rain": 0}, _make_aqi_hour()) is False


def test_hour_is_safe_missing_uv_key():
    assert _hour_is_safe({"temperature": 20, "rain": 0}, _make_aqi_hour()) is False


def test_hour_is_safe_missing_rain_key():
    assert _hour_is_safe({"temperature": 20, "uv_index": 2}, _make_aqi_hour()) is False


# --- find_next_safe_window ---


def _make_forecast(hours):
    """Build weather + air_quality dicts from a list of (offset_hours, temp, uv, rain, aqi) tuples.

    Uses UTC times so comparisons are timezone-consistent regardless of machine timezone.
    """
    now_utc = datetime.now(tz=ZoneInfo("UTC")).replace(tzinfo=None)
    weather_hourly = []
    aqi_hourly = []
    for offset, temp, uv, rain, aqi in hours:
        t = (now_utc + timedelta(hours=offset)).replace(minute=0, second=0, microsecond=0).isoformat()
        weather_hourly.append({"time": t, "temperature": temp, "uv_index": uv, "rain": rain})
        aqi_hourly.append({"time": t, "european_aqi": aqi})
    weather = {"hourly": weather_hourly, "timezone": "UTC"}
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


def test_find_next_safe_window_all_past_hours():
    weather, aq = _make_forecast([
        (-3, 20, 2, 0, 30),
        (-2, 20, 2, 0, 30),
        (-1, 20, 2, 0, 30),
    ])
    result = find_next_safe_window(weather, aq)
    assert result is None


def test_find_next_safe_window_uses_timezone():
    """Timezone-aware comparison does not raise TypeError."""
    weather, aq = _make_forecast([
        (1, 20, 2, 0, 30),
    ])
    weather["timezone"] = "America/New_York"
    # Should not raise; result may or may not be None depending on clock,
    # but the call must succeed without TypeError.
    result = find_next_safe_window(weather, aq)
    # The hour string is a UTC time labelled as New York — in test we just
    # verify it returns a string or None without crashing.
    assert result is None or ":" in result
