from __future__ import annotations

import time
from typing import Any, Callable

_CACHE: dict[str, tuple[float, Any]] = {}
TTL = 600  # 10 minutes
STALE_TTL = 21600  # 6 hours


def cached_call(key: str, fn: Callable, ttl: int = TTL) -> Any:
    """Return cached result if fresh, else call fn() and cache result."""
    now = time.monotonic()
    if key in _CACHE:
        ts, value = _CACHE[key]
        if now - ts < ttl:
            return value
    result = fn()
    _CACHE[key] = (now, result)
    return result


def cached_call_resilient(key: str, fn: Callable, ttl: int = TTL, stale_ttl: int = STALE_TTL) -> Any:
    """Return fresh cache when available.

    If refresh fails (e.g. transient network error), return stale cache up to stale_ttl.
    If no usable cache exists, re-raise the original error.
    """
    now = time.monotonic()
    if key in _CACHE:
        ts, value = _CACHE[key]
        if now - ts < ttl:
            return value

    try:
        result = fn()
        _CACHE[key] = (now, result)
        return result
    except Exception:
        if key in _CACHE:
            ts, value = _CACHE[key]
            if now - ts < stale_ttl:
                return value
        raise


def clear_cache() -> None:
    """Clear all cached entries."""
    _CACHE.clear()
