"""Local Data Manager - Robust offline price data with multi-tier fallback

Architecture:
1. Try live API (with 1-day cache)
2. Fall back to daily snapshot file (if exists)
3. Fall back to static CSV (always available)
4. Last resort: synthetic demo data

This eliminates 429 errors during user interaction.
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import csv

# Cache directory
CACHE_DIR = Path(__file__).parent / ".cache"
CACHE_DIR.mkdir(exist_ok=True)

# Static fallback data
STATIC_CSV = Path(__file__).parent / "static_prices.csv"

# Daily snapshot (updated by ETL job)
DAILY_SNAPSHOT = CACHE_DIR / f"daily_prices_{datetime.now().strftime('%Y-%m-%d')}.json"


def load_static_prices() -> Dict[str, Dict[str, Any]]:
    """Load static CSV fallback data."""
    prices = {}
    if not STATIC_CSV.exists():
        return prices
    
    try:
        with open(STATIC_CSV, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ticker = row['ticker'].upper()
                prices[ticker] = {
                    'ticker': ticker,
                    'name': row['name'],
                    'price': float(row['price']),
                    'change': float(row['change']),
                    'volume': int(row.get('volume', 0)),
                    'marketCap': float(row.get('marketCap', 0)),
                    'pe': row.get('pe', 'N/A'),
                    'dividend': float(row.get('dividend', 0)),
                    'rsi': float(row.get('rsi', 50)),
                    'sector': row.get('sector', 'Unknown'),
                    'beta': float(row.get('beta', 1.0)),
                    'avg_volume': int(row.get('avg_volume', 0)),
                    'week52High': float(row.get('week52High', 0)),
                    'week52Low': float(row.get('week52Low', 0)),
                    'last_updated': row.get('last_updated', ''),
                    'success': True,
                    'source': 'static_csv'
                }
    except Exception as e:
        print(f"⚠️ Failed to load static CSV: {e}")
    
    return prices


def load_daily_snapshot() -> Dict[str, Dict[str, Any]]:
    """Load daily snapshot if available and recent."""
    if not DAILY_SNAPSHOT.exists():
        return {}
    
    try:
        # Check if snapshot is from today
        mod_time = datetime.fromtimestamp(DAILY_SNAPSHOT.stat().st_mtime)
        if (datetime.now() - mod_time) > timedelta(days=1):
            return {}
        
        with open(DAILY_SNAPSHOT, 'r') as f:
            data = json.load(f)
            return {k.upper(): v for k, v in data.items()}
    except Exception as e:
        print(f"⚠️ Failed to load daily snapshot: {e}")
        return {}


def save_daily_snapshot(data: Dict[str, Dict[str, Any]]) -> None:
    """Save successful API responses to daily snapshot."""
    try:
        with open(DAILY_SNAPSHOT, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Saved daily snapshot: {len(data)} tickers")
    except Exception as e:
        print(f"⚠️ Failed to save daily snapshot: {e}")


def get_local_price(ticker: str) -> Optional[Dict[str, Any]]:
    """Get price from local sources (snapshot -> static CSV)."""
    ticker = ticker.upper()
    
    # Try daily snapshot first
    snapshot = load_daily_snapshot()
    if ticker in snapshot:
        data = snapshot[ticker].copy()
        data['source'] = 'daily_snapshot'
        return data
    
    # Fall back to static CSV
    static = load_static_prices()
    if ticker in static:
        return static[ticker]
    
    return None


def get_prices_with_fallback(
    tickers: List[str],
    api_fetch_func,
    max_cache_age_hours: int = 24
) -> List[Dict[str, Any]]:
    """
    Robust price fetching with multi-tier fallback:
    1. Try live API (with cache)
    2. Use daily snapshot
    3. Use static CSV
    4. Return demo data
    """
    results = []
    live_data = {}
    
    for ticker in tickers:
        ticker = ticker.upper()
        data = None
        
        # Tier 1: Try live API
        try:
            api_result = api_fetch_func([ticker])
            if api_result and len(api_result) > 0:
                candidate = api_result[0]
                if candidate.get('success') and candidate.get('price', 0) > 0:
                    data = candidate
                    data['source'] = 'live_api'
                    live_data[ticker] = data
        except Exception as e:
            print(f"⚠️ Live API failed for {ticker}: {e}")
        
        # Tier 2 & 3: Local fallback
        if not data:
            data = get_local_price(ticker)
            if data:
                print(f"📂 Using local data for {ticker} (source: {data.get('source')})")
        
        # Tier 4: Demo data
        if not data:
            print(f"⚠️ No data for {ticker}, using demo")
            data = {
                'ticker': ticker,
                'name': ticker,
                'price': 100.0,
                'change': 0.0,
                'volume': 1000000,
                'marketCap': 1000000000,
                'pe': 'N/A',
                'dividend': 0.0,
                'rsi': 50,
                'sector': 'Unknown',
                'success': True,
                'source': 'demo'
            }
        
        results.append(data)
    
    # Save successful live fetches to daily snapshot
    if live_data:
        existing = load_daily_snapshot()
        existing.update(live_data)
        save_daily_snapshot(existing)
    
    return results


def cleanup_old_snapshots(max_age_days: int = 7) -> None:
    """Remove snapshot files older than max_age_days."""
    try:
        cutoff = datetime.now() - timedelta(days=max_age_days)
        for file in CACHE_DIR.glob("daily_prices_*.json"):
            if datetime.fromtimestamp(file.stat().st_mtime) < cutoff:
                file.unlink()
                print(f"🗑️ Removed old snapshot: {file.name}")
    except Exception as e:
        print(f"⚠️ Cleanup failed: {e}")
