from unittest.mock import MagicMock, patch

from touch_grass.location import get_location


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
