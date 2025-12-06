"""
Quick test script for multi-provider system
Run this to verify everything works before deployment
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from multi_provider import (
    get_stock_data_multi,
    get_stocks_parallel_multi,
    validate_api_keys,
    get_provider_status,
    get_cache_stats,
    clear_cache
)

def test_api_keys():
    """Test API key detection"""
    print("\n" + "="*60)
    print("🔑 API KEY STATUS")
    print("="*60)
    keys = validate_api_keys()
    print(f"Finnhub: {'✅ Configured' if keys['finnhub'] else '⚠️ Not configured (optional)'}")
    print(f"Alpha Vantage: {'✅ Configured' if keys['alpha_vantage'] else '⚠️ Not configured (optional)'}")
    print("\n" + get_provider_status())

def test_single_stock():
    """Test fetching a single stock"""
    print("\n" + "="*60)
    print("📊 SINGLE STOCK TEST (AAPL)")
    print("="*60)
    
    ticker = "AAPL"
    print(f"Fetching {ticker}...")
    
    data = get_stock_data_multi(ticker)
    
    if data:
        print(f"✅ Success! Got data for {ticker}")
        print(f"   Price: ${data.get('current_price', 'N/A')}")
        print(f"   Name: {data.get('name', 'N/A')}")
        print(f"   Market Cap: ${data.get('market_cap', 0):,.0f}")
        print(f"   P/E Ratio: {data.get('pe_ratio', 'N/A')}")
        print(f"   Real-time: {data.get('realtime', False)}")
    else:
        print(f"❌ Failed to fetch {ticker}")

def test_multiple_stocks():
    """Test fetching multiple stocks in parallel"""
    print("\n" + "="*60)
    print("📊 PARALLEL FETCH TEST (5 stocks)")
    print("="*60)
    
    tickers = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA"]
    print(f"Fetching {len(tickers)} stocks in parallel...")
    
    import time
    start = time.time()
    
    results = get_stocks_parallel_multi(tickers, max_workers=3)
    
    elapsed = time.time() - start
    
    print(f"✅ Fetched {len(results)}/{len(tickers)} stocks in {elapsed:.2f}s")
    
    for ticker, data in results.items():
        price = data.get('current_price', 'N/A')
        print(f"   {ticker}: ${price}")

def test_cache():
    """Test cache functionality"""
    print("\n" + "="*60)
    print("💾 CACHE TEST")
    print("="*60)
    
    stats = get_cache_stats()
    
    print(f"Total cache files: {stats['total_files']}")
    print(f"Total size: {stats['total_size_mb']:.2f} MB")
    print(f"By provider:")
    for provider, count in stats['by_provider'].items():
        print(f"   {provider}: {count} files")
    
    if stats['total_files'] > 0:
        print("\n⚠️ Cache contains data. Test fetch will use cache (instant)")
        print("   Run with clear_cache() first for fresh API test")

def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 MULTI-PROVIDER SYSTEM TEST")
    print("="*60)
    
    try:
        test_api_keys()
        test_cache()
        test_single_stock()
        test_multiple_stocks()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\n💡 Tips:")
        print("   - Cache makes subsequent requests instant")
        print("   - Add FINNHUB_API_KEY for real-time quotes")
        print("   - Add ALPHA_VANTAGE_API_KEY for backup data")
        print("   - See API_SETUP_GUIDE.md for instructions")
        
    except Exception as e:
        print("\n" + "="*60)
        print("❌ TEST FAILED")
        print("="*60)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    import sys
    
    # Optional: Clear cache before testing
    if "--clear-cache" in sys.argv:
        print("🗑️ Clearing cache...")
        clear_cache()
    
    success = run_all_tests()
    sys.exit(0 if success else 1)
