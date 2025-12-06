"""News fetching and sentiment analysis using RSS feeds (no API keys needed)."""

import time
from datetime import datetime, timedelta
from typing import List, Dict

import feedparser
import streamlit as st

# Try importing ML models for enhanced sentiment
try:
    from ml_models import (
        analyze_financial_sentiment,
        calculate_ml_sentiment_score,
        HF_AVAILABLE
    )
    ML_ENABLED = True
except ImportError:
    ML_ENABLED = False


# Keyword-based sentiment scoring (simple but effective)
POSITIVE_KEYWORDS = {
    "beat", "beats", "surge", "surges", "soar", "soars", "jump", "jumps",
    "rally", "rallies", "gain", "gains", "profit", "profits", "growth",
    "upgrade", "upgrades", "bullish", "record", "high", "strong", "positive",
    "success", "win", "wins", "breakthrough", "innovation", "expand", "expansion"
}

NEGATIVE_KEYWORDS = {
    "miss", "misses", "fall", "falls", "drop", "drops", "decline", "declines",
    "loss", "losses", "lawsuit", "lawsuits", "downgrade", "downgrades", "bearish",
    "low", "weak", "negative", "fail", "fails", "concern", "concerns", "warning",
    "risk", "risks", "investigate", "investigation", "fraud", "scandal", "cut", "cuts"
}


def calculate_sentiment_score(text: str) -> float:
    """
    Calculate sentiment score from text using keyword matching.
    Returns: -1.0 (very negative) to +1.0 (very positive)
    """
    if not text:
        return 0.0
    
    text_lower = text.lower()
    
    positive_count = sum(1 for word in POSITIVE_KEYWORDS if word in text_lower)
    negative_count = sum(1 for word in NEGATIVE_KEYWORDS if word in text_lower)
    
    total_count = positive_count + negative_count
    
    if total_count == 0:
        return 0.0
    
    # Calculate net sentiment
    sentiment = (positive_count - negative_count) / total_count
    return round(sentiment, 2)


def get_sentiment_label(score: float) -> str:
    """Convert sentiment score to readable label."""
    if score >= 0.5:
        return "🟢 Very Positive"
    elif score >= 0.2:
        return "🟢 Positive"
    elif score > -0.2:
        return "🟡 Neutral"
    elif score > -0.5:
        return "🔴 Negative"
    else:
        return "🔴 Very Negative"


@st.cache_data(ttl=1800)  # Cache for 30 minutes
def fetch_stock_news(ticker: str, max_articles: int = 5, use_ml: bool = True) -> List[Dict]:
    """
    Fetch recent news for a stock from Yahoo Finance RSS feed.
    Returns list of articles with title, link, published date, and sentiment.
    
    Args:
        ticker: Stock symbol
        max_articles: Maximum number of articles to return
        use_ml: Use ML-powered sentiment (FinBERT) if available
    """
    # Clean ticker (remove exchange suffix for RSS)
    clean_ticker = ticker.split('.')[0]
    
    # Yahoo Finance RSS feed URL
    rss_url = f"https://finance.yahoo.com/rss/headline?s={clean_ticker}"
    
    try:
        feed = feedparser.parse(rss_url)
        
        articles = []
        cutoff_date = datetime.now() - timedelta(days=7)  # Last 7 days
        
        for entry in feed.entries[:max_articles * 2]:  # Fetch extra in case some are old
            try:
                # Parse date
                published = entry.get('published_parsed')
                if published:
                    pub_date = datetime(*published[:6])
                    if pub_date < cutoff_date:
                        continue
                else:
                    pub_date = datetime.now()
                
                # Extract text for sentiment
                title = entry.get('title', '')
                summary = entry.get('summary', '')
                text = f"{title} {summary}"
                
                # Calculate sentiment (ML-powered if available)
                if use_ml and ML_ENABLED:
                    ml_result = analyze_financial_sentiment(text)
                    sentiment_score = _convert_ml_to_score(ml_result)
                    sentiment_label = _ml_label_to_emoji(ml_result['label'])
                    sentiment_method = 'finbert'
                else:
                    sentiment_score = calculate_sentiment_score(text)
                    sentiment_label = get_sentiment_label(sentiment_score)
                    sentiment_method = 'keyword'
                
                articles.append({
                    'title': title,
                    'link': entry.get('link', ''),
                    'published': pub_date.strftime('%Y-%m-%d %H:%M'),
                    'sentiment_score': sentiment_score,
                    'sentiment_label': sentiment_label,
                    'sentiment_method': sentiment_method,
                    'summary': summary[:200] + '...' if len(summary) > 200 else summary,
                    'description': summary  # For ML batch processing
                })
                
                if len(articles) >= max_articles:
                    break
                    
            except Exception:
                continue
        
        return articles
        
    except Exception:
        # Fallback: return empty list if RSS fails
        return []


def calculate_overall_sentiment(articles: List[Dict], use_ml: bool = True) -> Dict:
    """
    Calculate overall sentiment from multiple articles.
    Returns dict with score, label, and article count.
    
    Args:
        articles: List of article dicts
        use_ml: Use ML-powered aggregation if available
    """
    if not articles:
        return {
            'score': 0.0,
            'label': '🟡 No Recent News',
            'article_count': 0,
            'method': 'none'
        }
    
    # Use ML-powered sentiment if available
    if use_ml and ML_ENABLED:
        ml_score, ml_label = calculate_ml_sentiment_score(articles)
        return {
            'score': round(ml_score, 2),
            'label': ml_label,
            'article_count': len(articles),
            'method': 'finbert'
        }
    
    # Fallback to keyword-based average
    avg_score = sum(a['sentiment_score'] for a in articles) / len(articles)
    
    return {
        'score': round(avg_score, 2),
        'label': get_sentiment_label(avg_score),
        'article_count': len(articles),
        'method': 'keyword'
    }

# ============================================================================
# ML CONVERSION HELPERS
# ============================================================================

def _convert_ml_to_score(ml_result: Dict) -> float:
    """
    Convert ML sentiment result to numeric score [-1, 1].
    
    Args:
        ml_result: {'label': 'positive'|'negative'|'neutral', 'score': 0.95}
    
    Returns:
        float between -1 and 1
    """
    label = ml_result.get('label', 'neutral').lower()
    confidence = ml_result.get('score', 0.5)
    
    if label == 'positive':
        return confidence  # 0 to 1
    elif label == 'negative':
        return -confidence  # -1 to 0
    else:
        return 0.0  # neutral

def _ml_label_to_emoji(label: str) -> str:
    """Convert ML label to emoji label."""
    label_lower = label.lower()
    
    if label_lower == 'positive':
        return '🟢 Positive'
    elif label_lower == 'negative':
        return '🔴 Negative'
    else:
        return '🟡 Neutral'
