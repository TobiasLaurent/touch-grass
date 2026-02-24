import json
import os
import tempfile

import pytest

from touch_grass.config import DEFAULT_THRESHOLDS, load_thresholds


def test_load_thresholds_defaults():
    result = load_thresholds()
    assert result == DEFAULT_THRESHOLDS


def test_load_thresholds_from_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"temp_max": 30, "uv_max": 3}, f)
        path = f.name
    try:
        result = load_thresholds(path)
        assert result["temp_max"] == 30
        assert result["uv_max"] == 3
        # Other keys stay at defaults
        assert result["temp_min"] == DEFAULT_THRESHOLDS["temp_min"]
        assert result["aqi_max"] == DEFAULT_THRESHOLDS["aqi_max"]
    finally:
        os.unlink(path)


def test_load_thresholds_file_unknown_keys_ignored():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"unknown_key": 999, "temp_max": 28}, f)
        path = f.name
    try:
        result = load_thresholds(path)
        assert result["temp_max"] == 28
        assert "unknown_key" not in result
    finally:
        os.unlink(path)


def test_load_thresholds_bad_config_path():
    with pytest.raises(FileNotFoundError, match="not found"):
        load_thresholds("/nonexistent/path/config.json")


def test_load_thresholds_env_var_overrides(monkeypatch):
    monkeypatch.setenv("TOUCH_GRASS_TEMP_MAX", "28")
    result = load_thresholds()
    assert result["temp_max"] == 28.0
    assert result["temp_min"] == DEFAULT_THRESHOLDS["temp_min"]


def test_load_thresholds_env_overrides_file(monkeypatch):
    monkeypatch.setenv("TOUCH_GRASS_TEMP_MAX", "25")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"temp_max": 30}, f)
        path = f.name
    try:
        result = load_thresholds(path)
        assert result["temp_max"] == 25.0  # env wins over file
    finally:
        os.unlink(path)


def test_load_thresholds_invalid_env_var(monkeypatch):
    monkeypatch.setenv("TOUCH_GRASS_TEMP_MAX", "notanumber")
    with pytest.raises(ValueError, match="TOUCH_GRASS_TEMP_MAX"):
        load_thresholds()


def test_load_thresholds_all_env_vars(monkeypatch):
    monkeypatch.setenv("TOUCH_GRASS_TEMP_MIN", "-10")
    monkeypatch.setenv("TOUCH_GRASS_TEMP_MAX", "40")
    monkeypatch.setenv("TOUCH_GRASS_UV_MAX", "6")
    monkeypatch.setenv("TOUCH_GRASS_AQI_MAX", "75")
    monkeypatch.setenv("TOUCH_GRASS_US_AQI_MAX", "150")
    monkeypatch.setenv("TOUCH_GRASS_RAIN_MAX", "1")
    monkeypatch.setenv("TOUCH_GRASS_WIND_MAX", "70")
    result = load_thresholds()
    assert result["temp_min"] == -10.0
    assert result["temp_max"] == 40.0
    assert result["uv_max"] == 6.0
    assert result["aqi_max"] == 75
    assert result["us_aqi_max"] == 150
    assert result["rain_max"] == 1.0
    assert result["wind_max"] == 70.0
