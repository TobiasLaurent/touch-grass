import requests

_EU_COUNTRIES = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR",
    "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK",
    "SI", "ES", "SE",           # EU member states
    "GB", "NO", "IS", "LI",     # EEA / close neighbours
    "CH", "TR", "RS", "BA", "ME", "MK", "AL", "UA", "MD", "BY", "RU",
}


def get_aqi_region(country: str) -> str:
    """Return 'eu' for European countries, 'us' otherwise."""
    return "eu" if country.upper() in _EU_COUNTRIES else "us"


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
