from __future__ import annotations

import time
from typing import Any, Callable

_CACHE: dict[str, tuple[float, Any]] = {}
TTL = 600  # 10 minutes


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


def clear_cache() -> None:
    """Clear all cached entries."""
    _CACHE.clear()
