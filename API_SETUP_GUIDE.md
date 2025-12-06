# 🚀 Multi-Provider API Setup Guide

## ⚠️ Security First

**IMPORTANT:** Never hardcode API keys in your code! See [SECURITY.md](SECURITY.md) for:
- ✅ How to use environment variables securely
- ✅ Key rotation instructions
- ✅ `.env` file setup

---

## Overview

The AI Investment Advisor uses **4 FREE data providers** to eliminate rate limits and deliver fast, reliable stock data:

1. **Yahoo Finance** (Always active, no setup needed)
2. **Finnhub** (Optional, real-time quotes)
3. **MarketStack** (Optional, global markets - 170k+ tickers)
4. **Alpha Vantage** (Optional, backup fundamentals)

## 🎯 Why Multi-Provider?

**Problem**: Single-provider systems hit rate limits (429 errors) when analyzing multiple stocks.

**Solution**: Distribute requests across 4 free APIs:
- Yahoo Finance: Historical data (1hr cache)
- Finnhub: Real-time quotes (5min cache)
- MarketStack: Global markets, EOD data (15min cache)
- Alpha Vantage: Backup data (1hr cache)

**Result**: Zero 429 errors, faster responses, 100% free!

---

## 🔑 Getting Your FREE API Keys

### Option 1: Run Without Extra APIs (Default)
**No setup needed!** The app works perfectly with just Yahoo Finance:
- ✅ Historical prices and fundamentals
- ✅ All analysis features work
- ⚠️ Slower during high usage (1.5s delay between stocks)

### Option 2: Add Finnhub (Recommended)
**Benefits**: Real-time quotes, faster updates, reduced Yahoo load

**Steps**:
1. Visit https://finnhub.io/register
2. Sign up for FREE (no credit card required)
3. Copy your API key from the dashboard
4. **60 calls/minute** on free tier

**Add to your environment**:
```bash
# Secure method: Use .env file (recommended)
# 1. Copy template:
cp .env.example .env

# 2. Edit .env and add your key:
FINNHUB_API_KEY="your_key_here"

# 3. .env is gitignored (safe)

# Alternative: Export in terminal (temporary)
export FINNHUB_API_KEY="your_key_here"

# For Streamlit Cloud: Use Secrets in dashboard
# See SECURITY.md for details
```

**🔒 Security Note:** Never commit API keys to git. Use `.env` file or environment variables.

### Option 3: Add MarketStack (Global Markets)
**Benefits**: 170,000+ tickers, 70+ exchanges, international stocks

**Steps**:
1. Visit https://marketstack.com/signup/free
2. Sign up for FREE (no credit card required)
3. Copy your API key from dashboard
4. **1000 calls/month** (~33/day) on free tier

**Verify your key**:
```bash
python verify_marketstack.py YOUR_API_KEY_HERE
```

**Add to your environment**:
```bash
# Option A: Environment variable
export MARKETSTACK_API_KEY="your_key_here"

# Option B: Streamlit secrets
echo 'MARKETSTACK_API_KEY = "your_key_here"' >> .streamlit/secrets.toml
```

**Supported Markets**: NYSE, NASDAQ, LSE, TSX, BSE, TSE, XETRA, and 65+ more!

### Option 4: Add Alpha Vantage (Extra Backup)
**Benefits**: Backup fundamentals, analyst ratings, more data sources

**Steps**:
1. Visit https://www.alphavantage.co/support/#api-key
2. Enter your email to get FREE key instantly
3. Copy the key from your email
4. **25 calls/day** on free tier (use sparingly!)

**Add to your environment**:
```bash
# Option A: Environment variable
export ALPHA_VANTAGE_API_KEY="your_key_here"

# Option B: Streamlit secrets
echo 'ALPHA_VANTAGE_API_KEY = "your_key_here"' >> .streamlit/secrets.toml
```

---

## 📁 Caching Strategy

### How It Works
1. **First Request**: Fetch from API → Save to `.cache/` folder
2. **Subsequent Requests**: Read from cache (instant!)
3. **Expiration**: Cache refreshes automatically based on TTL

### Cache Lifetimes
- Yahoo Finance: **1 hour** (fundamentals don't change often)
- Finnhub: **5 minutes** (real-time quotes)
- MarketStack: **15 minutes** (EOD data)
- Alpha Vantage: **1 hour** (backup data)

### Cache Location
All cached data is stored in `.cache/` directory:
```
.cache/
├── yfinance_AAPL_main.json
├── finnhub_AAPL_quote.json
├── alphavantage_AAPL_overview.json
└── ...
```

### Clear Cache
- **UI**: Click "🗑️ Clear Cache" button in the app
- **CLI**: Delete `.cache/` folder
```bash
rm -rf .cache/
```

---

## 🔧 Configuration Examples

### Streamlit Cloud Deployment
Create `.streamlit/secrets.toml`:
```toml
# Optional API keys (leave blank to use only Yahoo Finance)
FINNHUB_API_KEY = "your_finnhub_key"
ALPHA_VANTAGE_API_KEY = "your_alphavantage_key"
```

### Docker Deployment
Add to `docker-compose.yml`:
```yaml
environment:
  - FINNHUB_API_KEY=your_key_here
  - ALPHA_VANTAGE_API_KEY=your_key_here
```

### Local Development (.env file)
Create `.env` and load with `python-dotenv`:
```bash
FINNHUB_API_KEY=your_key_here
ALPHA_VANTAGE_API_KEY=your_key_here
```

---

## 📊 Provider Status

The app shows real-time provider status in the UI:

- ✅ **Green** = Active and configured
- ⚠️ **Yellow** = Not configured (optional)
- ❌ **Red** = Error or rate limited

Click "📊 Refresh Stats" to update cache statistics.

---

## 🚀 Performance Tips

### 1. Analyze Top 10 Stocks First
- Focus on your best picks
- Cached data makes subsequent analyses instant

### 2. Use Multi-Provider Mode
- Distributes load across APIs
- Eliminates 429 errors completely

### 3. Let Cache Work
- Don't clear cache unnecessarily  
- Hour-old fundamentals are still accurate

### 4. Batch Your Analyses
- Analyze 5-10 stocks at once
- Parallel fetching is much faster than sequential

---

## 🐛 Troubleshooting

### "429 Too Many Requests" Error
**Solution**: Enable multi-provider mode or wait 1-2 minutes.

### "API Key Invalid" Error
**Solution**: Check that your key is correct and active.

### Slow Performance
**Solution**: 
1. Enable multi-provider mode
2. Reduce number of stocks (max 10-15)
3. Check internet connection

### Cache Not Working
**Solution**:
1. Check `.cache/` folder exists
2. Clear cache and retry
3. Verify disk write permissions

---

## 📈 Free Tier Limits

| Provider | Free Tier Limit | Our Usage | Buffer |
|----------|----------------|-----------|--------|
| Yahoo Finance | ~2000/hr | 1 call/1.5s = 2400/hr | ⚠️ Tight |
| Finnhub | 60 calls/min | 1 call/sec = 60/min | ✅ Safe |
| Alpha Vantage | 25 calls/day | 1 call/13s = ~25/day | ✅ Safe |

**With caching**: Real usage is 90% lower! Cache hits = zero API calls.

---

## 🎓 Educational Use Disclaimer

This tool is for **educational purposes only**:
- Not financial advice
- Past performance ≠ future results
- Consult licensed advisor before investing
- Data may have delays or inaccuracies

---

## 💡 FAQ

**Q: Do I need all 3 API keys?**  
A: No! Yahoo Finance alone works perfectly. Extra APIs just make it faster and more reliable.

**Q: Are these really free forever?**  
A: Yes! All 3 providers have permanent free tiers. Just respect rate limits.

**Q: What happens if I exceed free limits?**  
A: The app falls back to cache or sample data. No crashes, no paid charges.

**Q: Can I use my own API keys?**  
A: Yes! This is YOUR deployment. Use your own keys, modify code freely.

**Q: Is my data private?**  
A: Yes! All data is cached locally on YOUR server. No third-party analytics.

---

## 📞 Support

- GitHub Issues: Report bugs or request features
- Documentation: See README.md for full details
- Community: Share your experience on social media

---

**Made with ❤️ by Shamique Khan**  
VIT Bhopal | CSE | GSSoC '25 Contributor
