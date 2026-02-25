from unittest.mock import MagicMock, patch

from touch_grass.location import get_aqi_region, get_location


@patch("touch_grass.location.requests.get")
def test_get_location_parses_response(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "city": "San Francisco",
        "region": "California",
        "country": "US",
        "loc": "37.7749,-122.4194",
    }
    mock_get.return_value = mock_resp

    loc = get_location()

    assert loc["city"] == "San Francisco"
    assert loc["region"] == "California"
    assert loc["country"] == "US"
    assert loc["latitude"] == 37.7749
    assert loc["longitude"] == -122.4194
    mock_resp.raise_for_status.assert_called_once()


def test_get_aqi_region_eu_countries():
    assert get_aqi_region("DE") == "eu"
    assert get_aqi_region("FR") == "eu"
    assert get_aqi_region("GB") == "eu"
    assert get_aqi_region("PL") == "eu"


def test_get_aqi_region_us_and_non_eu():
    assert get_aqi_region("US") == "us"
    assert get_aqi_region("CA") == "us"
    assert get_aqi_region("JP") == "us"
    assert get_aqi_region("AU") == "us"


def test_get_aqi_region_empty_country():
    assert get_aqi_region("") == "us"


def test_get_aqi_region_case_insensitive():
    assert get_aqi_region("de") == "eu"
    assert get_aqi_region("gb") == "eu"
