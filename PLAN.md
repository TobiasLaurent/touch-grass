# Plan: Show Region-Appropriate AQI Based on IP Location

## Problem

The app currently displays **both** the European AQI and the US AQI in the
conditions table regardless of where the user is located. The IP-based
geolocation already returns a `country` field; we should use it to show only
the AQI standard that is relevant to the user's region.

_(Note: UV index is a universal scale and is unaffected. The EU/US distinction
in this codebase is for Air Quality Index only.)_

---

## Approach

Introduce an `aqi_region` value (`"eu"` or `"us"`) derived from the country
code that `get_location()` already returns. Thread that value through the
evaluation pipeline so only one AQI is fetched for display and safety checks.

---

## Files to Change

### 1. `src/touch_grass/location.py`

Add a pure helper function `get_aqi_region(country: str) -> str`.

```python
_EU_COUNTRIES = {
    "AT","BE","BG","HR","CY","CZ","DK","EE","FI","FR","DE","GR",
    "HU","IE","IT","LV","LT","LU","MT","NL","PL","PT","RO","SK",
    "SI","ES","SE",          # EU member states
    "GB","NO","IS","LI",     # EEA / close neighbours
    "CH","TR","RS","BA","ME","MK","AL","UA","MD","BY","RU",  # wider Europe
}

def get_aqi_region(country: str) -> str:
    """Return 'eu' for European countries, 'us' otherwise."""
    return "eu" if country.upper() in _EU_COUNTRIES else "us"
```

- Used for the IP-derived location AND as a fallback for manual coordinates
  (when `country` is `""`, returns `"us"`; that's acceptable because manual
  coordinates are typically used by power users who know their region).

---

### 2. `src/touch_grass/conditions.py`

Add `aqi_region: str = "eu"` parameter to three functions.

#### `evaluate_current(weather, air_quality, aqi_region="eu")`

Replace the hard-coded two-AQI block with a branch:

```python
# Before (always adds both):
("air_quality", eu_aqi),
("us_air_quality", us_aqi),

# After (adds only the relevant one):
if aqi_region == "eu":
    checks_input.append(("air_quality", eu_aqi))
else:
    checks_input.append(("us_air_quality", us_aqi))
```

The skip-when-None guard for `us_air_quality` can be removed because we only
add that check when the user is in a US-AQI region.

#### `_hour_is_safe(weather_hour, aqi_hour, aqi_region="eu")`

Replace the check-both block:

```python
# Before:
if aqi_hour:
    eu = aqi_hour.get("european_aqi")
    if eu is not None and eu >= THRESHOLDS["aqi_max"]:
        return False
    us = aqi_hour.get("us_aqi")
    if us is not None and us >= THRESHOLDS["us_aqi_max"]:
        return False

# After:
if aqi_hour:
    if aqi_region == "eu":
        eu = aqi_hour.get("european_aqi")
        if eu is not None and eu >= THRESHOLDS["aqi_max"]:
            return False
    else:
        us = aqi_hour.get("us_aqi")
        if us is not None and us >= THRESHOLDS["us_aqi_max"]:
            return False
```

#### `find_next_safe_window(weather, air_quality, aqi_region="eu")`

Pass `aqi_region` through to `_hour_is_safe`:

```python
if _hour_is_safe(hour, aqi_hour, aqi_region):
```

---

### 3. `src/touch_grass/cli.py`

Import `get_aqi_region` and determine the region after location resolution.

```python
from touch_grass.location import get_location, get_aqi_region
```

After the location block:

```python
aqi_region = get_aqi_region(location["country"])
```

Pass it to both evaluation calls:

```python
result = evaluate_current(weather, air_quality, aqi_region)
...
next_window = find_next_safe_window(weather, air_quality, aqi_region)
```

---

### 4. `tests/test_location.py`

Add tests for the new helper:

```python
from touch_grass.location import get_aqi_region

def test_get_aqi_region_eu_countries():
    assert get_aqi_region("DE") == "eu"
    assert get_aqi_region("FR") == "eu"
    assert get_aqi_region("GB") == "eu"

def test_get_aqi_region_us_and_non_eu():
    assert get_aqi_region("US") == "us"
    assert get_aqi_region("CA") == "us"
    assert get_aqi_region("JP") == "us"

def test_get_aqi_region_empty_country():
    assert get_aqi_region("") == "us"

def test_get_aqi_region_case_insensitive():
    assert get_aqi_region("de") == "eu"
```

---

### 5. `tests/test_conditions.py`

Update tests that relied on both AQIs being checked simultaneously.

**`test_evaluate_current_all_safe`** — unchanged (uses `_make_data` with EU-only
air_quality, and `aqi_region` defaults to `"eu"`; still 4 checks).

**`test_evaluate_current_includes_wind_and_us_aqi`** — split into two tests:

```python
def test_evaluate_current_eu_region_wind_and_eu_aqi():
    weather = {"current": {"temperature": 20, "uv_index": 2, "rain": 0, "wind_speed": 10}}
    air_quality = {"current": {"european_aqi": 30, "us_aqi": 60}}
    result = evaluate_current(weather, air_quality, aqi_region="eu")
    assert result["safe"] is True
    assert len(result["checks"]) == 5  # temp, uv, rain, wind, EU AQI
    assert not any(c["name"] == "us_air_quality" for c in result["checks"])

def test_evaluate_current_us_region_wind_and_us_aqi():
    weather = {"current": {"temperature": 20, "uv_index": 2, "rain": 0, "wind_speed": 10}}
    air_quality = {"current": {"european_aqi": 30, "us_aqi": 60}}
    result = evaluate_current(weather, air_quality, aqi_region="us")
    assert result["safe"] is True
    assert len(result["checks"]) == 5  # temp, uv, rain, wind, US AQI
    assert not any(c["name"] == "air_quality" for c in result["checks"])
```

**`test_evaluate_current_us_aqi_unsafe`** — add `aqi_region="us"` argument:

```python
result = evaluate_current(weather, air_quality, aqi_region="us")
```

**`test_hour_is_safe_us_aqi_bad`** — add `aqi_region="us"` argument:

```python
def test_hour_is_safe_us_aqi_bad():
    assert _hour_is_safe(_make_weather_hour(), _make_aqi_hour(us_aqi=150), aqi_region="us") is False
```

Add a complementary test to confirm US AQI is **ignored** in EU region:

```python
def test_hour_is_safe_us_aqi_ignored_in_eu_region():
    # High US AQI should have no effect when region is EU
    assert _hour_is_safe(_make_weather_hour(), _make_aqi_hour(us_aqi=500), aqi_region="eu") is True
```

**`_make_forecast` helper** — no change needed; it only puts `european_aqi`
into hourly data which is fine for the default `aqi_region="eu"`.

---

## Summary of Changes

| File | Change |
|---|---|
| `location.py` | Add `_EU_COUNTRIES` set and `get_aqi_region()` helper |
| `conditions.py` | Add `aqi_region` param to 3 functions; only evaluate relevant AQI |
| `cli.py` | Derive `aqi_region` from country; pass to evaluate + find_next |
| `tests/test_location.py` | Add 4 tests for `get_aqi_region` |
| `tests/test_conditions.py` | Update/split 3 tests; add 2 new tests |

No other files need changes. The air quality API still fetches both
`european_aqi` and `us_aqi` (no network change needed), but only the relevant
one is checked and shown.
