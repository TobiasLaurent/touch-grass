import time
from unittest.mock import MagicMock

from touch_grass.cache import TTL, _CACHE, cached_call, clear_cache


def test_cache_returns_cached_value_on_second_call():
    fn = MagicMock(return_value={"data": 1})
    result1 = cached_call("key1", fn)
    result2 = cached_call("key1", fn)
    assert result1 is result2
    assert fn.call_count == 1


def test_cache_calls_fn_for_different_keys():
    fn = MagicMock(return_value=42)
    cached_call("a", fn)
    cached_call("b", fn)
    assert fn.call_count == 2


def test_cache_expired_refetches():
    fn = MagicMock(side_effect=[{"v": 1}, {"v": 2}])
    cached_call("expiry_key", fn)
    # Manually expire the cached entry
    ts, val = _CACHE["expiry_key"]
    _CACHE["expiry_key"] = (ts - TTL - 1, val)
    result = cached_call("expiry_key", fn)
    assert result == {"v": 2}
    assert fn.call_count == 2


def test_clear_cache_forces_refetch():
    fn = MagicMock(return_value="fresh")
    cached_call("clear_key", fn)
    clear_cache()
    cached_call("clear_key", fn)
    assert fn.call_count == 2


def test_clear_cache_empties_all_entries():
    cached_call("x", lambda: 1)
    cached_call("y", lambda: 2)
    clear_cache()
    assert len(_CACHE) == 0
