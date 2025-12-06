"""
Multi-Provider Data Source Manager
Distributes requests across Yahoo Finance, Finnhub, and Alpha Vantage
to avoid rate limits while keeping everything 100% FREE.
"""

import yfinance as yf
import requests
import time
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import threading
from typing import Dict, List, Optional

# Load environment variables from .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, will use system env vars only

# ============================================================================
# CONFIGURATION
# ============================================================================

# Cache settings
CACHE_DIR = Path(__file__).parent / ".cache"
CACHE_DIR.mkdir(exist_ok=True)

YFINANCE_CACHE_TTL = 3600  # 1 hour
FINNHUB_CACHE_TTL = 300     # 5 minutes (real-time)
ALPHA_VANTAGE_CACHE_TTL = 3600  # 1 hour
TWELVE_DATA_CACHE_TTL = 300  # 5 minutes (real-time)
MARKETSTACK_CACHE_TTL = 900  # 15 minutes

# API Keys (FREE TIER - get yours at the links below)
# Finnhub: https://finnhub.io/register (60 calls/minute free)
# Alpha Vantage: https://www.alphavantage.co/support/#api-key (25 calls/day free)
# Twelve Data: https://twelvedata.com/pricing (800 calls/day free)
# MarketStack: https://marketstack.com/product (1000 calls/month free)

# ⚠️ SECURITY: Load from environment variables only (never hardcode)
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
TWELVE_DATA_API_KEY = os.getenv('TWELVE_DATA_API_KEY')
MARKETSTACK_API_KEY = os.getenv('MARKETSTACK_API_KEY')

# Rate limiting
_yfinance_lock = threading.Lock()
_finnhub_lock = threading.Lock()
_alphavantage_lock = threading.Lock()
_twelvedata_lock = threading.Lock()
_marketstack_lock = threading.Lock()

YFINANCE_DELAY = 1.5  # seconds between calls
FINNHUB_DELAY = 1.0   # 60 calls/min = 1 call/sec (safe)
ALPHAVANTAGE_DELAY = 13.0  # 25 calls/day ≈ 1 call per 13 sec (very conservative)
TWELVE_DATA_DELAY = 0.11  # 800 calls/day ≈ 8 calls/min (safe with buffer)
MARKETSTACK_DELAY = 0.1  # 1000 calls/month ≈ 33/day (safe with buffer)

# ============================================================================
# CACHE UTILITIES
# ============================================================================

def _get_cache_path(provider: str, ticker: str, data_type: str = "main") -> Path:
    """Generate cache file path for a provider/ticker combo."""
    safe_ticker = ticker.replace(".", "_").replace("/", "_")
    return CACHE_DIR / f"{provider}_{safe_ticker}_{data_type}.json"

def _read_cache(cache_path: Path, ttl_seconds: int) -> Optional[Dict]:
    """Read cache if it exists and is not expired."""
    if not cache_path.exists():
        return None
    
    try:
        with open(cache_path, 'r') as f:
            data = json.load(f)
        
        # Check expiration
        cached_time = datetime.fromisoformat(data.get('cached_at', '2000-01-01'))
        if datetime.now() - cached_time > timedelta(seconds=ttl_seconds):
            return None  # Expired
        
        return data.get('data')
    except Exception:
        return None

def _write_cache(cache_path: Path, data: Dict):
    """Write data to cache with timestamp."""
    try:
        cache_data = {
            'cached_at': datetime.now().isoformat(),
            'data': data
        }
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f)
    except Exception as e:
        print(f"⚠️ Cache write failed: {e}")

# ============================================================================
# YAHOO FINANCE (Historical data, fundamentals)
# ============================================================================

def get_yfinance_data(ticker: str) -> Optional[Dict]:
    """
    Fetch comprehensive data from Yahoo Finance with caching and safe rate limiting.
    USE FOR: Historical prices, fundamentals, basic info.
    CACHE: 1 hour
    """
    cache_path = _get_cache_path('yfinance', ticker)
    
    # Try cache first
    cached = _read_cache(cache_path, YFINANCE_CACHE_TTL)
    if cached:
        return cached
    
    # Import safe rate-limited fetch from data_sources
    try:
        from data_sources import get_stock_data
        result = get_stock_data(ticker)
        
        if result and result.get('success'):
            # Map data_sources format to multi_provider format
            data = {
                'ticker': ticker,
                'name': result.get('name', ticker),
                'current_price': result.get('price', 0),
                'previous_close': result.get('previous_close', 0),
                'market_cap': result.get('marketCap', 0),
                'pe_ratio': result.get('pe', 0),
                'dividend_yield': result.get('dividend', 0),
                'beta': result.get('beta', 1.0),
                'fifty_two_week_high': result.get('fiftyTwoWeekHigh', 0),
                'fifty_two_week_low': result.get('fiftyTwoWeekLow', 0),
                'volume': result.get('volume', 0),
                'avg_volume': result.get('avgVolume', 0),
                'history': result.get('history', {}),
                'timestamp': datetime.now().isoformat()
            }
            
            # Cache and return
            _write_cache(cache_path, data)
            return data
            
    except Exception as e:
        print(f"⚠️ YFinance (via data_sources) error for {ticker}: {e}")
    
    return None

# ============================================================================
# FINNHUB (Real-time quotes, news)
# ============================================================================

def get_finnhub_quote(ticker: str) -> Optional[Dict]:
    """
    Fetch real-time quote from Finnhub.
    USE FOR: Live price, day change, intraday data.
    CACHE: 5 minutes
    FREE TIER: 60 calls/minute
    """
    if not FINNHUB_API_KEY:
        return None  # API key not configured
    
    cache_path = _get_cache_path('finnhub', ticker, 'quote')
    
    # Try cache first
    cached = _read_cache(cache_path, FINNHUB_CACHE_TTL)
    if cached:
        return cached
    
    # Rate-limited fetch
    with _finnhub_lock:
        try:
            url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={FINNHUB_API_KEY}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                quote = response.json()
                
                data = {
                    'ticker': ticker,
                    'current_price': quote.get('c', 0),  # Current price
                    'change': quote.get('d', 0),          # Change
                    'percent_change': quote.get('dp', 0),  # Percent change
                    'high': quote.get('h', 0),            # Day high
                    'low': quote.get('l', 0),             # Day low
                    'open': quote.get('o', 0),            # Day open
                    'previous_close': quote.get('pc', 0), # Previous close
                    'timestamp': datetime.now().isoformat()
                }
                
                _write_cache(cache_path, data)
                time.sleep(FINNHUB_DELAY)
                return data
            else:
                time.sleep(FINNHUB_DELAY)
                return None
                
        except Exception as e:
            print(f"⚠️ Finnhub error for {ticker}: {e}")
            time.sleep(FINNHUB_DELAY)
            return None

# ============================================================================
# ALPHA VANTAGE (Backup for indicators, FX)
# ============================================================================

def get_alphavantage_overview(ticker: str) -> Optional[Dict]:
    """
    Fetch company overview from Alpha Vantage.
    USE FOR: Backup fundamentals, analyst ratings.
    CACHE: 1 hour
    FREE TIER: 25 calls/day (use sparingly!)
    """
    if not ALPHA_VANTAGE_API_KEY:
        return None
    
    cache_path = _get_cache_path('alphavantage', ticker, 'overview')
    
    # Try cache first
    cached = _read_cache(cache_path, ALPHA_VANTAGE_CACHE_TTL)
    if cached:
        return cached
    
    # Rate-limited fetch (VERY conservative for 25/day limit)
    with _alphavantage_lock:
        try:
            url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={ALPHA_VANTAGE_API_KEY}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                overview = response.json()
                
                if 'Symbol' not in overview:
                    return None  # Invalid response
                
                data = {
                    'ticker': ticker,
                    'name': overview.get('Name', ticker),
                    'sector': overview.get('Sector', 'Unknown'),
                    'industry': overview.get('Industry', 'Unknown'),
                    'market_cap': float(overview.get('MarketCapitalization', 0)),
                    'pe_ratio': float(overview.get('PERatio', 0)),
                    'peg_ratio': float(overview.get('PEGRatio', 0)),
                    'dividend_yield': float(overview.get('DividendYield', 0)),
                    'eps': float(overview.get('EPS', 0)),
                    'analyst_target': float(overview.get('AnalystTargetPrice', 0)),
                    'timestamp': datetime.now().isoformat()
                }
                
                _write_cache(cache_path, data)
                time.sleep(ALPHAVANTAGE_DELAY)
                return data
            else:
                time.sleep(ALPHAVANTAGE_DELAY)
                return None
                
        except Exception as e:
            print(f"⚠️ Alpha Vantage error for {ticker}: {e}")
            time.sleep(ALPHAVANTAGE_DELAY)
            return None

# ============================================================================
# TWELVE DATA (Real-time quotes, time series)
# ============================================================================

def get_twelvedata_quote(ticker: str) -> Optional[Dict]:
    """
    Fetch real-time quote from Twelve Data.
    USE FOR: Live price, comprehensive market data.
    CACHE: 5 minutes
    FREE TIER: 800 calls/day (8 per minute)
    """
    if not TWELVE_DATA_API_KEY:
        return None
    
    cache_path = _get_cache_path('twelvedata', ticker, 'quote')
    
    # Try cache first
    cached = _read_cache(cache_path, TWELVE_DATA_CACHE_TTL)
    if cached:
        return cached
    
    # Rate-limited fetch
    with _twelvedata_lock:
        try:
            url = f"https://api.twelvedata.com/quote?symbol={ticker}&apikey={TWELVE_DATA_API_KEY}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                quote = response.json()
                
                # Check for API error response
                if 'code' in quote or 'status' in quote:
                    print(f"⚠️ Twelve Data API error for {ticker}: {quote.get('message', 'Unknown error')}")
                    time.sleep(TWELVE_DATA_DELAY)
                    return None
                
                # Extract data
                data = {
                    'ticker': ticker,
                    'name': quote.get('name', ticker),
                    'current_price': float(quote.get('close', 0)),
                    'previous_close': float(quote.get('previous_close', 0)),
                    'change': float(quote.get('change', 0)),
                    'percent_change': float(quote.get('percent_change', 0)),
                    'high': float(quote.get('high', 0)),
                    'low': float(quote.get('low', 0)),
                    'open': float(quote.get('open', 0)),
                    'volume': int(quote.get('volume', 0)),
                    'fifty_two_week_high': float(quote.get('fifty_two_week', {}).get('high', 0)),
                    'fifty_two_week_low': float(quote.get('fifty_two_week', {}).get('low', 0)),
                    'timestamp': datetime.now().isoformat()
                }
                
                _write_cache(cache_path, data)
                time.sleep(TWELVE_DATA_DELAY)
                return data
            else:
                print(f"⚠️ Twelve Data HTTP {response.status_code} for {ticker}")
                time.sleep(TWELVE_DATA_DELAY)
                return None
                
        except Exception as e:
            print(f"⚠️ Twelve Data error for {ticker}: {e}")
            time.sleep(TWELVE_DATA_DELAY)
            return None

# ============================================================================
# MARKETSTACK (EOD data, real-time intraday)
# ============================================================================

def get_marketstack_data(ticker: str) -> Optional[Dict]:
    """
    Fetch stock data from MarketStack API.
    USE FOR: End-of-day data, global markets (170k+ tickers).
    CACHE: 15 minutes
    FREE TIER: 1000 calls/month (33/day)
    """
    if not MARKETSTACK_API_KEY:
        return None
    
    cache_path = _get_cache_path('marketstack', ticker, 'eod')
    
    # Try cache first
    cached = _read_cache(cache_path, MARKETSTACK_CACHE_TTL)
    if cached:
        return cached
    
    # Rate-limited fetch
    with _marketstack_lock:
        try:
            # Get latest EOD data (use HTTPS for better compatibility)
            url = f"https://api.marketstack.com/v1/eod/latest"
            params = {
                'access_key': MARKETSTACK_API_KEY,
                'symbols': ticker,
                'limit': 1
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                
                # Check for API error
                if 'error' in result:
                    print(f"⚠️ MarketStack API error for {ticker}: {result['error'].get('message', 'Unknown error')}")
                    time.sleep(MARKETSTACK_DELAY)
                    return None
                
                # Extract data from response
                if not result.get('data') or len(result['data']) == 0:
                    print(f"⚠️ MarketStack: No data for {ticker}")
                    time.sleep(MARKETSTACK_DELAY)
                    return None
                
                quote = result['data'][0]
                
                # Calculate percent change
                close = float(quote.get('close', 0))
                open_price = float(quote.get('open', 0))
                percent_change = ((close - open_price) / open_price * 100) if open_price > 0 else 0.0
                
                data = {
                    'ticker': ticker,
                    'name': quote.get('symbol', ticker),
                    'current_price': close,
                    'open': open_price,
                    'high': float(quote.get('high', 0)),
                    'low': float(quote.get('low', 0)),
                    'previous_close': float(quote.get('adj_close', close)),
                    'change': close - open_price,
                    'percent_change': percent_change,
                    'volume': int(quote.get('volume', 0)),
                    'date': quote.get('date', datetime.now().isoformat()),
                    'exchange': quote.get('exchange', 'Unknown'),
                    'timestamp': datetime.now().isoformat(),
                    'provider': 'marketstack'
                }
                
                _write_cache(cache_path, data)
                time.sleep(MARKETSTACK_DELAY)
                return data
            else:
                print(f"⚠️ MarketStack HTTP {response.status_code} for {ticker}")
                time.sleep(MARKETSTACK_DELAY)
                return None
                
        except Exception as e:
            print(f"⚠️ MarketStack error for {ticker}: {e}")
            time.sleep(MARKETSTACK_DELAY)
            return None

# ============================================================================
# UNIFIED API - Combines all providers intelligently
# ============================================================================

def fetch_quote_multi_provider(ticker: str) -> Optional[Dict]:
    """
    Fetch stock quote with cascading fallback across providers.
    
    Strategy: Yahoo → Finnhub → MarketStack → Alpha Vantage (immediate fallback on error)
    - Try Yahoo Finance first (with safe rate limiting)
    - If Yahoo fails (429, parse error, etc.), immediately try Finnhub
    - If Finnhub fails, try MarketStack
    - If MarketStack fails, try Alpha Vantage
    - Return None only after all providers fail
    
    Returns unified dict with stock data, or None if all providers fail.
    """
    # Try Yahoo Finance first
    try:
        yf_data = get_yfinance_data(ticker)
        if yf_data and yf_data.get('current_price'):
            print(f"✅ Yahoo Finance success for {ticker}")
            return yf_data
        else:
            print(f"⚠️ Yahoo Finance failed for {ticker}, trying Finnhub...")
    except Exception as e:
        print(f"⚠️ Yahoo Finance exception for {ticker}, trying Finnhub... ({e})")
    
    # Fallback to Finnhub if API key available
    if FINNHUB_API_KEY:
        try:
            fh_data = get_finnhub_quote(ticker)
            if fh_data and fh_data.get('current_price'):
                print(f"✅ Finnhub success for {ticker}")
                return fh_data
            else:
                print(f"⚠️ Finnhub failed for {ticker}, trying MarketStack...")
        except Exception as e:
            print(f"⚠️ Finnhub exception for {ticker}, trying MarketStack... ({e})")
    
    # Fallback to MarketStack if API key available
    if MARKETSTACK_API_KEY:
        try:
            ms_data = get_marketstack_data(ticker)
            if ms_data and ms_data.get('current_price'):
                print(f"✅ MarketStack success for {ticker}")
                return ms_data
            else:
                print(f"⚠️ MarketStack failed for {ticker}, trying Alpha Vantage...")
        except Exception as e:
            print(f"⚠️ MarketStack exception for {ticker}, trying Alpha Vantage... ({e})")
    
    # Fallback to Alpha Vantage if API key available
    if ALPHA_VANTAGE_API_KEY:
        try:
            av_data = get_alphavantage_overview(ticker)
            if av_data and av_data.get('current_price'):
                print(f"✅ Alpha Vantage success for {ticker}")
                return av_data
            else:
                print(f"⚠️ Alpha Vantage failed for {ticker}")
        except Exception as e:
            print(f"⚠️ Alpha Vantage exception for {ticker}: {e}")
    
    print(f"❌ All providers failed for {ticker}")
    return None

def get_stock_data_multi(ticker: str) -> Optional[Dict]:
    """
    Fetch stock data from multiple providers in parallel.
    
    Strategy:
    - Yahoo Finance: Historical data, fundamentals (cached 1hr)
    - Finnhub: Real-time quote (cached 5min)
    - MarketStack: EOD data, global markets (cached 15min)
    - Alpha Vantage: Backup fundamentals (cached 1hr, used sparingly)
    
    Returns unified dict with all available data.
    """
    results = {}
    
    # Primary source: Yahoo Finance (fundamental data)
    yf_data = get_yfinance_data(ticker)
    if yf_data:
        results.update(yf_data)
    
    # Real-time quote: Finnhub (if API key available)
    if FINNHUB_API_KEY:
        fh_data = get_finnhub_quote(ticker)
        if fh_data:
            # Update with real-time price
            results['current_price'] = fh_data['current_price']
            results['day_change'] = fh_data['change']
            results['day_change_percent'] = fh_data['percent_change']
            results['day_high'] = fh_data['high']
            results['day_low'] = fh_data['low']
            results['realtime'] = True
    
    # Supplemental: MarketStack (if API key available and no data yet)
    if not results and MARKETSTACK_API_KEY:
        ms_data = get_marketstack_data(ticker)
        if ms_data:
            results.update(ms_data)
    
    # Backup: Alpha Vantage (only if Yahoo failed and we have budget)
    if not results and ALPHA_VANTAGE_API_KEY:
        av_data = get_alphavantage_overview(ticker)
        if av_data:
            results.update(av_data)
    
    return results if results else None

def get_stocks_parallel_multi(tickers: List[str], max_workers: int = 3) -> Dict[str, Dict]:
    """
    Fetch multiple stocks in parallel with cascading fallback across providers.
    
    Args:
        tickers: List of ticker symbols
        max_workers: Number of parallel workers (3 is safe for free tiers)
    
    Returns:
        Dict mapping ticker -> stock data (using fetch_quote_multi_provider with fallback)
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    results = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks using cascading fallback
        future_to_ticker = {
            executor.submit(fetch_quote_multi_provider, ticker): ticker
            for ticker in tickers
        }
        
        # Collect results
        for future in as_completed(future_to_ticker):
            ticker = future_to_ticker[future]
            try:
                data = future.result()
                if data:
                    results[ticker] = data
            except Exception as e:
                print(f"⚠️ Error fetching {ticker}: {e}")
    
    return results

# ============================================================================
# CACHE MANAGEMENT
# ============================================================================

def clear_cache(provider: Optional[str] = None, ticker: Optional[str] = None):
    """
    Clear cache files.
    
    Args:
        provider: If specified, only clear this provider's cache
        ticker: If specified, only clear this ticker's cache
    """
    pattern = "*"
    if provider:
        pattern = f"{provider}_*"
    if ticker:
        safe_ticker = ticker.replace(".", "_").replace("/", "_")
        pattern = f"*_{safe_ticker}_*"
    
    count = 0
    for cache_file in CACHE_DIR.glob(pattern + ".json"):
        cache_file.unlink()
        count += 1
    
    print(f"✅ Cleared {count} cache files")

def get_cache_stats() -> Dict:
    """Get cache statistics."""
    cache_files = list(CACHE_DIR.glob("*.json"))
    
    total_size = sum(f.stat().st_size for f in cache_files)
    
    providers = {}
    for f in cache_files:
        provider = f.name.split('_')[0]
        providers[provider] = providers.get(provider, 0) + 1
    
    return {
        'total_files': len(cache_files),
        'total_size_mb': total_size / (1024 * 1024),
        'by_provider': providers
    }

# ============================================================================
# API KEY VALIDATION
# ============================================================================

def validate_api_keys() -> Dict[str, bool]:
    """Check which API keys are configured."""
    return {
        'finnhub': bool(FINNHUB_API_KEY),
        'alpha_vantage': bool(ALPHA_VANTAGE_API_KEY),
        'marketstack': bool(MARKETSTACK_API_KEY)
    }

def get_provider_status() -> str:
    """Get human-readable status of configured providers."""
    keys = validate_api_keys()
    
    status = ["✅ Yahoo Finance (Always Available)"]
    
    if keys['finnhub']:
        status.append("✅ Finnhub (Real-time quotes)")
    else:
        status.append("⚠️ Finnhub (Not configured - add FINNHUB_API_KEY)")
    
    if keys['marketstack']:
        status.append("✅ MarketStack (Global markets, EOD data)")
    else:
        status.append("⚠️ MarketStack (Not configured - add MARKETSTACK_API_KEY)")
    
    if keys['alpha_vantage']:
        status.append("✅ Alpha Vantage (Backup data)")
    else:
        status.append("⚠️ Alpha Vantage (Not configured - add ALPHA_VANTAGE_API_KEY)")
    
    return "\n".join(status)
