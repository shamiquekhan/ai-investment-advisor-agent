"""AI Investment Advisor - Rich UI with Defensive Data Handling

Features
--------
- Zero/NaN prices are skipped (no $0.00 crashes)
- Missing columns handled defensively
- Sequential fetching with small delay to ease rate limits
- 1-hour caching via st.cache_data
- Multi-provider friendly (uses project helpers when available)

Run:
    streamlit run streamlit_app.py
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict, Iterable, List

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Page config must be the first Streamlit call
st.set_page_config(page_title="AI Investment Advisor", page_icon="💼", layout="wide")

# --- Optional project imports with safe fallbacks ---
try:
    from data_sources import get_demo_stock, get_stocks_parallel
except Exception:  # pragma: no cover
    def get_demo_stock(ticker: str) -> Dict[str, Any]:
        return {
            "ticker": ticker,
            "name": ticker,
            "price": 100.0,
            "change": 0.0,
            "rsi": 50,
            "pe": "N/A",
            "marketCap": 0.0,
            "dividend": 0.0,
            "sector": "Unknown",
            "success": True,
        }

    def get_stocks_parallel(tickers: Iterable[str]) -> List[Dict[str, Any]]:
        return [get_demo_stock(t) for t in tickers]

# Import local data manager for robust fallback
try:
    from local_data import get_prices_with_fallback, cleanup_old_snapshots, load_static_prices
    LOCAL_DATA_AVAILABLE = True
except Exception:  # pragma: no cover
    LOCAL_DATA_AVAILABLE = False
    def get_prices_with_fallback(tickers, api_fetch_func, max_cache_age_hours=24):
        return api_fetch_func(tickers)
    def cleanup_old_snapshots(max_age_days=7):
        pass
    def load_static_prices():
        return {}

try:
    from multi_provider import (
        get_stocks_parallel_multi,
        validate_api_keys,
        get_cache_stats,
        clear_cache as clear_multi_cache,
    )
except Exception:  # pragma: no cover
    def get_stocks_parallel_multi(tickers: Iterable[str], max_workers: int = 3) -> Dict[str, Dict[str, Any]]:
        return {t: get_demo_stock(t) for t in tickers}

    def validate_api_keys():
        return {"finnhub": False, "alpha_vantage": False}

    def get_cache_stats():
        return {"total_files": 0, "total_size_mb": 0.0, "by_provider": {}}

    def clear_multi_cache():
        return None

try:
    from news_sentiment import fetch_stock_news, calculate_overall_sentiment
except Exception:  # pragma: no cover
    def fetch_stock_news(ticker: str, max_articles: int = 5, use_ml: bool = False):
        return []

    def calculate_overall_sentiment(articles, use_ml: bool = False):  # noqa: ANN001
        return {"score": 0.0, "label": "🟡 Neutral"}

try:
    # Check if ML should be disabled via environment variable
    import os
    DISABLE_ML = os.getenv("DISABLE_ML", "false").lower() == "true"
    
    if not DISABLE_ML:
        from ml_models import check_ml_availability, preload_models
        ML_AVAILABLE = True
    else:
        print("⚠️ ML models disabled via DISABLE_ML environment variable")
        ML_AVAILABLE = False
        def check_ml_availability():
            return {"transformers_installed": False}
        def preload_models():
            pass
except Exception as e:  # pragma: no cover
    ML_AVAILABLE = False
    print(f"⚠️ ML models not available: {e}")
    def check_ml_availability():
        return {"transformers_installed": False}
    def preload_models():
        pass

try:
    from scoring import calculate_ai_score, get_recommendation
except Exception:  # pragma: no cover
    def calculate_ai_score(data, health_score=50, sentiment_score=0.0):  # noqa: ANN001
        return 5.0

    def get_recommendation(score, **kwargs):  # noqa: ANN001
        if score >= 7:
            rec = "STRONG BUY"
        elif score >= 5:
            rec = "HOLD"
        else:
            rec = "SELL"
        return {"recommendation": rec, "confidence": "Medium", "explanation": "Fallback recommendation"}

try:
    from health_scoring import calculate_health_score, calculate_volatility_risk
except Exception:  # pragma: no cover
    def calculate_health_score(data):
        return {"score": 50, "grade": "C", "breakdown": {}, "explanation": "Health scoring unavailable"}

    def calculate_volatility_risk(data):
        return {"score": 5, "label": "🟡 Moderate Risk", "explanation": "Risk scoring unavailable"}


# --- Helpers ---
def safe_float(x: Any, default: float = float("nan")) -> float:
    try:
        if x is None:
            return default
        f = float(x)
        if f != f:  # NaN
            return default
        return f
    except Exception:
        return default


def is_valid_price(x: Any) -> bool:
    f = safe_float(x, default=float("nan"))
    return not (f != f or f <= 0)


def format_price(x: Any) -> str:
    return f"${safe_float(x):,.2f}" if is_valid_price(x) else "N/A"


def format_change(x: Any) -> str:
    f = safe_float(x, default=float("nan"))
    if f != f:
        return "N/A"
    sign = "+" if f >= 0 else ""
    return f"{sign}{f:.2f}%"


@st.cache_data(ttl=86400)  # 24-hour cache
def fetch_sequential(tickers: List[str], use_multi: bool = True, delay: float = 0.5) -> List[Dict[str, Any]]:
    """
    Fetch data with robust multi-tier fallback:
    1. Live API (cached 24h)
    2. Daily snapshot file
    3. Static CSV
    4. Demo data
    """
    # Clean up old snapshots
    cleanup_old_snapshots(max_age_days=7)
    
    # Use local data manager with fallback chain
    def api_fetch_wrapper(tickers_batch):
        if use_multi:
            try:
                data_map = get_stocks_parallel_multi(tickers_batch, max_workers=2)
                results = []
                for t in tickers_batch:
                    d = data_map.get(t)
                    if d is None or not d.get('success') or d.get('price', 0) <= 0:
                        # Try single fetch as backup
                        fallback = get_stocks_parallel([t])
                        d = fallback[0] if fallback else None
                    if d:
                        results.append(d)
                    time.sleep(delay)  # Rate limiting
                return results
            except Exception as e:
                print(f"⚠️ Multi-provider failed: {e}")
        
        # Single provider fallback
        results = []
        for t in tickers_batch:
            try:
                fetched = get_stocks_parallel([t])
                if fetched and len(fetched) > 0:
                    results.append(fetched[0])
                time.sleep(delay)
            except Exception as e:
                print(f"⚠️ Single fetch failed for {t}: {e}")
        return results
    
    # Use robust fallback system
    if LOCAL_DATA_AVAILABLE:
        return get_prices_with_fallback(tickers, api_fetch_wrapper, max_cache_age_hours=24)
    else:
        # Legacy path without local data
        return api_fetch_wrapper(tickers)


def sanitize_results(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    clean: List[Dict[str, Any]] = []
    for rec in items:
        r = dict(rec or {})
        r["ticker"] = (r.get("ticker") or r.get("symbol") or "UNK").upper()
        r["name"] = r.get("name") or r["ticker"]
        r["price"] = safe_float(r.get("price"))
        r["change"] = safe_float(r.get("change"))
        r["rsi"] = safe_float(r.get("rsi"), 50.0)
        r["pe"] = r.get("pe", "N/A")
        r["marketCap"] = safe_float(r.get("marketCap"), 0.0)
        r["dividend"] = safe_float(r.get("dividend"), 0.0)
        r["success"] = bool(r.get("success", True))
        r["news_articles"] = r.get("news_articles") or []
        r["health_grade"] = r.get("health_grade", "N/A")
        r["sentiment_label"] = r.get("sentiment_label", "🟡 Neutral")
        r["risk_label"] = r.get("risk_label", "🟡 Moderate Risk")
        clean.append(r)
    return clean


# --- UI helpers ---
def rating_from_score(score: float) -> str:
    if score >= 7:
        return "STRONG BUY"
    if score >= 5:
        return "HOLD"
    return "SELL"


def render_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Doto:wght@100..900&display=swap');
        @font-face {
            font-family: 'Ndot';
            src: url('https://intl.nothing.tech/cdn/shop/t/4/assets/Ndot-55.otf?v=18522138017450180331657461025') format('opentype');
            font-weight: 400;
            font-style: normal;
            font-display: swap;
        }
        
        :root {
            --accent-1-50: #FF0000;
            --accent-1-100: #E60000;
            --accent-1-500: #D71921;
            --accent-1-700: #B30000;
            --accent-1-900: #800000;
            --neutral-1-0: #FFFFFF;
            --neutral-1-10: #F7F7F7;
            --neutral-1-50: #F0F0F0;
            --neutral-1-100: #E5E5E5;
            --neutral-1-200: #CCCCCC;
            --neutral-1-300: #B3B3B3;
            --neutral-1-400: #999999;
            --neutral-1-500: #808080;
            --neutral-1-600: #666666;
            --neutral-1-700: #4D4D4D;
            --neutral-1-800: #333333;
            --neutral-1-900: #1A1A1A;
            --neutral-1-1000: #000000;
            --neutral-2-500: #7A7A7A;
        }
        
        .stApp {
            background: var(--neutral-1-0);
            color: var(--neutral-1-1000);
            font-family: 'Ndot', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        
        .main-header {
            font-family: 'Doto', monospace;
            font-size: 3.5rem;
            font-weight: 600;
            letter-spacing: 0.08em;
            color: var(--accent-1-500);
            text-align: center;
            margin: 3rem 0 1.5rem 0;
            text-transform: uppercase;
            line-height: 1.2;
            text-shadow: 0 0 20px rgba(215, 25, 33, 0.3);
            animation: glitch 3s infinite;
        }
        
        @keyframes glitch {
            0%, 100% { text-shadow: 0 0 20px rgba(215, 25, 33, 0.3); }
            50% { text-shadow: 2px 0 rgba(215, 25, 33, 0.5), -2px 0 rgba(0, 0, 0, 0.3); }
        }
        
        .subtitle {
            font-family: 'Doto', monospace;
            font-size: 0.85rem;
            color: var(--neutral-1-600);
            text-align: center;
            letter-spacing: 0.15em;
            font-weight: 400;
            margin-bottom: 2rem;
            text-transform: uppercase;
        }
        
        .card {
            border: 1px solid var(--neutral-1-200);
            padding: 1.2rem;
            border-radius: 2px;
            background: var(--neutral-1-10);
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            margin-bottom: 1rem;
            overflow: hidden;
        }
        
        .card:hover {
            background: var(--neutral-1-50);
            border-color: var(--neutral-1-300);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        }
        
        .card strong {
            color: var(--neutral-1-1000);
            font-family: 'Doto', monospace;
            font-weight: 600;
        }
        
        .stButton > button {
            font-family: 'Doto', monospace;
            background: var(--accent-1-500) !important;
            color: var(--neutral-1-0) !important;
            border: 1px solid var(--accent-1-700) !important;
            border-radius: 2px !important;
            padding: 1rem 2.5rem !important;
            font-size: 0.85rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.12em !important;
            text-transform: uppercase !important;
            transition: all 0.2s ease !important;
        }
        
        .stButton > button:hover {
            background: var(--accent-1-700) !important;
            border-color: var(--accent-1-900) !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(215, 25, 33, 0.3);
        }
        
        div[data-testid="stMetric"] {
            background: var(--neutral-1-10);
            border: 1px solid var(--neutral-1-200);
            border-radius: 2px;
            padding: 1.5rem !important;
        }
        
        div[data-testid="stMetric"]:hover {
            background: var(--neutral-1-50);
            border-color: var(--neutral-1-300);
        }
        
        div[data-testid="stMetricValue"] {
            font-family: 'Doto', monospace;
            color: var(--neutral-1-1000) !important;
            font-size: 2rem !important;
            font-weight: 600 !important;
        }
        
        .stTextInput input, .stSelectbox select, .stMultiSelect {
            background: var(--neutral-1-0) !important;
            color: var(--neutral-1-1000) !important;
            border: 1px solid var(--neutral-1-300) !important;
            border-radius: 2px !important;
            font-family: 'Ndot', sans-serif !important;
            font-size: 0.875rem !important;
            padding: 0.75rem 1rem !important;
        }
        
        .stTextInput input:focus, .stSelectbox select:focus, .stMultiSelect:focus-within {
            border: 1px solid var(--accent-1-500) !important;
            outline: none !important;
            box-shadow: 0 0 0 2px rgba(215, 25, 33, 0.1);
        }
        
        .stDataFrame {
            background: var(--neutral-1-10) !important;
            border: 1px solid var(--neutral-1-200) !important;
            border-radius: 2px !important;
        }
        
        .streamlit-expanderHeader {
            background: var(--neutral-1-10) !important;
            color: var(--neutral-1-1000) !important;
            border: 1px solid var(--neutral-1-200) !important;
            border-radius: 2px !important;
            font-family: 'Doto', monospace !important;
            padding: 1rem 3rem 1rem 1.5rem !important;
            font-weight: 600 !important;
            position: relative !important;
            min-height: 3rem !important;
            display: flex !important;
            align-items: center !important;
        }
        
        .streamlit-expanderHeader:hover {
            background: var(--neutral-1-50) !important;
            border-color: var(--accent-1-500) !important;
        }
        
        /* Hide the default expander icon to prevent overlap */
        button[kind="header"] svg {
            position: absolute !important;
            right: 1rem !important;
            top: 50% !important;
            transform: translateY(-50%) !important;
        }
        
        /* Hide keyboard arrow text artifacts */
        .streamlit-expanderHeader p:first-child::after,
        [data-testid="stExpander"] summary::after {
            content: none !important;
        }
        
        /* Hide any text containing 'keyboard_arrow' */
        p:has-text("keyboard_arrow") {
            display: none !important;
        }
        
        /* Target Streamlit's icon text rendering */
        .streamlit-expanderHeader p {
            overflow: hidden !important;
            text-overflow: clip !important;
        }
        
        /* Ensure only the label text shows */
        [data-testid="stExpander"] summary {
            list-style: none !important;
        }
        
        [data-testid="stExpander"] summary::-webkit-details-marker {
            display: none !important;
        }
        
        /* Hide material icon text names */
        .streamlit-expanderHeader span[class*="icon"],
        .streamlit-expanderHeader span[class*="keyboard"] {
            display: none !important;
        }
        
        .footer {
            background: var(--neutral-1-10);
            border: 1px solid var(--neutral-1-200);
            border-top: 2px solid var(--accent-1-500);
            border-radius: 2px;
            padding: 2rem;
            margin-top: 3rem;
            text-align: center;
            clear: both;
        }
        
        .footer p {
            margin: 0 !important;
            padding: 0 !important;
            line-height: 1.6 !important;
        }
        
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Doto', monospace !important;
            color: var(--neutral-1-1000) !important;
            font-weight: 600 !important;
            letter-spacing: 0.08em !important;
            text-transform: uppercase !important;
            margin-top: 2rem !important;
            margin-bottom: 1rem !important;
            line-height: 1.3 !important;
        }
        
        p, span, div, label {
            font-family: 'Ndot', sans-serif !important;
            font-size: 0.875rem !important;
            color: var(--neutral-1-600) !important;
            line-height: 1.5 !important;
        }
        
        p {
            margin-bottom: 0.5rem !important;
        }
        
        /* Ensure labels don't overlap */
        label {
            display: block !important;
            margin-bottom: 0.5rem !important;
        }
        
        hr {
            border: none;
            height: 1px;
            background: var(--neutral-1-200);
            margin: 3rem 0;
        }
        
        /* Status indicators */
        .stSuccess {
            background: rgba(76, 175, 80, 0.1) !important;
            border-left: 3px solid #4CAF50 !important;
        }
        
        .stWarning {
            background: rgba(255, 152, 0, 0.1) !important;
            border-left: 3px solid #FF9800 !important;
        }
        
        .stError {
            background: rgba(244, 67, 54, 0.1) !important;
            border-left: 3px solid #F44336 !important;
        }
        
        .stInfo {
            background: rgba(33, 150, 243, 0.1) !important;
            border-left: 3px solid #2196F3 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_top_cards(successful: List[Dict[str, Any]]):
    if not successful:
        return
    st.markdown("## 🏆 Top Recommendations")
    cols = st.columns(3)
    for i, res in enumerate(successful[:9]):
        col = cols[i % 3]
        price_display = format_price(res.get("price"))
        change_display = format_change(res.get("change"))
        score = safe_float(res.get("score"), 0.0)
        rating = rating_from_score(score)
        
        # Data source indicator
        source = res.get('source', 'live_api')
        source_icons = {
            'live_api': '🟢',
            'daily_snapshot': '📂',
            'static_csv': '📋',
            'demo': '⚠️'
        }
        source_icon = source_icons.get(source, '🟢')
        source_tooltip = {
            'live_api': 'Live API',
            'daily_snapshot': 'Daily Cache',
            'static_csv': 'Static Data',
            'demo': 'Demo Data'
        }.get(source, 'Live API')
        
        with col:
            st.markdown(
                f"""
                <div class='card'>
                    <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;'>
                        <strong style='font-size:1rem;'>{res.get('ticker','')} {source_icon}</strong>
                        <span style='font-size:0.75rem;color:var(--accent-1-500);font-weight:600;'>{rating}</span>
                    </div>
                    <p style='font-size:1.5rem;margin:0.5rem 0;font-weight:600;line-height:1.2;'>{price_display}</p>
                    <p style='margin:0.3rem 0;color:{'#16a34a' if res.get('change',0)>=0 else '#dc2626'};font-size:0.95rem;'>{change_display}</p>
                    <p style='margin:0.5rem 0 0.3rem 0;color:#555;font-size:0.85rem;'>Score: {score:.1f}/10</p>
                    <p style='margin:0;color:#777;font-size:0.75rem;line-height:1.3;'>Health: {res.get('health_grade','N/A')} • {source_tooltip}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_detailed(successful: List[Dict[str, Any]]):
    if not successful:
        return
    st.markdown("## 📋 Detailed Stock Analysis")
    for res in successful:
        score = safe_float(res.get("score"), 0.0)
        with st.expander(f"{res.get('ticker','')} — {res.get('name','')} | Score {score:.1f}/10"):
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Price", format_price(res.get("price")), format_change(res.get("change")))
            c2.metric("AI Score", f"{score:.1f}/10")
            c3.metric("Health", res.get("health_grade", "N/A"))
            c4.metric("Sentiment", res.get("sentiment_label", "Neutral"))

            st.markdown("**Investment Recommendation**")
            st.write(res.get("recommendation", ""))
            st.caption(res.get("explanation", ""))

            articles = res.get("news_articles", [])
            if articles:
                st.markdown("**Recent News**")
                for art in articles[:5]:
                    st.write(f"- [{art.get('title','Untitled')}]({art.get('link','#')}) ({art.get('published','')})")
            else:
                st.info("No recent news available")


def render_table(successful: List[Dict[str, Any]]):
    if not successful:
        return
    st.markdown("## 📊 Comprehensive Market Data")
    df = pd.DataFrame(successful)

    def _sanitize_price(x):
        try:
            xf = float(x)
            if xf <= 0 or xf != xf:
                return pd.NA
            return xf
        except Exception:
            return pd.NA

    if "price" in df.columns:
        df["price"] = df["price"].apply(_sanitize_price)
    if "change" in df.columns:
        df["change"] = pd.to_numeric(df["change"], errors="coerce")

    display_cols = ["ticker", "name", "score", "health_grade", "price", "change", "rsi", "pe"]
    display_cols = [c for c in display_cols if c in df.columns]

    st.dataframe(
        df[display_cols],
        use_container_width=True,
        hide_index=True,
        column_config={
            "score": st.column_config.NumberColumn("AI Score", format="%.1f", min_value=0, max_value=10),
            "change": st.column_config.NumberColumn("Change %", format="%.2f%%"),
            "price": st.column_config.NumberColumn("Price", format="$%.2f"),
        },
    )


def render_portfolio(successful: List[Dict[str, Any]], amount: float, risk: str):
    if len(successful) < 2:
        return
    st.markdown("## 💼 Optimized Portfolio Allocation")
    weight_configs = {
        "Conservative": [20, 20, 20, 20, 20],
        "Moderate": [25, 25, 20, 15, 15],
        "Aggressive": [30, 25, 20, 15, 10],
    }
    weights = weight_configs.get(risk, weight_configs["Moderate"])[: len(successful)]

    cols = st.columns(min(3, len(successful)))
    for col, res, w in zip(cols, successful[: len(cols)], weights):
        allocation = amount * (w / 100)
        ch = safe_float(res.get("change"), 0.0)
        proj = ch * 1.1
        with col:
            st.markdown(
                f"""
                <div class='card' style='text-align:center;padding:1.5rem;'>
                    <p style='font-size:1.6rem;margin:0;'>{res.get('ticker','')}</p>
                    <p style='margin:0.1rem 0;color:#666;'>{w}% allocation</p>
                    <p style='font-size:1.4rem;margin:0.4rem 0;'>${allocation:,.0f}</p>
                    <p style='margin:0;color:{'#16a34a' if proj>=0 else '#dc2626'}'>{proj:+.1f}%</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_charts(successful: List[Dict[str, Any]], amount: float, risk: str):
    if not successful:
        return
    st.markdown("## 📈 Charts")
    col1, col2 = st.columns(2)

    with col1:
        fig = go.Figure()
        for res in successful[:8]:
            fig.add_trace(
                go.Bar(
                    x=[res.get("ticker", "")],
                    y=[safe_float(res.get("score"), 0.0)],
                    text=[f"{safe_float(res.get('score'),0.0):.1f}"],
                    textposition="outside",
                )
            )
        fig.update_layout(title="AI Confidence Scores", yaxis=dict(range=[0, 10]))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        weight_configs = {
            "Conservative": [20, 20, 20, 20, 20],
            "Moderate": [25, 25, 20, 15, 15],
            "Aggressive": [30, 25, 20, 15, 10],
        }
        weights = weight_configs.get(risk, weight_configs["Moderate"])[: len(successful[:5])]
        labels = [r.get("ticker", "") for r in successful[: len(weights)]]
        fig_pie = go.Figure(
            data=[
                go.Pie(
                    labels=labels,
                    values=weights,
                    hole=0.5,
                    hovertemplate="<b>%{label}</b><br>%{value}%<extra></extra>",
                )
            ]
        )
        fig_pie.update_layout(title="Portfolio Distribution")
        st.plotly_chart(fig_pie, use_container_width=True)


def render_report(successful: List[Dict[str, Any]], amount: float, risk: str, total_return: float):
    if not successful:
        return
    top3 = ", ".join([r.get("ticker", "") for r in successful[:3]])
    st.markdown(
        f"""
        ### 📄 Investment Analysis Report
        **Generated:** {datetime.now().strftime('%B %d, %Y at %H:%M')}

        - Top holdings: {top3}
        - Expected annual return: {total_return:.2f}%
        - Risk profile: {risk}
        - Stocks analyzed: {len(successful)}

        **Recommended Actions**
        1. Diversify per the allocation above
        2. Set 15% stop-loss per position
        3. Rebalance monthly or when drift >10%
        4. Track earnings reports
        """
    )


def footer():
    st.markdown(
        """
        <div class='footer'>
            <p>AI Investment Advisor • Educational use only. Consult a licensed advisor before investing.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --- Main app ---
def main() -> None:
    render_css()
    st.markdown(
        """
        <h1 class='main-header'>
            <span style='font-size: 0.7em;'>••• </span>AI INVESTMENT ADVISOR<span style='font-size: 0.7em;'> •••</span>
        </h1>
        """, 
        unsafe_allow_html=True
    )
    st.markdown(
        "<p class='subtitle'>> PROFESSIONAL MARKET ANALYSIS | REAL-TIME DATA | AI-POWERED INSIGHTS</p>", 
        unsafe_allow_html=True
    )

    api_keys = validate_api_keys()
    cache_stats = get_cache_stats()

    # Stock selection
    with st.container():
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("### 📈 Select Stocks to Analyze")
            popular = [
                "AAPL",
                "MSFT",
                "NVDA",
                "GOOGL",
                "AMZN",
                "TSLA",
                "META",
                "JPM",
                "UNH",
                "V",
            ]
            selected = st.multiselect("Popular stocks", popular, default=["AAPL", "MSFT", "NVDA", "GOOGL"])
        with col2:
            st.markdown("### ➕ Custom")
            custom = st.text_input("Ticker", placeholder="BTC-USD, RELIANCE.NS").strip().upper()
            if custom:
                for t in [c.strip().upper() for c in custom.split(",") if c.strip()]:
                    if t not in selected:
                        selected.append(t)

    st.markdown("---")
    col_api1, col_api2, col_api3 = st.columns(3)
    with col_api1:
        st.markdown("**Yahoo Finance**")
        st.success("✅ Active (1hr cache)")
        st.caption(f"📦 {cache_stats['by_provider'].get('yfinance', 0)} cached")
    with col_api2:
        st.markdown("**Finnhub**")
        if api_keys.get("finnhub"):
            st.success("✅ Active")
        else:
            st.warning("⚠️ Not configured")
    with col_api3:
        st.markdown("**Alpha Vantage**")
        if api_keys.get("alpha_vantage"):
            st.success("✅ Active")
        else:
            st.warning("⚠️ Not configured")

    st.info("Smart load distribution with cache; sequential fetch avoids rate limits.")
    
    # Show available static data
    if LOCAL_DATA_AVAILABLE:
        static_data = load_static_prices()
        if static_data:
            st.success(f"📂 {len(static_data)} tickers available in local fallback (updated 2025-12-06)")

    use_multi = st.checkbox("🚀 Enable Multi-Provider Mode", value=True)
    use_demo = st.checkbox("Use sample data if throttled", value=False)
    
    # ML sentiment control
    ml_status = check_ml_availability()
    if ml_status.get("transformers_installed"):
        use_ml_sentiment = st.checkbox("🤖 Use ML-Powered Sentiment (FinBERT)", value=True,
                                      help="Uses HuggingFace FinBERT for accurate financial sentiment")
        st.success("✅ ML models loaded (FinBERT)")
    else:
        use_ml_sentiment = False
        st.info("💡 Install ML models: `pip install transformers torch` for enhanced sentiment")

    col_cache1, col_cache2 = st.columns([2, 1])
    col_cache1.caption(f"Cache: {cache_stats['total_files']} files ({cache_stats['total_size_mb']:.2f} MB)")
    with col_cache2:
        if st.button("🗑️ Clear Cache"):
            try:
                st.cache_data.clear()
                clear_multi_cache()
            except Exception:
                st.cache_data.clear()
            st.success("Cache cleared")
            st.rerun()

    # Investor profile (optional)
    with st.expander("👤 Investor Profile (optional)", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            age = st.number_input("Age", 18, 100, 30)
            amount = st.number_input("Investment Amount ($)", 1000, 1_000_000, 50_000, step=1000)
        with c2:
            risk = st.selectbox("Risk Tolerance", ["Conservative", "Moderate", "Aggressive"], index=1)
            goal = st.text_input("Goal", placeholder="Retirement, House, etc.")

    if st.button("🚀 Analyze Selected Stocks", type="primary"):
        if not selected:
            st.error("Select at least one stock")
        elif len(selected) > 15:
            st.error("Maximum 15 stocks")
        else:
            st.session_state.selected = list(dict.fromkeys(selected))
            st.session_state.amount = amount
            st.session_state.risk = risk
            st.rerun()

    if "selected" in st.session_state:
        tickers = st.session_state.selected
        amount = st.session_state.get("amount", 50_000)
        risk = st.session_state.get("risk", "Moderate")

        st.success(f"Analyzing {len(tickers)} stocks...")

        with st.spinner("Fetching data..."):
            raw = fetch_sequential(tickers, use_multi=use_multi)
            if not raw and use_demo:
                raw = [get_demo_stock(t) for t in tickers]

        results = sanitize_results(raw)

        # Enrich with scores and recommendations
        enriched: List[Dict[str, Any]] = []
        for res in results:
            if not is_valid_price(res.get("price")) or not res.get("success", True):
                continue
            
            # Calculate health score
            try:
                health = calculate_health_score(res)
                health_score = health.get("score", 50)
                health_grade = health.get("grade", "C")
            except Exception:
                health_score = 50
                health_grade = "C"
            
            # Calculate volatility risk
            try:
                volatility_risk = calculate_volatility_risk(res)
                risk_label = volatility_risk.get("label", "🟡 Moderate Risk")
            except Exception:
                risk_label = "🟡 Moderate Risk"
            
            try:
                score = calculate_ai_score(res, health_score=health_score, sentiment_score=0.0)
            except Exception:
                score = 5.0
            try:
                rec = get_recommendation(score, health_grade=health_grade, sentiment_label=res.get("sentiment_label", "Neutral"), risk_label=risk_label)
            except Exception:
                rec = {"recommendation": rating_from_score(score), "confidence": "Medium", "explanation": "Fallback"}

            enriched.append(
                {
                    **res,
                    "score": score,
                    "health_score": health_score,
                    "health_grade": health_grade,
                    "risk_label": risk_label,
                    "recommendation": rec.get("recommendation"),
                    "confidence": rec.get("confidence", "N/A"),
                    "explanation": rec.get("explanation", ""),
                }
            )

        # Fetch news + sentiment (sequential, defensive)
        for item in enriched:
            try:
                articles = fetch_stock_news(item.get("ticker", ""), max_articles=5, use_ml=use_ml_sentiment)
                sentiment = calculate_overall_sentiment(articles, use_ml=use_ml_sentiment)
                item["news_articles"] = articles
                item["sentiment_label"] = sentiment.get("label", "🟡 Neutral")
                item["sentiment_score"] = sentiment.get("score", 0.0)
                item["sentiment_method"] = sentiment.get("method", "keyword")
            except Exception:
                item["news_articles"] = []
                item["sentiment_label"] = "🟡 Neutral"
                item["sentiment_score"] = 0.0
                item["sentiment_method"] = "fallback"

        enriched.sort(key=lambda x: safe_float(x.get("score"), 0.0), reverse=True)

        if enriched:
            render_top_cards(enriched)
            render_detailed(enriched)
            render_table(enriched)
            render_portfolio(enriched, amount, risk)
            render_charts(enriched, amount, risk)

            total_return = sum([safe_float(r.get("change"), 0.0) for r in enriched[:5]])
            render_report(enriched, amount, risk, total_return)
        else:
            st.warning("No valid stock data; try again or enable demo data.")

    footer()


if __name__ == "__main__":
    main()

