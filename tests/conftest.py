import pytest

from touch_grass.cache import clear_cache
from touch_grass.config import DEFAULT_THRESHOLDS
from touch_grass import conditions


@pytest.fixture(autouse=True)
def reset_state():
    """Clear cache and reset thresholds before/after every test."""
    clear_cache()
    conditions.apply_thresholds(dict(DEFAULT_THRESHOLDS))
    yield
    clear_cache()
    conditions.apply_thresholds(dict(DEFAULT_THRESHOLDS))
