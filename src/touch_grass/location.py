import requests


def get_location() -> dict:
    """Get user location from IP geolocation.

    Returns dict with keys: city, region, country, latitude, longitude
    """
    resp = requests.get("https://ipinfo.io/json", timeout=5)
    resp.raise_for_status()
    data = resp.json()

    lat, lon = data["loc"].split(",")

    return {
        "city": data.get("city", "Unknown"),
        "region": data.get("region", ""),
        "country": data.get("country", ""),
        "latitude": float(lat),
        "longitude": float(lon),
    }
