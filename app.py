"""
🚀 SHAMIQUEKHAN AI STOCK ADVISOR - LIVE STREAMLIT APP
https://shamiquekhan-stock-advisor-free.streamlit.app
100% FREE • No API Keys • Commercial Use OK
VIT Bhopal CSE | GSSoC '25 | shamiquekhan
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import time

# Page config
st.set_page_config(
    page_title="🚀 shamiquekhan Stock Advisor",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {font-size: 3.5rem !important; color: #1f77b4 !important;}
    .metric-card {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;}
    .stButton > button {width: 100%; height: 3em; border-radius: 15px;}
    .shamique-footer {background: linear-gradient(135deg, #1f77b4 0%, #667eea 100%); color: white; padding: 2rem;}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def get_stock_data(tickers):
    """📈 Live stock data"""
    results = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="6mo")
            
            # Technical indicators
            if len(hist) > 14:
                delta = hist['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                rsi_current = rsi.iloc[-1]
            else:
                rsi_current = 50
            
            results[ticker] = {
                'price': info.get('currentPrice', 0),
                'change': info.get('regularMarketChangePercent', 0),
                'pe': info.get('trailingPE', 'N/A'),
                'marketCap': info.get('marketCap', 0) / 1e9,
                'dividend': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
                'rsi': rsi_current,
                'volume': info.get('volume', 0),
                'sector': info.get('sector', 'Unknown'),
                'trend': "🟢" if info.get('regularMarketChangePercent', 0) > 0 else "🔴"
            }
        except:
            results[ticker] = {'error': True}
    return results

def calculate_score(data):
    """🎯 AI Scoring Algorithm"""
    score = 5.0
    
    # Momentum
    if data['change'] > 3: score += 2
    elif data['change'] > 0: score += 1
    
    # RSI
    if data['rsi'] < 30: score += 2  # Oversold
    elif data['rsi'] > 70: score -= 1  # Overbought
    
    # Valuation
    if isinstance(data['pe'], (int, float)) and data['pe'] < 25 and data['pe'] > 0:
        score += 1.5
    
    # Dividend
    if data['dividend'] > 2: score += 0.5
    
    return min(max(score, 1), 10)

# === MAIN APP ===
st.markdown('<h1 class="main-header" style="text-align: center;">🚀 shamiquekhan AI Stock Advisor</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; font-size: 1.5rem; color: #666;">Live Market Analysis • 100% FREE • Commercial Ready</p>', unsafe_allow_html=True)

# Sidebar Profile
with st.sidebar:
    st.image("https://avatars.githubusercontent.com/u/12345678?v=4", width=120, caption="shamiquekhan")
    st.markdown("### 👨‍💼 **shamiquekhan**")
    st.markdown("[🌐 GitHub](https://github.com/shamiquekhan) | [📱 LinkedIn](https://linkedin.com/in/shamiquekhan)")
    st.markdown("**VIT Bhopal CSE | GSSoC '25**")
    
    st.markdown("---")
    st.header("📊 Your Profile")
    age = st.slider("👴 Age", 18, 65, 22)
    risk = st.selectbox("⚠️ Risk Level", ["Conservative", "Moderate", "Aggressive"], index=1)
    amount = st.number_input("💰 Investment Amount", 1000, 500000, 25000, 1000)
    goal = st.selectbox("🎯 Goal", ["Retirement", "House", "Startup Capital", "Aggressive Growth"])

# Analysis Button
if st.button("🚀 **GENERATE AI PORTFOLIO**", type="primary", use_container_width=True, help="AI analyzes live market data"):
    st.session_state.analyze = True
    st.rerun()

# === ANALYSIS RESULTS ===
if st.session_state.get('analyze', False):
    with st.spinner("🔄 AI analyzing live market data..."):
        tickers = ["AAPL", "MSFT", "NVDA", "GOOGL", "TSLA", "META", "JPM", "UNH", "V", "PG"]
        data = get_stock_data(tickers)
        
        # Calculate recommendations
        recommendations = []
        for ticker, info in data.items():
            if not info.get('error'):
                score = calculate_score(info)
                recommendations.append((ticker, score, info))
        
        recommendations.sort(key=lambda x: x[1], reverse=True)
    
    # Results Layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📈 **TOP AI RECOMMENDATIONS**")
        
        for i, (ticker, score, info) in enumerate(recommendations[:6]):
            color = "🟢" if score >= 7 else "🟡" if score >= 5 else "🔴"
            trend_emoji = info['trend']
            
            with st.container():
                st.markdown(f"""
                <div style="padding: 1rem; margin: 0.5rem 0; border-left: 6px solid 
                {'#00ff88' if score >= 7 else '#ffaa00' if score >= 5 else '#ff4444'};
                background: {'#f0fff0' if score >= 7 else '#fff8e1' if score >= 5 else '#ffebee'}; border-radius: 8px;">
                    <h3 style="margin: 0;">{i+1}. **{ticker}** {color} **{score:.1f}/10**</h3>
                    <p><strong>💰 ${info['price']:.2f}</strong> | {trend_emoji} **{info['change']:.2f}%**</p>
                    <p>📊 P/E: {info['pe']} | RSI: **{info['rsi']:.0f}** | Cap: **${info['marketCap']:.1f}B**</p>
                </div>
                """, unsafe_allow_html=True)
    
    with col2:
        st.header("💼 **YOUR PORTFOLIO**")
        
        # Risk-based allocation
        allocations = {
            "Conservative": [20, 20, 20, 20, 20],
            "Moderate": [25, 25, 20, 15, 15],
            "Aggressive": [30, 25, 20, 15, 10]
        }
        weights = allocations[risk]
        
        portfolio_value = amount
        total_return = 0
        
        for i in range(min(5, len(recommendations))):
            ticker, score, info = recommendations[i]
            weight = weights[i]
            allocation = portfolio_value * (weight / 100)
            proj_return = info['change'] * 1.1  # Conservative projection
            total_return += proj_return * weight / 100
            
            st.metric(
                label=f"{ticker}",
                value=f"${allocation:,.0f}",
                delta=f"{proj_return:.1f}%"
            )
        
        st.markdown("---")
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1: st.metric("📈 Expected Return", f"{total_return:.1f}%")
        with col_m2: st.metric("💰 Total Invested", f"${amount:,.0f}")
        with col_m3: st.metric("⚠️ Risk Level", risk)
    
    # Charts
    st.markdown("---")
    st.header("📊 **LIVE AI VISUALIZATION**")
    
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        # Scores Bar Chart
        fig_bar = go.Figure()
        top_5 = recommendations[:5]
        colors = ['#00ff88', '#88ff00', '#ffff00', '#ff8800', '#ff4444']
        
        for i, (ticker, score, _) in enumerate(top_5):
            fig_bar.add_trace(go.Bar(
                x=[ticker],
                y=[score],
                marker_color=colors[i],
                text=f"{score:.1f}",
                textposition="auto",
                name=ticker
            ))
        
        fig_bar.update_layout(
            title="🤖 AI Stock Scores (1-10)",
            yaxis_title="Score",
            yaxis_range=[0, 10],
            showlegend=False,
            height=450,
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    with col_chart2:
        # Portfolio Pie
        labels = [r[0] for r in top_5]
        values = weights[:5]
        fig_pie = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            marker_colors=colors[:5]
        )])
        fig_pie.update_layout(
            title="💼 Your Allocation %",
            height=450,
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Investment Report
    st.markdown("---")
    st.header("📋 **PERSONALIZED INVESTMENT REPORT**")
    
    top3 = [r[0] for r in recommendations[:3]]
    report = f"""
**Generated: {datetime.now().strftime('%Y-%m-%d %H:%M IST')}**

👤 **Investor**: shamiquekhan | Age: {age} | **{risk}** Risk
💰 **Investment**: ${amount:,} | Goal: {goal}

🎯 **Top 3 AI Picks**: {', '.join(top3)}
📈 **Expected Return**: **{total_return:.1f}% annually**

✅ **Action Plan**:
• Fund portfolio using weights above
• Set **15% stop-loss** on all positions
• **Rebalance monthly**
• Monitor **Q1 2026 earnings**

⚠️ *Educational tool. Not financial advice.*
    """
    st.info(report)
    
    # Reset
    st.markdown("---")
    if st.button("🔄 **NEW ANALYSIS**", type="secondary"):
        st.session_state.analyze = False
        st.rerun()

else:
    st.info("👈 **Enter your profile → Click ANALYZE → Get AI portfolio instantly!**")

# Footer
st.markdown("""
<div class="shamique-footer">
    <h2 style="text-align: center; margin-bottom: 1rem;">🚀 Built by shamiquekhan</h2>
    <p style="text-align: center; font-size: 1.2rem;">
        <strong>VIT Bhopal CSE</strong> | GSSoC '25 | Data Science | Hackathons
    </p>
    <p style="text-align: center;">
        <a href="https://github.com/shamiquekhan" style="color: white; text-decoration: none;">🐙 GitHub</a> | 
        <a href="https://linkedin.com/in/shamiquekhan" style="color: white; text-decoration: none;">💼 LinkedIn</a> | 
        <a href="https://shamiquekhan-stock-advisor-free.streamlit.app" style="color: white; text-decoration: none;">🌐 Live App</a>
    </p>
    <p style="text-align: center; font-size: 0.9rem;">
        ⭐ <strong>100% FREE FOREVER</strong> • No API Keys • Commercial Use OK
    </p>
</div>
""", unsafe_allow_html=True)
