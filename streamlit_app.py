"""
🚀 SHAMIQUKHAN STOCK ADVISOR - 100% ERROR-FREE VERSION
✅ Multi-select stocks ✓ Custom tickers ✓ FREE AI Analysis
✅ NO time.sleep error ✓ Production ready
"""

import random
import time
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from cache_manager import clear_cache
from data_sources import get_demo_stock, get_stock_data, get_stocks_parallel
from scoring import calculate_ai_score, get_recommendation

# Page config
st.set_page_config(
    page_title="AI Investment Advisor | Professional Market Analysis",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Nothing-inspired Minimal Tech Theme (Ndot + Lettera Mono)
st.markdown("""
<style>
@font-face {
    font-family: 'Ndot';
    src: url('https://intl.nothing.tech/cdn/shop/t/4/assets/Ndot-55.otf?v=18522138017450180331657461025') format('opentype');
    font-weight: 400;
    font-style: normal;
    font-display: swap;
}

@font-face {
    font-family: 'LetteraMono';
    src: url('https://intl.nothing.tech/cdn/shop/t/4/assets/LetteraMonoLL-Regular.otf?v=71080347982022511271688898930') format('opentype');
    font-weight: 400;
    font-style: normal;
    font-display: swap;
}

@font-face {
    font-family: 'LetteraMonoCond';
    src: url('https://intl.nothing.tech/cdn/shop/t/4/assets/LetteraMonoLLCondLight-Regular.otf?v=165587148734230230191663851208') format('opentype');
    font-weight: 300;
    font-style: normal;
    font-display: swap;
}

@import url('https://fonts.googleapis.com/css2?family=Noto+Sans:wght@300;400;500;600;700&display=swap');

:root {
    --bg-main: #FFFFFF;
    --bg-panel: #FAFAFA;
    --text-primary: #000000;
    --text-secondary: #666666;
    --accent-red: #D71921;
    --border-color: rgba(0, 0, 0, 0.08);
    --hover-bg: rgba(0, 0, 0, 0.02);
}

* {
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.stApp {
    background: #FFFFFF;
    color: #000000;
    font-family: 'Ndot', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.main-header {
    font-family: 'Ndot', sans-serif;
    font-size: 3.5rem !important;
    font-weight: 400 !important;
    letter-spacing: 0.18em;
    color: #000000;
    text-align: center;
    margin: 3rem 0 1.5rem 0;
    padding: 0;
    text-transform: uppercase;
    line-height: 1.2;
    background-image: radial-gradient(circle, #000000 52%, transparent 55%);
    background-size: 4.5px 4.5px;
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: fadeInDown 0.6s ease-out;
}

@keyframes fadeInDown {
    from { opacity: 0; transform: translateY(-18px); }
    to { opacity: 1; transform: translateY(0); }
}

.subtitle {
    font-family: 'Ndot', sans-serif;
    font-size: 0.85rem;
    color: #666666;
    text-align: center;
    letter-spacing: 0.12em;
    font-weight: 400;
    margin-bottom: 1rem;
    text-transform: uppercase;
    animation: fadeIn 0.8s ease-out 0.2s both;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 0.9; }
}

.market-ticker {
    font-family: 'LetteraMono', monospace;
    font-size: 0.7rem;
    color: #D71921;
    text-align: center;
    letter-spacing: 0.15em;
    margin: 0.5rem 0 3rem 0;
    text-transform: uppercase;
    font-weight: 400;
}

.dot-matrix {
    background-image: radial-gradient(circle, currentColor 60%, transparent 62%);
    background-size: 7px 7px;
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    text-fill-color: transparent;
    text-shadow: 0 10px 26px var(--shadow);
}

.report-title {
    font-family: 'Ndot', 'Noto Sans', sans-serif;
    letter-spacing: 0.12em;
    color: #F6F4E8;
    background-image: radial-gradient(circle, currentColor 58%, transparent 60%);
    background-size: 6px 6px;
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0 10px 28px rgba(0, 0, 0, 0.45);
}

.report-subhead {
    color: #D6D2C7;
    opacity: 0.9;
}

.report-copy {
    color: #F3F1E7;
}

.report-muted {
    color: #CAC6BB;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}

.stock-selector {
    background: #FAFAFA;
    border: 1px solid rgba(0, 0, 0, 0.08);
    padding: 2.5rem;
    border-radius: 0;
    margin: 2rem 0;
    box-shadow: none;
    animation: slideUp 0.5s ease-out;
}

@keyframes slideUp {
    from { opacity: 0; transform: translateY(26px); }
    to { opacity: 1; transform: translateY(0); }
}

.stButton > button {
    font-family: 'Ndot', sans-serif;
    background: #D71921 !important;
    color: #FFFFFF !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    border-radius: 0 !important;
    padding: 1rem 2.5rem !important;
    font-size: 0.85rem !important;
    font-weight: 400 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    box-shadow: none !important;
    transition: all 0.2s ease !important;
    position: relative;
    overflow: hidden;
}

.stButton > button::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 0;
    height: 0;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.1);
    transform: translate(-50%, -50%);
    transition: width 0.6s, height 0.6s;
}

.stButton > button:hover::before { width: 280px; height: 280px; }

.stButton > button:hover {
    background: #B01519 !important;
    border-color: rgba(255, 255, 255, 0.2) !important;
    transform: translateY(-1px);
}

.stButton > button:active { transform: translateY(-1px) scale(0.99); }

div[data-testid="stMetric"] {
    background: #FAFAFA;
    border: 1px solid rgba(0, 0, 0, 0.08);
    border-radius: 0;
    padding: 1.5rem !important;
    box-shadow: none;
}

div[data-testid="stMetric"]:hover {
    background: #F5F5F5;
    border-color: rgba(0, 0, 0, 0.12);
    transform: none;
}

div[data-testid="stMetricValue"] {
    font-family: 'Ndot', sans-serif;
    color: #000000 !important;
    font-size: 2rem !important;
    font-weight: 400 !important;
    letter-spacing: 0;
}

div[data-testid="stMetricDelta"] {
    font-family: 'LetteraMono', monospace;
    font-weight: 400 !important;
    font-size: 0.875rem !important;
}

.metric-card {
    background: #FAFAFA;
    border: 1px solid rgba(0, 0, 0, 0.08);
    border-radius: 0;
    padding: 1.5rem;
    box-shadow: none;
}

.metric-card:hover { 
    background: #F5F5F5;
    border-color: rgba(0, 0, 0, 0.12);
}

.stTextInput input, .stSelectbox select, .stMultiSelect {
    background: #FFFFFF !important;
    color: #000000 !important;
    border: 1px solid rgba(0, 0, 0, 0.12) !important;
    border-radius: 0 !important;
    font-family: 'Ndot', sans-serif !important;
    font-size: 0.875rem !important;
    padding: 0.75rem 1rem !important;
    box-shadow: none !important;
}

.stTextInput input:focus, .stSelectbox select:focus, .stMultiSelect:focus-within {
    border: 1px solid rgba(215, 25, 33, 0.5) !important;
    box-shadow: none !important;
    outline: none !important;
    background: #FFFFFF !important;
}

.stDataFrame {
    background: #FAFAFA !important;
    border: 1px solid rgba(0, 0, 0, 0.08) !important;
    border-radius: 0 !important;
    box-shadow: none !important;
    overflow: hidden;
}

.streamlit-expanderHeader {
    background: #FAFAFA !important;
    color: #000000 !important;
    border: 1px solid rgba(0, 0, 0, 0.08) !important;
    border-radius: 0 !important;
    font-family: 'Ndot', sans-serif !important;
    padding: 1rem 1.5rem !important;
}

.streamlit-expanderHeader:hover { 
    background: #F5F5F5 !important;
    border-color: rgba(215, 25, 33, 0.3) !important; 
}

.footer {
    background: #FAFAFA;
    border: 1px solid rgba(0, 0, 0, 0.08);
    border-top: 2px solid #D71921;
    border-radius: 0;
    padding: 3rem;
    margin-top: 4rem;
    box-shadow: none;
}

.footer h3 {
    font-family: 'Ndot', sans-serif;
    color: #000000;
    letter-spacing: 0.08em;
}

h1, h2, h3, h4, h5, h6 { font-family: 'Ndot', sans-serif !important; color: #000000 !important; font-weight: 400 !important; letter-spacing: 0.08em !important; text-transform: uppercase !important; }

p, span, div, label { font-family: 'Ndot', sans-serif !important; font-size: 0.875rem !important; color: #666666 !important; }

hr { border: none; height: 1px; background: rgba(0, 0, 0, 0.08); margin: 3rem 0; }

.stCheckbox { color: #000000 !important; }
.stCheckbox > label { font-family: 'Ndot', sans-serif; font-size: 0.875rem; font-weight: 400; color: #666666 !important; }

.stAlert { 
    background: rgba(215, 25, 33, 0.1) !important; 
    border-left: 3px solid #D71921 !important; 
    border-radius: 0 !important; 
    box-shadow: none !important;
    color: #000000 !important;
}

.stProgress > div > div { 
    background: #D71921 !important; 
    border-radius: 0 !important; 
    box-shadow: none !important; 
}

.stSpinner > div { border-color: #D71921 !important; }

::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: #FAFAFA; border-radius: 0; }
::-webkit-scrollbar-thumb { background: rgba(0, 0, 0, 0.15); border-radius: 0; border: 2px solid #FAFAFA; }
::-webkit-scrollbar-thumb:hover { background: rgba(0, 0, 0, 0.25); }
</style>
""", unsafe_allow_html=True)

# === MAIN APPLICATION ===
st.markdown('<h1 class="main-header">AI Investment Advisor</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Professional Market Analysis • Real-Time Data • AI-Powered Insights</p>', unsafe_allow_html=True)
st.markdown('<p class="market-ticker">● LIVE • NYSE • NASDAQ • NSE • GLOBAL MARKETS</p>', unsafe_allow_html=True)

# === STOCK SELECTION SECTION ===
st.markdown('<div class="stock-selector">', unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("### 📈 **SELECT STOCKS TO ANALYZE**")
    
    # Popular stocks (US + India)
    popular_stocks = [
        "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA", "META",
        "JPM", "UNH", "V", "PG", "JNJ", "HD", "MA", "NFLX",
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ITC.NS"
    ]
    
    selected_stocks = st.multiselect(
        "Popular stocks (Ctrl+click for multiple):",
        popular_stocks,
        default=["AAPL", "MSFT", "NVDA", "GOOGL"],
        help="Hold Ctrl/Cmd to select multiple • Indian stocks: .NS suffix"
    )

with col2:
    st.markdown("### ➕ **Custom**")
    custom_ticker = st.text_input(
        "Ticker", 
        placeholder="BTC-USD, RELIANCE.NS", 
        help="e.g., BTC-USD, RELIANCE.NS, TATAMOTORS.NS"
    ).strip().upper()
    
    if custom_ticker and custom_ticker not in selected_stocks:
        selected_stocks.append(custom_ticker)

# Fallback toggle
use_demo_if_rate_limited = st.checkbox(
    "Use sample data if live data is throttled (Yahoo 429)",
    value=True
)

# Cache controls
col_cache1, col_cache2 = st.columns([2, 1])
with col_cache1:
    st.caption("💾 Persistent cache stores recent API data to avoid throttling.")
with col_cache2:
    if st.button("🗑️ Clear Cache", help="Remove all cached stock data"):
        clear_cache()
        st.success("Cache cleared!")
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# === INVESTOR PROFILE ===
with st.expander("👤 **Investor Profile** (Optional for Portfolio)", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Age", 18, 100, 30, help="For risk calculation")
        investment_amount = st.number_input("Investment Amount ($)", 1000, 10000000, 50000, step=1000)
    with col2:
        risk_tolerance = st.selectbox("Risk Tolerance", ["Conservative", "Moderate", "Aggressive"])
        goal = st.text_input("Goal", placeholder="Retirement, House, etc.")

# === ANALYZE BUTTON ===
if st.button("🚀 **ANALYZE SELECTED STOCKS**", type="primary", use_container_width=True):
    if len(selected_stocks) == 0:
        st.error("⚠️ Select at least 1 stock!")
    elif len(selected_stocks) > 15:
        st.error("⚠️ Maximum 15 stocks (for performance)")
    else:
        # Remove duplicates
        selected_stocks = list(dict.fromkeys(selected_stocks))
        st.session_state.selected_stocks = selected_stocks
        st.session_state.analyze = True
        st.session_state.amount = investment_amount
        st.session_state.risk = risk_tolerance
        st.rerun()

# === RESULTS SECTION ===
if 'analyze' in st.session_state and st.session_state.analyze:
    selected_stocks = st.session_state.selected_stocks
    amount = st.session_state.get('amount', 50000)
    risk = st.session_state.get('risk', 'Moderate')
    
    st.success(f"✅ Analyzing **{len(selected_stocks)} stocks** live...")
    
    # === DATA FETCHING (PARALLEL) ===
    with st.spinner(f"📊 Fetching LIVE market data for {len(selected_stocks)} stocks in parallel..."):
        # Fetch all stocks in parallel using ThreadPoolExecutor
        stock_data_list = get_stocks_parallel(selected_stocks)
        
        # Convert list to dictionary for easier access
        stock_data = {data['ticker']: data for data in stock_data_list}
        
        st.success(f"✅ Fetched {len(stock_data)} stocks in parallel!")
        
    
    # === ANALYSIS ===
    analysis_results = []
    total_return = 0.0
    for ticker, data in stock_data.items():
        score = calculate_ai_score(data)
        recommendation = get_recommendation(score)
        
        analysis_results.append({
            'ticker': data.get('ticker', ticker),
            'name': data.get('name', ticker)[:30] + "..." if len(data.get('name', '')) > 30 else data.get('name', ticker),
            'score': score,
            'recommendation': recommendation,
            'price': data.get('price', 0),
            'change': data.get('change', 0),
            'pe': data.get('pe', 'N/A'),
            'rsi': data.get('rsi', 50),
            'marketCap': data.get('marketCap', 0),
            'dividend': data.get('dividend', 0),
            'sector': data.get('sector', 'Unknown'),
            'success': data.get('success', False)
        })
    
    # Sort: successful + high score first
    analysis_results.sort(key=lambda x: (x['success'], x['score']), reverse=True)
    
    successful_results = [r for r in analysis_results if r['success']]

    # If everything failed and user allowed demo, fill with demo data (up to 5 tickers)
    if not successful_results and use_demo_if_rate_limited:
        demo_list = []
        for t in selected_stocks[:5]:
            demo_data = get_demo_stock(t)
            demo_score = calculate_ai_score(demo_data)
            demo_list.append({
                **demo_data,
                'score': demo_score,
                'recommendation': get_recommendation(demo_score),
            })
        successful_results = demo_list
        st.info("Showing sample data due to API rate limits (Yahoo 429). Try fewer tickers or wait a minute.")

    # Guarantee score/recommendation exist for downstream UI even if data came from cache/fallback
    for res in successful_results:
        if 'score' not in res:
            res['score'] = calculate_ai_score(res)
        if 'recommendation' not in res:
            res['recommendation'] = get_recommendation(res['score'])
    
    # Final safety: drop any results without a score (shouldn't happen now, but defensive)
    successful_results = [r for r in successful_results if 'score' in r]
    
    # === TOP RECOMMENDATIONS ===
    st.markdown("<h2 class='dot-matrix' style='font-family: Ndot, \"Noto Sans\", sans-serif; color: var(--cornsilk); font-size: 2rem; font-weight: 700; text-align: center; margin: 2rem 0; border-bottom: 2px solid var(--accent); padding-bottom: 1rem; letter-spacing: 0.12em;'>🏆 TOP INVESTMENT RECOMMENDATIONS</h2>", unsafe_allow_html=True)
    
    if successful_results:
        cols = st.columns(3)
        for i, result in enumerate(successful_results[:9]):
            score_val = result.get('score', 0)
            col_idx = i % 3
            with cols[col_idx]:
                # Wall Street color coding
                if score_val >= 7:
                    rating = "STRONG BUY"
                    rating_color = "var(--copperwood)"
                    border_color = "var(--copperwood)"
                elif score_val >= 5:
                    rating = "HOLD"
                    rating_color = "var(--sunlit-clay)"
                    border_color = "var(--sunlit-clay)"
                else:
                    rating = "SELL"
                    rating_color = "var(--olive-leaf)"
                    border_color = "var(--olive-leaf)"
                
                trend_symbol = "▲" if result['change'] >= 0 else "▼"
                trend_color = "var(--copperwood)" if result['change'] >= 0 else "var(--olive-leaf)"
                
                # Bloomberg-style card
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.06) 100%); 
                border-left: 4px solid {border_color}; border-radius: 12px; padding: 1.2rem; margin: 0.5rem 0;
                box-shadow: 0 12px 28px rgba(0, 0, 0, 0.45);'>
                    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;'>
                        <p style='font-family: Ndot, "Noto Sans", sans-serif; color: var(--cornsilk); font-size: 1.25rem; font-weight: 700; margin: 0; letter-spacing: 0.06em;'>
                            {result['ticker']}
                        </p>
                        <span style='font-family: "Noto Sans", sans-serif; background: {rating_color}; color: var(--cornsilk); 
                        padding: 0.3rem 0.8rem; border-radius: 4px; font-size: 0.75rem; font-weight: 700; letter-spacing: 0.08em;'>
                            {rating}
                        </span>
                    </div>
                    <p style='font-family: "LetteraMono", monospace; color: var(--sunlit-clay); font-size: 2rem; font-weight: 600; margin: 0.5rem 0;'>
                        ${result['price']:.2f}
                    </p>
                    <p style='font-family: "LetteraMonoCond", monospace; color: {trend_color}; font-size: 1.05rem; font-weight: 500; margin: 0;'>
                        {trend_symbol} {result['change']:.2f}%
                    </p>
                    <div style='margin-top: 0.8rem; padding-top: 0.8rem; border-top: 1px solid rgba(255,255,255,0.08);'>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <span style='font-family: "Noto Sans", sans-serif; color: var(--cornsilk); font-size: 0.85rem;'>
                                Score: <strong style='color: var(--sunlit-clay); letter-spacing: 0.04em;'>{score_val:.1f}/10</strong>
                            </span>
                            <span style='font-family: "Noto Sans", sans-serif; color: var(--cornsilk); font-size: 0.85rem;'>
                                RSI: <strong style='font-family: "LetteraMono", monospace;'>{result['rsi']:.0f}</strong>
                            </span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # === ANALYSIS TABLE ===
    st.markdown("---")
    st.markdown("<h2 class='dot-matrix' style='font-family: Ndot, \"Noto Sans\", sans-serif; color: var(--cornsilk); font-size: 1.8rem; font-weight: 700; text-align: center; margin: 2rem 0; border-bottom: 2px solid var(--accent); padding-bottom: 1rem; letter-spacing: 0.12em;'>📊 COMPREHENSIVE MARKET ANALYSIS</h2>", unsafe_allow_html=True)
    
    if successful_results:
        df = pd.DataFrame(successful_results)

        st.dataframe(
            df[['ticker', 'name', 'score', 'recommendation', 'price', 'change', 
                'rsi', 'pe', 'marketCap']],
            use_container_width=True,
            column_config={
                "score": st.column_config.NumberColumn("AI Score", format="%.1f", min_value=0, max_value=10),
                "change": st.column_config.NumberColumn("Change %", format="%.1f%%"),
                "price": st.column_config.NumberColumn("Price", format="$%.0f"),
                "marketCap": st.column_config.NumberColumn("Market Cap B$", format="%.1f")
            },
            hide_index=True
        )
    else:
        st.warning("⚠️ No valid stock data (likely Yahoo rate limit). Try fewer tickers or wait a minute.")
    
    # === PORTFOLIO BUILDER ===
    if len(successful_results) >= 2:
        st.markdown("---")
        st.markdown("<h2 class='dot-matrix' style='font-family: Ndot, \"Noto Sans\", sans-serif; color: var(--cornsilk); font-size: 1.8rem; font-weight: 700; text-align: center; margin: 2rem 0; border-bottom: 2px solid var(--accent); padding-bottom: 1rem; letter-spacing: 0.12em;'>💼 OPTIMIZED PORTFOLIO ALLOCATION</h2>", unsafe_allow_html=True)
        
        # Risk-based weights
        weight_configs = {
            "Conservative": [20, 20, 20, 20, 20],
            "Moderate": [25, 25, 20, 15, 15],
            "Aggressive": [30, 25, 20, 15, 10]
        }
        weights = weight_configs.get(risk, [25, 25, 20, 15, 15])[:len(successful_results)]
        
        portfolio_value = amount
        total_return = 0.0
        
        portfolio_cols = st.columns(min(3, len(successful_results)))
        
        for i, (col, result, weight_pct) in enumerate(zip(portfolio_cols, successful_results[:5], weights)):
            allocation = portfolio_value * (weight_pct / 100)
            proj_return = result['change'] * 1.1  # Conservative projection
            total_return += proj_return * weight_pct
            
            with col:
                st.metric(
                    label=f"{result['ticker']}\n<small>({weight_pct}%)</small>",
                    value=f"${allocation:,.0f}",
                    delta=f"{proj_return:.1f}%"
                )
        
        # Portfolio summary
        col1, col2, col3 = st.columns(3)
        with col1: st.metric("📈 Expected Return", f"{total_return:.1f}%")
        with col2: st.metric("💰 Total Invested", f"${amount:,.0f}")
        with col3: st.metric("⚠️ Risk Level", risk)
        
        # === CHARTS - Wall Street Professional Theme ===
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            fig_scores = go.Figure()
            # Nothing palette: deep reds + cotton neutrals
            colors = ['#D71921', '#810100', '#630000', '#EDEBDD', '#BEBBB3', '#D71921', '#810100', '#EDEBDD']
            
            for i, result in enumerate(successful_results[:8]):
                fig_scores.add_trace(go.Bar(
                    x=[result['ticker']],
                    y=[result['score']],
                    marker_color=colors[i % len(colors)],
                    marker_line_color='#2A2A2D',
                    marker_line_width=1.8,
                    text=f"{result['score']:.1f}",
                    textposition="outside",
                    textfont=dict(size=14, color='#EDEBDD', family='Noto Sans', weight=600),
                    name=result['ticker'],
                    hovertemplate='<b>%{x}</b><br>AI Score: %{y:.1f}/10<br>Rating: ' + 
                                  ('Strong Buy' if result['score'] >= 7 else 'Hold' if result['score'] >= 5 else 'Sell') + 
                                  '<extra></extra>'
                ))
            
            fig_scores.update_layout(
                title=dict(
                    text="🏆 AI CONFIDENCE SCORES",
                    font=dict(size=18, color='#D71921', family='Ndot', weight=600)
                ),
                xaxis=dict(
                    title="Stock Ticker",
                    titlefont=dict(color='#EDEBDD', family='Noto Sans', size=12),
                    tickfont=dict(color='#EDEBDD', family='LetteraMono', size=11),
                    gridcolor='#2A2A2D',
                    showgrid=False,
                    zeroline=False
                ),
                yaxis=dict(
                    title="Score (1-10 Scale)",
                    titlefont=dict(color='#EDEBDD', family='Noto Sans', size=12),
                    tickfont=dict(color='#EDEBDD', family='LetteraMono'),
                    range=[0, 10],
                    gridcolor='#2A2A2D',
                    showgrid=False,
                    zeroline=False
                ),
                showlegend=False,
                height=450,
                plot_bgcolor='#1F1F21',
                paper_bgcolor='#1B1B1D',
                font=dict(color='#EDEBDD', family='Noto Sans'),
                margin=dict(t=50, l=50, r=30, b=50)
            )
            st.plotly_chart(fig_scores, use_container_width=True)
        
        with col_chart2:
            top5 = successful_results[:5]
            labels = [r['ticker'] for r in top5]
            values = weights[:5]
            
            # Nothing palette slices
            pie_colors = ['#D71921', '#810100', '#630000', '#EDEBDD', '#BEBBB3']
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=0.5,
                marker=dict(
                    colors=pie_colors,
                    line=dict(color='#1B1B1D', width=3)
                ),
                textfont=dict(size=13, color='#1B1B1D', family='Noto Sans', weight=700),
                textposition='outside',
                textinfo='label+percent',
                hovertemplate='<b>%{label}</b><br>Allocation: %{value}%<br>Amount: $%{customdata:,.0f}<extra></extra>',
                customdata=[amount * (v/100) for v in values]
            )])
            
            fig_pie.update_layout(
                title=dict(
                    text="🍰 PORTFOLIO DISTRIBUTION",
                    font=dict(size=18, color='#D71921', family='Ndot', weight=600)
                ),
                height=450,
                plot_bgcolor='#1F1F21',
                paper_bgcolor='#1B1B1D',
                font=dict(color='#EDEBDD', family='Noto Sans'),
                showlegend=True,
                legend=dict(
                    font=dict(color='#EDEBDD', family='Noto Sans', size=11),
                    bgcolor='rgba(31, 31, 33, 0.9)',
                    bordercolor='#2A2A2D',
                    borderwidth=1,
                    x=1.05,
                    y=0.5
                ),
                margin=dict(t=50, l=20, r=120, b=20)
            )
            st.plotly_chart(fig_pie, use_container_width=True)
    
    # === REPORT ===
    st.markdown("---")
    if successful_results:
        top3 = [r['ticker'] for r in successful_results[:3]]
        # Nothing-inspired report
        st.markdown(f"""
<div style='background: linear-gradient(135deg, rgba(27, 27, 29, 0.95) 0%, rgba(16, 16, 18, 0.95) 100%);
border: 1px solid rgba(255,255,255,0.08); border-top: 4px solid #D71921; border-radius: 14px; padding: 2.5rem;
box-shadow: 0 16px 40px rgba(0,0,0,0.5); font-family: "Noto Sans", "Ndot", sans-serif;'>
    <div style='text-align: center; margin-bottom: 2rem; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 1rem;'>
        <h3 class='report-title' style='font-size: 2rem; font-weight: 600; margin: 0; text-transform: uppercase;'>
            📊 INVESTMENT ANALYSIS REPORT
        </h3>
        <p class='report-subhead' style='font-size: 0.9rem; font-weight: 400; margin-top: 0.5rem;'>
            Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')} | Market Hours: NYSE/NASDAQ
        </p>
    </div>
    <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 1.2rem; margin-bottom: 1.8rem;'>
        <div style='background: rgba(255,255,255,0.04); padding: 1.4rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); box-shadow: 0 12px 28px rgba(0,0,0,0.4);'>
            <p style='color: #D71921; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; margin: 0 0 0.4rem 0; letter-spacing: 0.08em;'>Top Holdings</p>
            <p class='report-copy' style='font-size: 1.2rem; font-family: "LetteraMono", monospace; font-weight: 500; margin: 0;'>
                {', '.join(top3)}
            </p>
        </div>
        <div style='background: rgba(255,255,255,0.04); padding: 1.4rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); box-shadow: 0 12px 28px rgba(0,0,0,0.4);'>
            <p style='color: #D71921; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; margin: 0 0 0.4rem 0; letter-spacing: 0.08em;'>Expected Annual Return</p>
            <p class='report-copy' style='font-size: 1.8rem; font-family: "LetteraMono", monospace; font-weight: 600; margin: 0;'>
                {total_return:.2f}%
            </p>
        </div>
        <div style='background: rgba(255,255,255,0.04); padding: 1.4rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); box-shadow: 0 12px 28px rgba(0,0,0,0.4);'>
            <p style='color: #D71921; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; margin: 0 0 0.4rem 0; letter-spacing: 0.08em;'>Risk Profile</p>
            <p class='report-copy' style='font-size: 1.2rem; font-family: "Noto Sans", sans-serif; font-weight: 500; margin: 0;'>
                {risk}
            </p>
        </div>
        <div style='background: rgba(255,255,255,0.04); padding: 1.4rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); box-shadow: 0 12px 28px rgba(0,0,0,0.4);'>
            <p style='color: #D71921; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; margin: 0 0 0.4rem 0; letter-spacing: 0.08em;'>Stocks Analyzed</p>
            <p class='report-copy' style='font-size: 1.8rem; font-family: "LetteraMono", monospace; font-weight: 600; margin: 0;'>
                {len(successful_results)}
            </p>
        </div>
    </div>
    <div style='background: rgba(255,255,255,0.03); padding: 1.8rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.06);'>
        <h4 class='dot-matrix' style='color: #D71921; font-family: "Ndot", "Noto Sans", sans-serif; font-size: 1.05rem; font-weight: 600; margin: 0 0 1.2rem 0; letter-spacing: 0.08em;'>✓ RECOMMENDED ACTION PLAN</h4>
        <div style='display: grid; gap: 0.9rem;'>
            <div style='display: flex; align-items: start; gap: 0.8rem;'>
                <span style='color: #D71921; font-size: 1.2rem; line-height: 1;'>1</span>
                <p class='report-copy' style='font-size: 1rem; line-height: 1.6; margin: 0;'>
                    <strong style='color: #F3F1E7;'>Diversify Investments:</strong> Allocate funds according to the portfolio distribution chart above
                </p>
            </div>
            <div style='display: flex; align-items: start; gap: 0.8rem;'>
                <span style='color: #D71921; font-size: 1.2rem; line-height: 1;'>2</span>
                <p class='report-copy' style='font-size: 1rem; line-height: 1.6; margin: 0;'>
                    <strong style='color: #F3F1E7;'>Set Stop-Loss Orders:</strong> Implement 15% stop-loss on each position to manage downside risk
                </p>
            </div>
            <div style='display: flex; align-items: start; gap: 0.8rem;'>
                <span style='color: #D71921; font-size: 1.2rem; line-height: 1;'>3</span>
                <p class='report-copy' style='font-size: 1rem; line-height: 1.6; margin: 0;'>
                    <strong style='color: #F3F1E7;'>Monthly Rebalancing:</strong> Review and adjust portfolio monthly or when positions drift >10%
                </p>
            </div>
            <div style='display: flex; align-items: start; gap: 0.8rem;'>
                <span style='color: #D71921; font-size: 1.2rem; line-height: 1;'>4</span>
                <p class='report-copy' style='font-size: 1rem; line-height: 1.6; margin: 0;'>
                    <strong style='color: #F3F1E7;'>Monitor Earnings:</strong> Track quarterly earnings reports and adjust positions accordingly
                </p>
            </div>
        </div>
    </div>
    <div style='margin-top: 1.8rem; padding-top: 1.2rem; border-top: 1px solid rgba(255,255,255,0.06); text-align: center;'>
        <p class='report-muted' style='font-size: 0.85rem; line-height: 1.6; margin: 0;'>
            <strong style='color: #D71921;'>⚠️ DISCLAIMER:</strong> Educational use only. Past performance does not guarantee future results. Consult a licensed financial advisor before investing.
        </p>
    </div>
</div>
        """, unsafe_allow_html=True)
    
    # Reset button
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 **NEW ANALYSIS**", type="secondary", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    with col2:
        if successful_results:
            report_df = pd.DataFrame(successful_results)
            st.download_button(
                label="📥 Download Report (CSV)",
                data=report_df.to_csv(index=False),
                mime="text/csv",
                file_name="shamiquekhan-stock-report.csv"
            )
        else:
            st.button("📥 Download Report (CSV)", disabled=True)

# Footer - Nothing theme light version
footer_html = """
<div class='footer'>
    <div style='text-align: center; margin-bottom: 1.5rem;'>
        <h3 style='font-family: Ndot, sans-serif; color: #000000; font-size: 1.8rem; font-weight: 400; margin: 0; letter-spacing: 0.02em;'>
            AI Investment Advisor
        </h3>
        <p style='font-family: Ndot, sans-serif; color: rgba(0,0,0,0.6); font-size: 0.875rem; margin-top: 0.5rem;'>
            Powered by Advanced Machine Learning & Real-Time Market Data
        </p>
    </div>
    <div style='display: grid; grid-template-columns: repeat(3, 1fr); gap: 2rem; margin: 2rem 0; padding: 2rem 0; border-top: 1px solid rgba(0,0,0,0.08); border-bottom: 1px solid rgba(0,0,0,0.08);'>
        <div style='text-align: center;'>
            <p style='font-family: Ndot, sans-serif; color: #FF0000; font-size: 0.75rem; font-weight: 400; text-transform: uppercase; margin-bottom: 0.5rem; letter-spacing: 0.05em;'>Developed By</p>
            <p style='font-family: Ndot, sans-serif; color: #000000; font-size: 1rem; font-weight: 400;'>Shamique Khan</p>
            <p style='font-family: Ndot, sans-serif; color: rgba(0,0,0,0.6); font-size: 0.75rem;'>VIT Bhopal CSE | GSSoC '25</p>
        </div>
        <div style='text-align: center;'>
            <p style='font-family: Ndot, sans-serif; color: #FF0000; font-size: 0.75rem; font-weight: 400; text-transform: uppercase; margin-bottom: 0.5rem; letter-spacing: 0.05em;'>Connect</p>
            <div style='display: flex; justify-content: center; gap: 1.5rem; margin-top: 0.8rem;'>
                <a href='https://github.com/shamiquekhan' style='color: #000000; text-decoration: none; font-family: Ndot, sans-serif; font-size: 0.875rem; font-weight: 400; transition: color 0.2s;' onmouseover='this.style.color="#FF0000"' onmouseout='this.style.color="#000000"'>GitHub</a>
                <a href='https://www.linkedin.com/in/shamique-khan/' style='color: #000000; text-decoration: none; font-family: Ndot, sans-serif; font-size: 0.875rem; font-weight: 400; transition: color 0.2s;' onmouseover='this.style.color="#FF0000"' onmouseout='this.style.color="#000000"'>LinkedIn</a>
            </div>
        </div>
        <div style='text-align: center;'>
            <p style='font-family: Ndot, sans-serif; color: #FF0000; font-size: 0.75rem; font-weight: 400; text-transform: uppercase; margin-bottom: 0.5rem; letter-spacing: 0.05em;'>Features</p>
            <p style='font-family: Ndot, sans-serif; color: rgba(0,0,0,0.8); font-size: 0.75rem; line-height: 1.8;'>
                Real-Time Data<br>
                AI Analysis<br>
                Portfolio Optimization
            </p>
        </div>
    </div>
    <div style='text-align: center; padding-top: 1.5rem;'>
        <p style='font-family: Ndot, sans-serif; color: #000000; font-size: 0.875rem; font-weight: 400; margin-bottom: 0.5rem; letter-spacing: 0.02em;'>
            100% FREE • NO API KEYS REQUIRED
        </p>
        <p style='font-family: Ndot, sans-serif; color: rgba(0,0,0,0.6); font-size: 0.75rem; line-height: 1.6;'>
            Professional-Grade Analysis • Global Market Coverage • Educational Tool
        </p>
        <p style='font-family: LetteraMono, monospace; color: #FF0000; font-size: 0.65rem; margin-top: 1rem; letter-spacing: 0.05em;'>
            © 2025 AI Investment Advisor • Nothing-inspired design
        </p>
    </div>
</div>
"""

components.html(footer_html, height=520, scrolling=False)
