"""
MarketStack API Key Verification Tool
Run this to test your MarketStack API key before using the full app.

Usage:
    python verify_marketstack.py YOUR_API_KEY_HERE
"""

import sys
import requests

def verify_marketstack_key(api_key: str) -> bool:
    """Test if MarketStack API key is valid."""
    
    print("\n" + "="*60)
    print("🔍 MARKETSTACK API KEY VERIFICATION")
    print("="*60)
    
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        print("\n❌ ERROR: No API key provided!")
        print("\nUsage:")
        print("  python verify_marketstack.py YOUR_API_KEY_HERE")
        print("\nGet a free key at: https://marketstack.com/signup/free")
        return False
    
    print(f"\n🔑 Testing API key: {api_key[:8]}...{api_key[-4:]}")
    
    # Test with a simple request
    url = "https://api.marketstack.com/v1/eod/latest"
    params = {
        'access_key': api_key,
        'symbols': 'AAPL',
        'limit': 1
    }
    
    print(f"\n📡 Sending test request to MarketStack...")
    print(f"   Endpoint: {url}")
    print(f"   Symbol: AAPL")
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        print(f"\n📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'error' in data:
                print(f"\n❌ API Error: {data['error'].get('message', 'Unknown error')}")
                print(f"   Error Code: {data['error'].get('code', 'N/A')}")
                return False
            
            if 'data' in data and len(data['data']) > 0:
                quote = data['data'][0]
                print("\n✅ SUCCESS! Your API key is valid!")
                print("\n📈 Test Data Retrieved:")
                print(f"   Symbol: {quote.get('symbol', 'N/A')}")
                print(f"   Close: ${quote.get('close', 0):.2f}")
                print(f"   Date: {quote.get('date', 'N/A')}")
                print(f"   Exchange: {quote.get('exchange', 'N/A')}")
                
                print("\n✅ Your API key is working correctly!")
                print("\n📝 Next Steps:")
                print("   1. Set environment variable:")
                print(f"      export MARKETSTACK_API_KEY=\"{api_key}\"")
                print("\n   2. Or update multi_provider.py line 35:")
                print(f"      MARKETSTACK_API_KEY = os.getenv('MARKETSTACK_API_KEY', '{api_key}')")
                print("\n   3. Run the app:")
                print("      streamlit run streamlit_app.py")
                
                return True
            else:
                print("\n⚠️  API responded but returned no data")
                print("   This might be a free tier limitation")
                return False
        
        elif response.status_code == 401:
            print("\n❌ AUTHENTICATION FAILED!")
            print("   Your API key is invalid or expired")
            print("\n🔧 Troubleshooting:")
            print("   1. Get a new key at: https://marketstack.com/signup/free")
            print("   2. Check you copied the entire key (no spaces)")
            print("   3. Verify key is active in dashboard")
            return False
        
        elif response.status_code == 429:
            print("\n⚠️  RATE LIMIT EXCEEDED!")
            print("   You've used your monthly quota (1000 calls)")
            print("\n💡 Solutions:")
            print("   1. Wait until next month for quota reset")
            print("   2. Upgrade plan at: https://marketstack.com/product")
            print("   3. Use other providers (Yahoo, Finnhub)")
            return False
        
        else:
            print(f"\n❌ HTTP Error: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("\n⏱️  REQUEST TIMEOUT!")
        print("   API took too long to respond")
        print("   Try again in a moment")
        return False
    
    except requests.exceptions.RequestException as e:
        print(f"\n❌ REQUEST FAILED: {e}")
        print("   Check your internet connection")
        return False
    
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("\n❌ ERROR: Missing API key argument!")
        print("\nUsage:")
        print("  python verify_marketstack.py YOUR_API_KEY_HERE")
        print("\nGet a free key at: https://marketstack.com/signup/free")
        return 1
    
    api_key = sys.argv[1].strip()
    
    success = verify_marketstack_key(api_key)
    
    if success:
        print("\n🎉 All systems go! You're ready to use MarketStack.")
        return 0
    else:
        print("\n❌ Verification failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
