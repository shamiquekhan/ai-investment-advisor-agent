#!/bin/bash
# Quick setup script for API key security

echo "🔒 API Key Security Setup"
echo "========================="
echo ""

# Check if .env exists
if [ -f .env ]; then
    echo "⚠️  .env file already exists"
    read -p "Overwrite? (y/N): " overwrite
    if [ "$overwrite" != "y" ]; then
        echo "Skipping .env creation"
    else
        cp .env.example .env
        echo "✅ Created .env from template"
    fi
else
    cp .env.example .env
    echo "✅ Created .env from template"
fi

echo ""
echo "📝 Next steps:"
echo "1. Edit .env and add your API keys"
echo "2. Get free keys from:"
echo "   - Finnhub: https://finnhub.io/register"
echo "   - Alpha Vantage: https://www.alphavantage.co/support/#api-key"
echo "   - Twelve Data: https://twelvedata.com/pricing"
echo "   - MarketStack: https://marketstack.com/signup/free"
echo ""
echo "3. Run the app:"
echo "   streamlit run streamlit_app.py"
echo ""
echo "🔒 Remember: Never commit .env to git!"
echo "   (Already in .gitignore)"
