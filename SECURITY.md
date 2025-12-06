# 🔒 API Key Security Guide

## ⚠️ URGENT: Rotate Your Keys

If you previously hardcoded API keys in your code, **rotate them immediately**:

### 1. Finnhub
1. Login: https://finnhub.io/dashboard
2. Go to "API Keys" → "Regenerate Key"
3. Copy new key to `.env` file

### 2. Alpha Vantage
1. Get new key: https://www.alphavantage.co/support/#api-key
2. Enter your email to receive new key
3. Add to `.env` file

### 3. Twelve Data
1. Login: https://twelvedata.com/account/api
2. Click "Reset API Key"
3. Copy new key to `.env` file

### 4. MarketStack
1. Login: https://marketstack.com/dashboard
2. Go to "Your API Access Key" → "Regenerate"
3. Copy new key to `.env` file

---

## ✅ Secure Setup (First Time)

### Step 1: Create `.env` File

```bash
cd "AI Investment Advisor Agent"
cp .env.example .env
```

### Step 2: Add Your Keys to `.env`

Edit `.env` with your real API keys:

```bash
# NEVER commit this file to git!
FINNHUB_API_KEY=your_new_finnhub_key
ALPHA_VANTAGE_API_KEY=your_new_alpha_key
TWELVE_DATA_API_KEY=your_new_twelve_key
MARKETSTACK_API_KEY=your_new_marketstack_key
```

### Step 3: Load in Python (Already Configured)

The app automatically loads from environment:

```python
import os
FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY')  # ✅ Secure
# NOT: FINNHUB_API_KEY = 'd4q2lv9r...'  # ❌ Insecure!
```

### Step 4: Verify `.gitignore`

Ensure `.env` is in `.gitignore` (already done):

```gitignore
# Environment Variables - NEVER COMMIT THESE!
.env
.env.local
.env.*.local
```

---

## 🚀 Usage

### Local Development

```bash
# Set env vars in terminal
export FINNHUB_API_KEY="your_key"
export ALPHA_VANTAGE_API_KEY="your_key"

# Or use .env file (recommended)
# The app will auto-load from .env if present
streamlit run streamlit_app.py
```

### Streamlit Cloud Deployment

1. Go to: https://share.streamlit.io/
2. Deploy your app
3. Click "Settings" → "Secrets"
4. Add your keys:

```toml
FINNHUB_API_KEY = "your_key"
ALPHA_VANTAGE_API_KEY = "your_key"
TWELVE_DATA_API_KEY = "your_key"
MARKETSTACK_API_KEY = "your_key"
```

5. Secrets are encrypted and never exposed in logs

### Docker/Production

Use environment variables:

```bash
docker run -e FINNHUB_API_KEY="your_key" \
           -e ALPHA_VANTAGE_API_KEY="your_key" \
           your-app
```

---

## 🛡️ Best Practices

### ✅ DO

- **Use environment variables** (`.env`, Streamlit secrets, Docker env)
- **Rotate keys** if they were ever committed to git
- **Use `.env.example`** as template (without real keys)
- **Add `.env` to `.gitignore`**
- **Monitor API usage** in dashboards

### ❌ DON'T

- **Never hardcode keys** in Python files
- **Never commit `.env`** to version control
- **Never share keys** publicly (Slack, Discord, etc.)
- **Never log keys** in console output
- **Never reuse keys** across projects

---

## 🔍 Check for Exposed Keys

### 1. Check Git History

```bash
# Search for any leaked keys in history
git log -p | grep -i "api.*key"
git log -p | grep -E "[A-Z0-9]{32}"
```

### 2. If Keys Were Committed

**Option A: Rotate keys immediately** (fastest)
1. Generate new keys from each provider
2. Update `.env` file
3. Old keys are now useless

**Option B: Remove from git history** (optional, after rotation)
```bash
# Use BFG Repo-Cleaner or git-filter-branch
# See: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository
```

### 3. Enable Secret Scanning (GitHub)

If using GitHub:
1. Go to Settings → Code security and analysis
2. Enable "Secret scanning"
3. GitHub will alert you if keys are pushed

---

## 📊 Rate Limit Protection

The app already implements:

```python
# ✅ Built-in protection
FINNHUB_DELAY = 1.0      # 1 second between calls
ALPHAVANTAGE_DELAY = 13.0 # Conservative for 25/day limit
TWELVEDATA_DELAY = 0.11   # Safe for 800/day
MARKETSTACK_DELAY = 0.1   # Safe for 1000/month

# ✅ Caching
FINNHUB_CACHE_TTL = 300   # 5 minutes
ALPHA_VANTAGE_CACHE_TTL = 3600  # 1 hour
```

This prevents:
- ❌ Exceeding free tier limits
- ❌ Getting rate-limited (429 errors)
- ❌ Wasting API quota

---

## 🧪 Testing Without Keys

The app gracefully handles missing keys:

```python
# If no keys configured:
if not FINNHUB_API_KEY:
    # Falls back to Yahoo Finance (no key needed)
    data = get_yfinance_data(ticker)
```

You can test the full app without any API keys!

---

## 📝 Summary Checklist

- [ ] Copy `.env.example` to `.env`
- [ ] Get free API keys from providers
- [ ] Add keys to `.env` file (never to code)
- [ ] Verify `.env` is in `.gitignore`
- [ ] Rotate any previously exposed keys
- [ ] Test app loads keys correctly
- [ ] Never commit `.env` to git

---

## 🆘 Emergency: Keys Were Leaked

1. **Immediately rotate all keys** (takes 5 minutes)
2. Check provider dashboards for unauthorized usage
3. Enable rate limiting/IP restrictions if available
4. Consider using secret management (AWS Secrets Manager, HashiCorp Vault)

---

## 📚 Resources

- [OWASP Secret Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [GitHub: Removing Sensitive Data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [Streamlit Secrets Management](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)

---

**Status:** 🔒 Secured (keys loaded from environment only)  
**Risk Level:** ✅ Low (no hardcoded keys)  
**Action Required:** Rotate any previously exposed keys
