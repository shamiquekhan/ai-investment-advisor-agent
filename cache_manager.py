"""Persistent file-based cache for stock data to survive API throttling."""

import json
import time
from pathlib import Path
from typing import Any, Optional

CACHE_DIR = Path(".cache")
CACHE_FILE = CACHE_DIR / "stock_data_cache.json"
CACHE_TTL_SECONDS = 300  # 5 minutes


def _ensure_cache_dir():
    """Create cache directory if it doesn't exist."""
    CACHE_DIR.mkdir(exist_ok=True)


def _load_cache() -> dict[str, dict[str, Any]]:
    """Load the entire cache from disk."""
    if not CACHE_FILE.exists():
        return {}
    try:
        with CACHE_FILE.open("r") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_cache(cache: dict[str, dict[str, Any]]):
    """Write the entire cache to disk."""
    _ensure_cache_dir()
    try:
        with CACHE_FILE.open("w") as f:
            json.dump(cache, f, indent=2)
    except Exception:
        pass


def get_cached_stock(ticker: str) -> Optional[dict[str, Any]]:
    """
    Retrieve cached stock data if it exists and is not expired.
    Returns None if cache miss or expired.
    """
    cache = _load_cache()
    entry = cache.get(ticker)
    if not entry:
        return None
    
    cached_time = entry.get("cached_at", 0)
    age = time.time() - cached_time
    
    if age > CACHE_TTL_SECONDS:
        return None
    
    return entry.get("data")


def set_cached_stock(ticker: str, data: dict[str, Any]):
    """Store stock data in the cache with current timestamp."""
    cache = _load_cache()
    cache[ticker] = {
        "cached_at": time.time(),
        "data": data,
    }
    _save_cache(cache)


def clear_cache():
    """Remove all cached stock data."""
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()
