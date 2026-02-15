from unittest.mock import patch

from click.testing import CliRunner

from touch_grass.cli import main

SAFE_WEATHER = {
    "current": {"temperature": 22, "uv_index": 2, "rain": 0},
    "hourly": [],
    "timezone": "UTC",
}
SAFE_AQ = {
    "current": {"european_aqi": 20},
    "hourly": [],
}
UNSAFE_WEATHER = {
    "current": {"temperature": 40, "uv_index": 8, "rain": 5},
    "hourly": [],
    "timezone": "UTC",
}
LOCATION = {
    "city": "Portland",
    "region": "Oregon",
    "country": "US",
    "latitude": 45.52,
    "longitude": -122.68,
}


@patch("touch_grass.cli.get_air_quality", return_value=SAFE_AQ)
@patch("touch_grass.cli.get_weather", return_value=SAFE_WEATHER)
@patch("touch_grass.cli.get_location", return_value=LOCATION)
def test_safe_conditions(mock_loc, mock_weather, mock_aq):
    result = CliRunner().invoke(main, catch_exceptions=False)
    assert result.exit_code == 0
    assert "Go touch grass!" in result.output


@patch("touch_grass.cli.find_next_safe_window", return_value=None)
@patch("touch_grass.cli.get_air_quality", return_value=SAFE_AQ)
@patch("touch_grass.cli.get_weather", return_value=UNSAFE_WEATHER)
@patch("touch_grass.cli.get_location", return_value=LOCATION)
def test_unsafe_conditions(mock_loc, mock_weather, mock_aq, mock_window):
    result = CliRunner().invoke(main, catch_exceptions=False)
    assert result.exit_code == 0
    assert "Keep coding" in result.output


@patch("touch_grass.cli.get_air_quality", return_value=SAFE_AQ)
@patch("touch_grass.cli.get_weather", return_value=SAFE_WEATHER)
def test_lat_lon_skips_geolocation(mock_weather, mock_aq):
    result = CliRunner().invoke(main, ["--lat", "45.52", "--lon", "-122.68"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "Custom" in result.output
