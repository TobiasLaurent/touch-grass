import json
import os
import tempfile
from unittest.mock import patch

import pytest
import requests
from click.testing import CliRunner

from touch_grass.cli import main

SAFE_WEATHER = {
    "current": {"temperature": 22, "uv_index": 2, "rain": 0, "wind_speed": 10},
    "hourly": [],
    "timezone": "UTC",
}
SAFE_AQ = {
    "current": {"european_aqi": 20, "us_aqi": 40},
    "hourly": [],
}
UNSAFE_WEATHER = {
    "current": {"temperature": 40, "uv_index": 8, "rain": 5, "wind_speed": 10},
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


@patch("touch_grass.cli.forecast_days", return_value=[])
@patch("touch_grass.cli.find_next_safe_window", return_value="4:00 PM")
@patch("touch_grass.cli.get_air_quality", return_value=SAFE_AQ)
@patch("touch_grass.cli.get_weather", return_value=UNSAFE_WEATHER)
@patch("touch_grass.cli.get_location", return_value=LOCATION)
def test_json_output_and_unsafe_exit_code(mock_loc, mock_weather, mock_aq, mock_window, mock_forecast):
    result = CliRunner().invoke(main, ["--json"], catch_exceptions=False)
    assert result.exit_code == 10
    payload = json.loads(result.output)
    assert payload["safe"] is False
    assert payload["next_safe_window"] == "4:00 PM"


@patch("touch_grass.cli.get_air_quality", return_value=SAFE_AQ)
@patch("touch_grass.cli.get_weather", return_value=SAFE_WEATHER)
def test_lat_lon_skips_geolocation(mock_weather, mock_aq):
    result = CliRunner().invoke(main, ["--lat", "45.52", "--lon", "-122.68"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "Custom" in result.output


# --- Error handling ---


@patch("touch_grass.cli.get_weather", side_effect=KeyError("hourly"))
@patch("touch_grass.cli.get_location", return_value=LOCATION)
def test_key_error_shows_missing_field(mock_loc, mock_weather):
    result = CliRunner().invoke(main)
    assert result.exit_code != 0
    assert "missing field" in result.output


@patch("touch_grass.cli.get_weather", side_effect=ValueError("bad float"))
@patch("touch_grass.cli.get_location", return_value=LOCATION)
def test_value_error_shows_parse_error(mock_loc, mock_weather):
    result = CliRunner().invoke(main)
    assert result.exit_code != 0
    assert "parse API response" in result.output


@patch("touch_grass.cli.get_weather", side_effect=requests.exceptions.ConnectionError("refused"))
@patch("touch_grass.cli.get_location", return_value=LOCATION)
def test_network_error_exits(mock_loc, mock_weather):
    result = CliRunner().invoke(main)
    assert result.exit_code != 0
    assert "Network error" in result.output


# --- Boundary coordinates ---


@patch("touch_grass.cli.get_air_quality", return_value=SAFE_AQ)
@patch("touch_grass.cli.get_weather", return_value=SAFE_WEATHER)
def test_boundary_lat_positive_90(mock_weather, mock_aq):
    result = CliRunner().invoke(main, ["--lat", "90", "--lon", "0"], catch_exceptions=False)
    assert result.exit_code == 0


@patch("touch_grass.cli.get_air_quality", return_value=SAFE_AQ)
@patch("touch_grass.cli.get_weather", return_value=SAFE_WEATHER)
def test_boundary_lat_negative_90(mock_weather, mock_aq):
    result = CliRunner().invoke(main, ["--lat", "-90", "--lon", "0"], catch_exceptions=False)
    assert result.exit_code == 0


@patch("touch_grass.cli.get_air_quality", return_value=SAFE_AQ)
@patch("touch_grass.cli.get_weather", return_value=SAFE_WEATHER)
def test_boundary_lon_positive_180(mock_weather, mock_aq):
    result = CliRunner().invoke(main, ["--lat", "0", "--lon", "180"], catch_exceptions=False)
    assert result.exit_code == 0


@patch("touch_grass.cli.get_air_quality", return_value=SAFE_AQ)
@patch("touch_grass.cli.get_weather", return_value=SAFE_WEATHER)
def test_boundary_lon_negative_180(mock_weather, mock_aq):
    result = CliRunner().invoke(main, ["--lat", "0", "--lon", "-180"], catch_exceptions=False)
    assert result.exit_code == 0


def test_boundary_lat_out_of_range():
    result = CliRunner().invoke(main, ["--lat", "91", "--lon", "0"])
    assert result.exit_code != 0
    assert "Latitude" in result.output or "latitude" in result.output.lower()


def test_boundary_lon_out_of_range():
    result = CliRunner().invoke(main, ["--lat", "0", "--lon", "181"])
    assert result.exit_code != 0
    assert "Longitude" in result.output or "longitude" in result.output.lower()


# --- --config option ---


@patch("touch_grass.cli.get_air_quality", return_value=SAFE_AQ)
@patch("touch_grass.cli.get_weather", return_value=SAFE_WEATHER)
def test_cli_config_option_valid_file(mock_weather, mock_aq):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"temp_max": 30}, f)
        path = f.name
    try:
        result = CliRunner().invoke(
            main, ["--lat", "45.52", "--lon", "-122.68", "--config", path],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
    finally:
        os.unlink(path)


def test_cli_bad_config_exits():
    result = CliRunner().invoke(main, ["--lat", "45.52", "--lon", "-122.68", "--config", "/nonexistent.json"])
    assert result.exit_code != 0
    assert "Configuration error" in result.output


def test_cli_config_path_directory_exits():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = CliRunner().invoke(main, ["--lat", "45.52", "--lon", "-122.68", "--config", tmpdir])
    assert result.exit_code != 0
    assert "Configuration error" in result.output


@patch("touch_grass.cli.get_air_quality", return_value=SAFE_AQ)
@patch("touch_grass.cli.get_weather", return_value=SAFE_WEATHER)
def test_cli_env_var_threshold(mock_weather, mock_aq):
    env = os.environ.copy()
    env["TOUCH_GRASS_TEMP_MAX"] = "25"
    result = CliRunner().invoke(
        main, ["--lat", "45.52", "--lon", "-122.68"],
        env=env,
        catch_exceptions=False,
    )
    # SAFE_WEATHER has temp=22 which is under 25, so still safe
    assert result.exit_code == 0
    assert "Go touch grass!" in result.output


@patch("touch_grass.cli.get_air_quality", return_value=SAFE_AQ)
@patch("touch_grass.cli.get_weather", return_value=SAFE_WEATHER)
def test_configure_skip_uses_defaults_and_saves(mock_weather, mock_aq):
    with tempfile.TemporaryDirectory() as tmpdir:
        env = os.environ.copy()
        env["TOUCH_GRASS_CONFIG_DIR"] = tmpdir
        result = CliRunner().invoke(
            main,
            ["--configure", "--lat", "45.52", "--lon", "-122.68"],
            input="y\n",
            env=env,
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "Go touch grass!" in result.output
        assert os.path.exists(os.path.join(tmpdir, "thresholds.json"))


@patch("touch_grass.cli.get_air_quality", return_value=SAFE_AQ)
@patch("touch_grass.cli.get_weather", return_value=SAFE_WEATHER)
def test_configure_custom_values_affect_result(mock_weather, mock_aq):
    with tempfile.TemporaryDirectory() as tmpdir:
        env = os.environ.copy()
        env["TOUCH_GRASS_CONFIG_DIR"] = tmpdir
        # no skip, then values: temp_min temp_max uv_max aqi_max us_aqi_max rain_max wind_max
        user_input = "n\n-5\n20\n3\n50\n100\n0\n50\n"
        result = CliRunner().invoke(
            main,
            ["--configure", "--lat", "45.52", "--lon", "-122.68"],
            input=user_input,
            env=env,
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert "Keep coding" in result.output


@patch("touch_grass.cli.forecast_days")
@patch("touch_grass.cli.find_next_safe_window", return_value="4:00 PM")
@patch("touch_grass.cli.get_air_quality", return_value=SAFE_AQ)
@patch("touch_grass.cli.get_weather", return_value=SAFE_WEATHER)
@patch("touch_grass.cli.get_location", return_value=LOCATION)
def test_forecast_json_output(mock_loc, mock_weather, mock_aq, mock_window, mock_forecast):
    mock_forecast.return_value = [
        {"date": "2026-03-09", "weekday": "Monday", "safe": True, "best_window": "10:00 AM", "safe_hour_count": 4, "primary_blockers": [], "metrics": {}},
        {"date": "2026-03-10", "weekday": "Tuesday", "safe": False, "best_window": None, "safe_hour_count": 0, "primary_blockers": ["uv_index"], "metrics": {}},
    ]
    result = CliRunner().invoke(main, ["--forecast", "7", "--json"], catch_exceptions=False)
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["forecast_count"] == 7
    assert len(payload["forecast_days"]) == 2
    assert payload["forecast_days"][0]["weekday"] == "Monday"
