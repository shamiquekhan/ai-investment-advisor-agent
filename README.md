# 🚀 shamiquekhan AI Stock Advisor

**LIVE: https://shamiquekhan-stock-advisor-free.streamlit.app**

[![Streamlit](https://img.shields.io/badge/Live-shamiquekhan-FF4B4B)](https://shamiquekhan-stock-advisor-free.streamlit.app)
[![GitHub](https://img.shields.io/badge/GitHub-shamiquekhan-181717)](https://github.com/shamiquekhan)
[![Stars](https://img.shields.io/github/stars/shamiquekhan/stock-advisor-free?style=social)](https://github.com/shamiquekhan/stock-advisor-free)

## ✨ **LIVE FEATURES**
```
📈 Real-time prices: AAPL, NVDA, TSLA, MSFT...
🤖 FREE AI scoring (RSI, P/E, momentum)
📰 News sentiment analysis (keyword-based)
🏥 Financial health scoring (0-100, A+ to F grades)
⚠️ Volatility risk metrics (1-10 scale)
💼 Risk-based portfolios
📊 Interactive charts
📱 Mobile responsive
🚀 Multi-provider API (Yahoo + Finnhub + Alpha Vantage)
💾 Smart caching (no 429 errors!)
```

## 🚀 **DEPLOYED LIVE**
```
✅ GitHub: github.com/shamiquekhan/stock-advisor-free
✅ Streamlit: shamiquekhan-stock-advisor-free.streamlit.app
✅ 100% FREE FOREVER hosting
✅ ZERO rate limit errors (multi-provider + caching)
```

## 🎯 **MULTI-PROVIDER ARCHITECTURE**

**No more 429 errors!** The app uses 3 FREE APIs to distribute load:

| Provider | Purpose | Cache | Free Tier |
|----------|---------|-------|-----------|
| **Yahoo Finance** | Historical data, fundamentals | 1 hour | Always active |
| **Finnhub** | Real-time quotes | 5 min | 60 calls/min (optional) |
| **Alpha Vantage** | Backup fundamentals | 1 hour | 25 calls/day (optional) |

**Setup**: See [API_SETUP_GUIDE.md](API_SETUP_GUIDE.md) for free API keys (optional).

## 🛠️ **QUICK START**
```bash
# Clone and install
git clone https://github.com/shamiquekhan/stock-advisor-free
cd stock-advisor-free
pip install -r requirements.txt

# Optional: Add API keys for multi-provider mode
export FINNHUB_API_KEY="your_key"  # Get at finnhub.io/register
export ALPHA_VANTAGE_API_KEY="your_key"  # Get at alphavantage.co

# Run
streamlit run streamlit_app.py
```

## 🎓 **shamiquekhan**
**VIT Bhopal CSE** | **GSSoC '25** | Data Science  
**Skills**: Python • Streamlit • yfinance • AI/ML

---
⭐ **Star this repo!** Hackathon ranking boost ✨
