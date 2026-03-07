import pytest

from touch_grass import cache


def test_cached_call_resilient_uses_stale_on_failure():
    cache.clear_cache()
    key = "k1"

    # seed cache
    value = cache.cached_call_resilient(key, lambda: {"ok": True}, ttl=0, stale_ttl=3600)
    assert value["ok"] is True

    # refresh fails -> stale value should be returned
    value2 = cache.cached_call_resilient(
        key,
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
        ttl=0,
        stale_ttl=3600,
    )
    assert value2 == value


def test_cached_call_resilient_raises_without_cache():
    cache.clear_cache()
    with pytest.raises(RuntimeError):
        cache.cached_call_resilient(
            "k2",
            lambda: (_ for _ in ()).throw(RuntimeError("boom")),
            ttl=0,
            stale_ttl=3600,
        )
