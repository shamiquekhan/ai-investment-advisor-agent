"""
HuggingFace ML Models for Financial Analysis
Provides sentiment analysis, NER, and summarization using free, domain-specific models.
"""

import os
from typing import Dict, List, Optional, Tuple
from functools import lru_cache
import warnings
warnings.filterwarnings('ignore')

# Try importing transformers, provide graceful fallback
try:
    from transformers import (
        pipeline,
        AutoTokenizer,
        AutoModelForSequenceClassification,
        AutoModelForTokenClassification
    )
    import torch
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    print("⚠️ transformers not installed. ML features disabled.")
    print("   Install with: pip install transformers torch sentencepiece")

# ============================================================================
# MODEL CACHE - Load once, reuse forever
# ============================================================================

_SENTIMENT_MODEL = None
_NER_MODEL = None
_SUMMARIZER_MODEL = None

@lru_cache(maxsize=1)
def get_sentiment_model():
    """
    Load FinBERT sentiment analysis model (cached).
    Model: ProsusAI/finbert (110M params, financial-domain BERT)
    Labels: positive, negative, neutral
    """
    global _SENTIMENT_MODEL
    
    if not HF_AVAILABLE:
        return None
    
    if _SENTIMENT_MODEL is None:
        try:
            print("📥 Loading FinBERT sentiment model (one-time download)...")
            _SENTIMENT_MODEL = pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert",
                device=-1  # CPU (use 0 for GPU)
            )
            print("✅ FinBERT loaded successfully!")
        except Exception as e:
            print(f"⚠️ Failed to load FinBERT: {e}")
            return None
    
    return _SENTIMENT_MODEL

@lru_cache(maxsize=1)
def get_ner_model():
    """
    Load FinBERT-NER model (cached).
    Model: yiyanghkust/finbert-ner
    Entities: Company names, money amounts, dates, locations
    """
    global _NER_MODEL
    
    if not HF_AVAILABLE:
        return None
    
    if _NER_MODEL is None:
        try:
            print("📥 Loading FinBERT-NER model (one-time download)...")
            _NER_MODEL = pipeline(
                "ner",
                model="yiyanghkust/finbert-ner",
                aggregation_strategy="simple",
                device=-1
            )
            print("✅ FinBERT-NER loaded successfully!")
        except Exception as e:
            print(f"⚠️ Failed to load FinBERT-NER: {e}")
            return None
    
    return _NER_MODEL

@lru_cache(maxsize=1)
def get_summarizer_model():
    """
    Load BART summarization model (cached).
    Model: facebook/bart-large-cnn
    Use: Summarize long financial documents
    """
    global _SUMMARIZER_MODEL
    
    if not HF_AVAILABLE:
        return None
    
    if _SUMMARIZER_MODEL is None:
        try:
            print("📥 Loading BART summarizer (one-time download)...")
            _SUMMARIZER_MODEL = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                device=-1
            )
            print("✅ BART summarizer loaded successfully!")
        except Exception as e:
            print(f"⚠️ Failed to load BART: {e}")
            return None
    
    return _SUMMARIZER_MODEL

# ============================================================================
# SENTIMENT ANALYSIS
# ============================================================================

def analyze_financial_sentiment(text: str) -> Dict[str, any]:
    """
    Analyze sentiment of financial text using FinBERT.
    
    Args:
        text: Financial news headline, earnings snippet, etc.
    
    Returns:
        {
            'label': 'positive'|'negative'|'neutral',
            'score': 0.95,  # confidence
            'raw_text': original text
        }
    """
    if not text or len(text.strip()) < 10:
        return {
            'label': 'neutral',
            'score': 0.0,
            'raw_text': text,
            'error': 'Text too short'
        }
    
    model = get_sentiment_model()
    if model is None:
        # Fallback to basic keyword sentiment
        return _fallback_sentiment(text)
    
    try:
        # FinBERT has max length 512 tokens, truncate if needed
        text_truncated = text[:512]
        
        result = model(text_truncated)[0]
        
        return {
            'label': result['label'].lower(),
            'score': result['score'],
            'raw_text': text,
            'model': 'finbert'
        }
    
    except Exception as e:
        print(f"⚠️ Sentiment analysis error: {e}")
        return _fallback_sentiment(text)

def analyze_batch_sentiment(texts: List[str], max_batch: int = 8) -> List[Dict]:
    """
    Analyze sentiment for multiple texts efficiently.
    
    Args:
        texts: List of financial texts
        max_batch: Batch size for inference
    
    Returns:
        List of sentiment dicts
    """
    model = get_sentiment_model()
    if model is None:
        return [_fallback_sentiment(t) for t in texts]
    
    results = []
    for i in range(0, len(texts), max_batch):
        batch = texts[i:i+max_batch]
        try:
            batch_results = model(batch)
            for text, result in zip(batch, batch_results):
                results.append({
                    'label': result['label'].lower(),
                    'score': result['score'],
                    'raw_text': text,
                    'model': 'finbert'
                })
        except Exception as e:
            print(f"⚠️ Batch sentiment error: {e}")
            results.extend([_fallback_sentiment(t) for t in batch])
    
    return results

def _fallback_sentiment(text: str) -> Dict:
    """Basic keyword-based sentiment fallback."""
    text_lower = text.lower()
    
    positive_words = ['beat', 'surge', 'gain', 'profit', 'growth', 'up', 'record', 'strong', 'exceeds', 'bullish']
    negative_words = ['miss', 'loss', 'fall', 'drop', 'down', 'weak', 'decline', 'bearish', 'concern', 'risk']
    
    pos_count = sum(1 for word in positive_words if word in text_lower)
    neg_count = sum(1 for word in negative_words if word in text_lower)
    
    if pos_count > neg_count:
        label = 'positive'
        score = 0.6
    elif neg_count > pos_count:
        label = 'negative'
        score = 0.6
    else:
        label = 'neutral'
        score = 0.5
    
    return {
        'label': label,
        'score': score,
        'raw_text': text,
        'model': 'keyword_fallback'
    }

# ============================================================================
# NAMED ENTITY RECOGNITION
# ============================================================================

def extract_financial_entities(text: str) -> List[Dict]:
    """
    Extract named entities from financial text.
    
    Args:
        text: Financial news or document
    
    Returns:
        List of entities: [
            {'entity': 'ORG', 'word': 'Apple Inc.', 'score': 0.99},
            {'entity': 'MONEY', 'word': '$120 billion', 'score': 0.95},
            ...
        ]
    """
    model = get_ner_model()
    if model is None:
        return []
    
    try:
        entities = model(text)
        return [
            {
                'entity': ent['entity_group'],
                'word': ent['word'],
                'score': ent['score']
            }
            for ent in entities
        ]
    except Exception as e:
        print(f"⚠️ NER error: {e}")
        return []

# ============================================================================
# TEXT SUMMARIZATION
# ============================================================================

def summarize_financial_text(
    text: str,
    max_length: int = 100,
    min_length: int = 30
) -> str:
    """
    Summarize long financial documents.
    
    Args:
        text: Long financial text (earnings call, 10-K section)
        max_length: Maximum summary length in tokens
        min_length: Minimum summary length in tokens
    
    Returns:
        Concise summary string
    """
    if len(text) < 200:
        return text  # Too short to summarize
    
    model = get_summarizer_model()
    if model is None:
        # Fallback: return first 200 chars
        return text[:200] + "..."
    
    try:
        summary = model(
            text,
            max_length=max_length,
            min_length=min_length,
            do_sample=False
        )
        return summary[0]['summary_text']
    
    except Exception as e:
        print(f"⚠️ Summarization error: {e}")
        return text[:200] + "..."

# ============================================================================
# SCORING & ANALYSIS
# ============================================================================

def calculate_ml_sentiment_score(news_articles: List[Dict]) -> Tuple[float, str]:
    """
    Calculate aggregate sentiment score from news articles using ML.
    
    Args:
        news_articles: List of news dicts with 'title' and 'description'
    
    Returns:
        (score, label) where:
            score: -1.0 (very negative) to +1.0 (very positive)
            label: '🟢 Positive' | '🔴 Negative' | '🟡 Neutral'
    """
    if not news_articles:
        return 0.0, '🟡 Neutral'
    
    # Combine title + description for each article
    texts = []
    for article in news_articles[:10]:  # Limit to 10 most recent
        title = article.get('title', '')
        desc = article.get('description', '')
        combined = f"{title}. {desc}".strip()
        if combined:
            texts.append(combined)
    
    if not texts:
        return 0.0, '🟡 Neutral'
    
    # Batch sentiment analysis
    sentiments = analyze_batch_sentiment(texts)
    
    # Calculate weighted score
    total_score = 0.0
    for sent in sentiments:
        label = sent['label']
        confidence = sent['score']
        
        if label == 'positive':
            total_score += confidence
        elif label == 'negative':
            total_score -= confidence
        # neutral contributes 0
    
    # Normalize to [-1, 1]
    avg_score = total_score / len(sentiments) if sentiments else 0.0
    
    # Determine label
    if avg_score > 0.3:
        label = '🟢 Positive'
    elif avg_score < -0.3:
        label = '🔴 Negative'
    else:
        label = '🟡 Neutral'
    
    return avg_score, label

def get_ml_insights(ticker: str, news_articles: List[Dict]) -> Dict:
    """
    Generate ML-powered insights for a stock.
    
    Args:
        ticker: Stock symbol
        news_articles: Recent news articles
    
    Returns:
        {
            'sentiment_score': 0.75,
            'sentiment_label': '🟢 Positive',
            'article_count': 5,
            'positive_count': 3,
            'negative_count': 1,
            'neutral_count': 1,
            'key_entities': ['Apple Inc.', '$120B', 'Q4 2024'],
            'model_used': 'finbert'
        }
    """
    score, label = calculate_ml_sentiment_score(news_articles)
    
    # Analyze all articles for sentiment breakdown
    texts = [f"{a.get('title', '')}. {a.get('description', '')}".strip() 
             for a in news_articles[:10]]
    sentiments = analyze_batch_sentiment(texts) if texts else []
    
    pos_count = sum(1 for s in sentiments if s['label'] == 'positive')
    neg_count = sum(1 for s in sentiments if s['label'] == 'negative')
    neu_count = sum(1 for s in sentiments if s['label'] == 'neutral')
    
    # Extract key entities from top article
    entities = []
    if news_articles:
        top_article = news_articles[0]
        text = f"{top_article.get('title', '')}. {top_article.get('description', '')}".strip()
        entities = extract_financial_entities(text)
    
    return {
        'sentiment_score': round(score, 2),
        'sentiment_label': label,
        'article_count': len(news_articles),
        'positive_count': pos_count,
        'negative_count': neg_count,
        'neutral_count': neu_count,
        'key_entities': [e['word'] for e in entities[:5]],
        'model_used': 'finbert' if HF_AVAILABLE else 'keyword_fallback'
    }

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def check_ml_availability() -> Dict[str, bool]:
    """Check which ML models are available."""
    return {
        'transformers_installed': HF_AVAILABLE,
        'sentiment_model': get_sentiment_model() is not None,
        'ner_model': get_ner_model() is not None,
        'summarizer_model': get_summarizer_model() is not None
    }

def preload_models():
    """Preload all models (call at startup to avoid first-request delay)."""
    if HF_AVAILABLE:
        print("🚀 Preloading ML models...")
        get_sentiment_model()
        # NER and summarizer are optional, load on-demand
        print("✅ Core ML models ready!")

# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTING ML MODELS")
    print("="*60)
    
    # Test 1: Sentiment Analysis
    print("\n📊 Test 1: Sentiment Analysis")
    test_texts = [
        "Apple beats earnings expectations with record Q4 revenue",
        "Tesla stock plunges on disappointing delivery numbers",
        "Microsoft announces quarterly dividend, stock holds steady"
    ]
    
    for text in test_texts:
        result = analyze_financial_sentiment(text)
        print(f"\n  Text: {text}")
        print(f"  Sentiment: {result['label'].upper()} ({result['score']:.2%})")
        print(f"  Model: {result.get('model', 'unknown')}")
    
    # Test 2: NER
    print("\n📊 Test 2: Named Entity Recognition")
    ner_text = "Apple Inc. reported $120 billion revenue for Q4 2024"
    entities = extract_financial_entities(ner_text)
    print(f"\n  Text: {ner_text}")
    print(f"  Entities found: {len(entities)}")
    for ent in entities:
        print(f"    - {ent['entity']}: {ent['word']} ({ent['score']:.2%})")
    
    # Test 3: Model availability
    print("\n📊 Test 3: Model Availability")
    availability = check_ml_availability()
    for model, available in availability.items():
        status = "✅" if available else "❌"
        print(f"  {status} {model}")
    
    print("\n✅ All tests completed!")
