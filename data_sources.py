"""Data access helpers for stock advisor app with parallel API requests."""

import concurrent.futures
import random
import time
import warnings
from threading import Lock
from typing import List, Dict

import pandas as pd
import streamlit as st
import yfinance as yf

from cache_manager import get_cached_stock, set_cached_stock

# Suppress ScriptRunContext warning from threading
warnings.filterwarnings("ignore", message=".*missing ScriptRunContext.*")

# Concurrency and throttling safeguards to reduce yfinance rate-limit errors
MAX_WORKERS = 2  # Reduced from 6 to 2 to prevent 429 errors
BATCH_SIZE = 4   # Reduced batch size
BATCH_PAUSE_SECONDS = 2.0  # Increased delay between batches
DELAY_BETWEEN_REQUESTS = 1.5  # Critical: delay between individual requests
MAX_RETRIES = 3  # Reduced retries
BACKOFF_BASE = 2.0  # Increased backoff
BACKOFF_FACTOR = 2.0
JITTER_MAX = 0.5

# Thread-safe rate limiting
_request_lock = Lock()


@st.cache_data(ttl=180)
def get_stock_data(ticker: str):
    """Fetch live stock data for a single ticker with file-based cache fallback."""
    # Check persistent cache first
    cached = get_cached_stock(ticker)
    if cached:
        return cached

    # Thread-safe rate limiting
    with _request_lock:
        time.sleep(DELAY_BETWEEN_REQUESTS)

    for attempt in range(MAX_RETRIES):
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="3mo")

            if len(hist) > 14 and not hist.empty:
                delta = hist["Close"].diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                rsi_val = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0
            else:
                rsi_val = 50.0

            result = {
                "success": True,
                "ticker": ticker,
                "name": info.get("longName", ticker),
                "price": info.get("currentPrice", 0) or 0,
                "change": info.get("regularMarketChangePercent", 0) or 0,
                "pe": info.get("trailingPE", "N/A"),
                "marketCap": (info.get("marketCap", 0) / 1e9) if info.get("marketCap") else 0,
                "dividend": (info.get("dividendYield", 0) * 100) or 0,
                "rsi": float(rsi_val),
                "volume": info.get("volume", 0) or 0,
                "sector": info.get("sector", "Unknown"),
            }
            
            # Store in persistent cache
            set_cached_stock(ticker, result)
            return result
        except Exception as exc:  # noqa: PERF203
            message = str(exc)
            is_rate_limited = any(keyword in message for keyword in ("429", "Rate", "Too Many", "limit"))

            # Exponential backoff with jitter for throttling
            if is_rate_limited and attempt < MAX_RETRIES - 1:
                delay = BACKOFF_BASE * (BACKOFF_FACTOR ** attempt) + random.uniform(0, JITTER_MAX)
                time.sleep(delay)
                continue

            # For transient network issues, retry with a longer pause
            if attempt < MAX_RETRIES - 1:
                time.sleep(1.0 * (attempt + 1))  # Increased from 0.4 to 1.0
                continue

            # On final failure, return an error dict (don't cache failures)
            return {
                "success": False,
                "ticker": ticker,
                "name": ticker,
                "error": "Data unavailable",
            }

    # After all retries failed
    return {
        "success": False,
        "ticker": ticker,
        "name": ticker,
        "error": "Throttled/Unavailable",
    }


def get_stocks_parallel(tickers: List[str], max_workers: int = MAX_WORKERS) -> List[Dict]:
    """
    Fetch stock data for multiple tickers with batched parallelism to avoid throttling.
    """

    results: List[Dict] = []
    capped_workers = max(1, min(max_workers, MAX_WORKERS))

    def fetch_batch(batch: List[str]) -> List[Dict]:
        batch_results: List[Dict] = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=capped_workers) as executor:
            future_to_ticker = {executor.submit(get_stock_data, ticker): ticker for ticker in batch}
            for future in concurrent.futures.as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    data = future.result(timeout=30)
                    batch_results.append(data)
                except concurrent.futures.TimeoutError:
                    batch_results.append({
                        "success": False,
                        "ticker": ticker,
                        "name": ticker,
                        "error": "Request timeout",
                    })
                except Exception as exc:  # noqa: PERF203
                    batch_results.append({
                        "success": False,
                        "ticker": ticker,
                        "name": ticker,
                        "error": f"Error: {exc}",
                    })
        return batch_results

    # Process tickers in small batches with a pause to respect rate limits
    for start in range(0, len(tickers), BATCH_SIZE):
        batch = tickers[start : start + BATCH_SIZE]
        results.extend(fetch_batch(batch))
        if start + BATCH_SIZE < len(tickers):
            time.sleep(BATCH_PAUSE_SECONDS)

    # Sort results to match original ticker order
    ticker_order = {ticker: i for i, ticker in enumerate(tickers)}
    results.sort(key=lambda x: ticker_order.get(x["ticker"], 999))

    return results


def get_demo_stock(ticker: str):
    """Deterministic demo stock to keep UI usable when live data fails."""
    seed = sum(ord(c) for c in ticker)
    price = 90 + (seed % 220)
    change = ((seed % 25) - 8) / 2
    pe = 10 + (seed % 25)
    rsi = 40 + (seed % 40)
    market_cap = 40 + (seed % 180)
    dividend = seed % 5
    return {
        "success": True,
        "ticker": ticker,
        "name": f"{ticker} (demo)",
        "price": float(price),
        "change": float(change),
        "pe": float(pe),
        "rsi": float(rsi),
        "marketCap": float(market_cap),
        "dividend": float(dividend),
        "sector": "Demo Sector",
        "volume": 15_000_000,
    }
