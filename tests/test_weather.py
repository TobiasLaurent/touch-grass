from unittest.mock import MagicMock, patch

import pytest
import requests

from touch_grass.weather import get_air_quality, get_weather


@patch("touch_grass.weather.requests.get")
def test_get_weather_parses_response(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "current": {
            "temperature_2m": 22.5,
            "rain": 0.0,
            "uv_index": 3.1,
            "windspeed_10m": 15.0,
        },
        "hourly": {
            "time": ["2026-02-15T12:00", "2026-02-15T13:00"],
            "temperature_2m": [22.5, 23.0],
            "rain": [0.0, 0.0],
            "uv_index": [3.1, 2.8],
            "windspeed_10m": [15.0, 12.0],
        },
        "timezone": "America/Los_Angeles",
    }
    mock_get.return_value = mock_resp

    result = get_weather(37.77, -122.42)

    assert result["current"]["temperature"] == 22.5
    assert result["current"]["rain"] == 0.0
    assert result["current"]["uv_index"] == 3.1
    assert result["current"]["wind_speed"] == 15.0
    assert len(result["hourly"]) == 2
    assert result["hourly"][0]["temperature"] == 22.5
    assert result["hourly"][0]["wind_speed"] == 15.0
    assert result["timezone"] == "America/Los_Angeles"


@patch("touch_grass.weather.requests.get")
def test_get_air_quality_parses_response(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "current": {"european_aqi": 25, "us_aqi": 40},
        "hourly": {
            "time": ["2026-02-15T12:00", "2026-02-15T13:00"],
            "european_aqi": [25, 30],
            "us_aqi": [40, 45],
        },
    }
    mock_get.return_value = mock_resp

    result = get_air_quality(37.77, -122.42)

    assert result["current"]["european_aqi"] == 25
    assert result["current"]["us_aqi"] == 40
    assert len(result["hourly"]) == 2
    assert result["hourly"][1]["european_aqi"] == 30
    assert result["hourly"][1]["us_aqi"] == 45


@patch("touch_grass.weather.requests.get")
def test_get_weather_missing_current_key(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "hourly": {
            "time": [],
            "temperature_2m": [],
            "rain": [],
            "uv_index": [],
            "windspeed_10m": [],
        },
        "timezone": "UTC",
    }
    mock_get.return_value = mock_resp

    with pytest.raises(KeyError):
        get_weather(37.77, -122.42)


@patch("touch_grass.weather.requests.get")
def test_get_weather_null_uv_index(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "current": {
            "temperature_2m": 22.5,
            "rain": 0.0,
            "uv_index": None,
            "windspeed_10m": 10.0,
        },
        "hourly": {
            "time": [],
            "temperature_2m": [],
            "rain": [],
            "uv_index": [],
            "windspeed_10m": [],
        },
        "timezone": "UTC",
    }
    mock_get.return_value = mock_resp

    result = get_weather(37.77, -122.42)
    assert result["current"]["uv_index"] is None


@patch("touch_grass.weather.requests.get")
def test_get_air_quality_missing_european_aqi(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "current": {"us_aqi": 40},
        "hourly": {
            "time": ["2026-02-15T12:00"],
            "us_aqi": [40],
        },
    }
    mock_get.return_value = mock_resp

    result = get_air_quality(37.77, -122.42)
    assert result["current"]["european_aqi"] is None
    assert result["current"]["us_aqi"] == 40


@patch("touch_grass.weather.requests.get")
def test_get_weather_timeout(mock_get):
    mock_get.side_effect = requests.exceptions.Timeout()

    with pytest.raises(requests.exceptions.Timeout):
        get_weather(37.77, -122.42)


@patch("touch_grass.weather.requests.get")
def test_get_air_quality_timeout(mock_get):
    mock_get.side_effect = requests.exceptions.Timeout()

    with pytest.raises(requests.exceptions.Timeout):
        get_air_quality(37.77, -122.42)


@patch("touch_grass.weather.requests.get")
def test_cache_returns_same_object_on_second_call(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "current": {
            "temperature_2m": 20.0,
            "rain": 0.0,
            "uv_index": 2.0,
            "windspeed_10m": 5.0,
        },
        "hourly": {
            "time": [],
            "temperature_2m": [],
            "rain": [],
            "uv_index": [],
            "windspeed_10m": [],
        },
        "timezone": "UTC",
    }
    mock_get.return_value = mock_resp

    result1 = get_weather(37.77, -122.42)
    result2 = get_weather(37.77, -122.42)

    assert result1 is result2
    assert mock_get.call_count == 1


@patch("touch_grass.weather.requests.get")
def test_cache_different_coords_fetches_separately(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "current": {
            "temperature_2m": 20.0,
            "rain": 0.0,
            "uv_index": 2.0,
            "windspeed_10m": 5.0,
        },
        "hourly": {
            "time": [],
            "temperature_2m": [],
            "rain": [],
            "uv_index": [],
            "windspeed_10m": [],
        },
        "timezone": "UTC",
    }
    mock_get.return_value = mock_resp

    get_weather(37.77, -122.42)
    get_weather(40.71, -74.01)

    assert mock_get.call_count == 2
