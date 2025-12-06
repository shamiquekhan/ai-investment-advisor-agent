"""Data access helpers for stock advisor app with parallel API requests."""

import concurrent.futures
import time
from typing import List, Dict

import pandas as pd
import streamlit as st
import yfinance as yf

from cache_manager import get_cached_stock, set_cached_stock


@st.cache_data(ttl=180)
def get_stock_data(ticker: str):
    """Fetch live stock data for a single ticker with file-based cache fallback."""
    # Check persistent cache first
    cached = get_cached_stock(ticker)
    if cached:
        return cached
    
    tries = 3
    for attempt in range(tries):
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
            if "429" in str(exc):
                time.sleep(0.6 * (attempt + 1))
                continue
            # On non-429 error, still return error dict (don't cache failures)
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


def get_stocks_parallel(tickers: List[str], max_workers: int = 10) -> List[Dict]:
    """
    Fetch stock data for multiple tickers in parallel using ThreadPoolExecutor.
    
    Args:
        tickers: List of stock ticker symbols
        max_workers: Maximum number of concurrent API requests (default: 10)
    
    Returns:
        List of stock data dictionaries in the same order as input tickers
    """
    results = []
    
    # Use ThreadPoolExecutor for parallel API requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all fetch tasks
        future_to_ticker = {
            executor.submit(get_stock_data, ticker): ticker 
            for ticker in tickers
        }
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_ticker):
            try:
                data = future.result(timeout=30)  # 30 second timeout per request
                results.append(data)
            except concurrent.futures.TimeoutError:
                ticker = future_to_ticker[future]
                results.append({
                    "success": False,
                    "ticker": ticker,
                    "name": ticker,
                    "error": "Request timeout"
                })
            except Exception as exc:
                ticker = future_to_ticker[future]
                results.append({
                    "success": False,
                    "ticker": ticker,
                    "name": ticker,
                    "error": f"Error: {str(exc)}"
                })
    
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
