"""News fetching and sentiment analysis using RSS feeds (no API keys needed)."""

import time
from datetime import datetime, timedelta
from typing import List, Dict

import feedparser
import streamlit as st


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
def fetch_stock_news(ticker: str, max_articles: int = 5) -> List[Dict]:
    """
    Fetch recent news for a stock from Yahoo Finance RSS feed.
    Returns list of articles with title, link, published date, and sentiment.
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
                
                # Calculate sentiment
                sentiment_score = calculate_sentiment_score(text)
                
                articles.append({
                    'title': title,
                    'link': entry.get('link', ''),
                    'published': pub_date.strftime('%Y-%m-%d %H:%M'),
                    'sentiment_score': sentiment_score,
                    'sentiment_label': get_sentiment_label(sentiment_score),
                    'summary': summary[:200] + '...' if len(summary) > 200 else summary
                })
                
                if len(articles) >= max_articles:
                    break
                    
            except Exception:
                continue
        
        return articles
        
    except Exception:
        # Fallback: return empty list if RSS fails
        return []


def calculate_overall_sentiment(articles: List[Dict]) -> Dict:
    """
    Calculate overall sentiment from multiple articles.
    Returns dict with score, label, and article count.
    """
    if not articles:
        return {
            'score': 0.0,
            'label': '🟡 No Recent News',
            'article_count': 0
        }
    
    avg_score = sum(a['sentiment_score'] for a in articles) / len(articles)
    
    return {
        'score': round(avg_score, 2),
        'label': get_sentiment_label(avg_score),
        'article_count': len(articles)
    }
