from unittest.mock import MagicMock, patch

from touch_grass.weather import get_air_quality, get_weather


@patch("touch_grass.weather.requests.get")
def test_get_weather_parses_response(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "current": {
            "temperature_2m": 22.5,
            "rain": 0.0,
            "uv_index": 3.1,
        },
        "hourly": {
            "time": ["2026-02-15T12:00", "2026-02-15T13:00"],
            "temperature_2m": [22.5, 23.0],
            "rain": [0.0, 0.0],
            "uv_index": [3.1, 2.8],
        },
        "timezone": "America/Los_Angeles",
    }
    mock_get.return_value = mock_resp

    result = get_weather(37.77, -122.42)

    assert result["current"]["temperature"] == 22.5
    assert result["current"]["rain"] == 0.0
    assert result["current"]["uv_index"] == 3.1
    assert len(result["hourly"]) == 2
    assert result["hourly"][0]["temperature"] == 22.5
    assert result["timezone"] == "America/Los_Angeles"


@patch("touch_grass.weather.requests.get")
def test_get_air_quality_parses_response(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "current": {"european_aqi": 25},
        "hourly": {
            "time": ["2026-02-15T12:00", "2026-02-15T13:00"],
            "european_aqi": [25, 30],
        },
    }
    mock_get.return_value = mock_resp

    result = get_air_quality(37.77, -122.42)

    assert result["current"]["european_aqi"] == 25
    assert len(result["hourly"]) == 2
    assert result["hourly"][1]["european_aqi"] == 30
