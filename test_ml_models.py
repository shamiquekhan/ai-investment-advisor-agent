"""
Test ML Models Integration
Run with: python test_ml_models.py
"""

import sys

def test_imports():
    """Test if required libraries are installed."""
    print("\n" + "="*60)
    print("TEST 1: Library Imports")
    print("="*60)
    
    try:
        import transformers
        print(f"✅ transformers: {transformers.__version__}")
    except ImportError:
        print("❌ transformers not installed")
        print("   Install with: pip install transformers")
        return False
    
    try:
        import torch
        print(f"✅ torch: {torch.__version__}")
    except ImportError:
        print("❌ torch not installed")
        print("   Install with: pip install torch")
        return False
    
    try:
        import sentencepiece
        print(f"✅ sentencepiece installed")
    except ImportError:
        print("⚠️  sentencepiece not installed (optional)")
    
    return True

def test_ml_models():
    """Test ML model loading and inference."""
    print("\n" + "="*60)
    print("TEST 2: ML Model Loading")
    print("="*60)
    
    try:
        from ml_models import (
            get_sentiment_model,
            analyze_financial_sentiment,
            check_ml_availability
        )
        
        # Check availability
        status = check_ml_availability()
        print(f"\n📊 Model Availability:")
        for model, available in status.items():
            symbol = "✅" if available else "❌"
            print(f"  {symbol} {model}")
        
        if not status.get('transformers_installed'):
            print("\n❌ transformers not available")
            return False
        
        # Test sentiment analysis
        print("\n📊 Testing FinBERT Sentiment Analysis...")
        test_texts = [
            "Apple beats earnings expectations with record Q4 revenue",
            "Tesla stock plunges on disappointing delivery numbers",
            "Microsoft announces quarterly dividend, stock holds steady"
        ]
        
        for text in test_texts:
            result = analyze_financial_sentiment(text)
            print(f"\n  Text: {text[:60]}...")
            print(f"  Sentiment: {result['label'].upper()} ({result['score']:.1%} confidence)")
            print(f"  Model: {result.get('model', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error loading ML models: {e}")
        return False

def test_news_integration():
    """Test integration with news sentiment."""
    print("\n" + "="*60)
    print("TEST 3: News Sentiment Integration")
    print("="*60)
    
    try:
        from news_sentiment import fetch_stock_news, calculate_overall_sentiment
        
        print("\n📰 Fetching news for AAPL (with ML sentiment)...")
        articles = fetch_stock_news("AAPL", max_articles=3, use_ml=True)
        
        if not articles:
            print("⚠️  No articles fetched (RSS feed may be down)")
            return True  # Not a failure, just no data
        
        print(f"\n✅ Fetched {len(articles)} articles")
        
        for i, article in enumerate(articles, 1):
            print(f"\n  Article {i}:")
            print(f"    Title: {article['title'][:60]}...")
            print(f"    Sentiment: {article['sentiment_label']}")
            print(f"    Score: {article['sentiment_score']:.2f}")
            print(f"    Method: {article.get('sentiment_method', 'unknown')}")
        
        # Test overall sentiment
        overall = calculate_overall_sentiment(articles, use_ml=True)
        print(f"\n📊 Overall Sentiment:")
        print(f"    Label: {overall['label']}")
        print(f"    Score: {overall['score']:.2f}")
        print(f"    Method: {overall.get('method', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing news integration: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "="*60)
    print("🤖 ML MODELS TEST SUITE")
    print("="*60)
    
    # Run all tests
    results = []
    
    # Test 1: Imports
    results.append(("Library Imports", test_imports()))
    
    if not results[0][1]:
        print("\n❌ Cannot proceed without required libraries")
        print("\nInstall with:")
        print("  pip install transformers torch sentencepiece")
        return 1
    
    # Test 2: Model loading
    results.append(("ML Model Loading", test_ml_models()))
    
    # Test 3: News integration
    results.append(("News Integration", test_news_integration()))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    passed = sum(1 for _, p in results if p)
    total = len(results)
    print(f"\n🎯 Score: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! ML models are ready to use.")
        print("\nNext steps:")
        print("  1. Run: streamlit run streamlit_app.py")
        print("  2. Enable '🤖 Use ML-Powered Sentiment' checkbox")
        print("  3. Analyze stocks with FinBERT-powered insights")
        return 0
    else:
        print("\n⚠️ Some tests failed. Check errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
