"""Scoring and recommendation helpers for stock advisor."""

from typing import Dict, Optional


def calculate_ai_score(stock_data: dict, health_score: Optional[int] = None, 
                       sentiment_score: Optional[float] = None) -> float:
    """
    Compute enhanced AI score incorporating fundamentals, technicals, health, and sentiment.
    
    Weights:
    - Base fundamentals: 40%
    - Health score: 30%
    - Sentiment: 20%
    - Technical (RSI): 10%
    """
    if not stock_data.get("success", False):
        return 0.0

    # Base score (40% weight) - fundamentals and momentum
    base_score = 4.0  # Out of 10, so 4 = 40%
    
    # Momentum/Price change (15% of base)
    change = float(stock_data.get("change", 0))
    if change > 5:
        base_score += 1.5
    elif change > 2:
        base_score += 1.0
    elif change > 0:
        base_score += 0.5
    elif change < -5:
        base_score -= 1.5
    elif change < -2:
        base_score -= 1.0

    # P/E ratio (15% of base)
    pe_str = stock_data.get("pe", "N/A")
    try:
        pe = float(pe_str) if pe_str != "N/A" else 50
        if 10 <= pe <= 20:
            base_score += 1.5
        elif 5 <= pe < 10 or 20 < pe <= 30:
            base_score += 1.0
        elif pe > 40:
            base_score -= 1.0
    except Exception:
        pass

    # Dividend (5% of base)
    dividend = float(stock_data.get("dividend", 0))
    if dividend > 3:
        base_score += 0.5
    elif dividend > 1:
        base_score += 0.3

    # Volume/Liquidity (5% of base)
    volume = float(stock_data.get("volume", 0))
    if volume > 10_000_000:
        base_score += 0.5

    # Health score (30% weight) - convert 0-100 to 0-3
    health_contribution = 0
    if health_score is not None:
        health_contribution = (health_score / 100) * 3.0

    # Sentiment score (20% weight) - convert -1 to +1 to 0-2
    sentiment_contribution = 1.0  # Neutral default
    if sentiment_score is not None:
        sentiment_contribution = (sentiment_score + 1) * 1.0  # Maps -1..+1 to 0..2

    # RSI (10% weight)
    rsi_contribution = 0.5  # Neutral
    rsi = float(stock_data.get("rsi", 50))
    if rsi < 30:
        rsi_contribution = 1.0  # Oversold = buying opportunity
    elif rsi < 50:
        rsi_contribution = 0.7
    elif rsi > 70:
        rsi_contribution = 0.3  # Overbought
    
    # Final score
    final_score = base_score + health_contribution + sentiment_contribution + rsi_contribution
    
    return round(min(max(final_score, 1), 10), 1)


def get_recommendation(score: float, health_grade: Optional[str] = None, 
                       sentiment_label: Optional[str] = None, 
                       risk_label: Optional[str] = None) -> Dict:
    """
    Generate comprehensive recommendation with reasoning.
    Returns dict with recommendation, confidence, and explanation.
    """
    # Base recommendation
    if score >= 8.5:
        rec = "🟢 STRONG BUY"
        confidence = "Very High"
    elif score >= 7.0:
        rec = "🟢 BUY"
        confidence = "High"
    elif score >= 5.5:
        rec = "🟡 HOLD"
        confidence = "Moderate"
    elif score >= 4.0:
        rec = "🔴 SELL"
        confidence = "Moderate"
    else:
        rec = "🔴 STRONG SELL"
        confidence = "High"
    
    # Generate explanation
    explanation_parts = []
    
    if score >= 8:
        explanation_parts.append("Strong fundamentals and positive momentum")
    elif score >= 6:
        explanation_parts.append("Solid fundamentals with decent growth prospects")
    elif score >= 5:
        explanation_parts.append("Mixed signals, suitable for hold strategy")
    else:
        explanation_parts.append("Weak fundamentals or negative momentum")
    
    if health_grade:
        if health_grade in ['A+', 'A', 'A-']:
            explanation_parts.append(f"excellent financial health ({health_grade})")
        elif health_grade in ['B+', 'B', 'B-']:
            explanation_parts.append(f"good financial health ({health_grade})")
        elif health_grade in ['C+', 'C', 'C-']:
            explanation_parts.append(f"fair financial health ({health_grade})")
        else:
            explanation_parts.append(f"concerning financial health ({health_grade})")
    
    if sentiment_label:
        if "Positive" in sentiment_label:
            explanation_parts.append("positive market sentiment")
        elif "Negative" in sentiment_label:
            explanation_parts.append("negative market sentiment")
    
    if risk_label:
        if "High Risk" in risk_label or "Very High" in risk_label:
            explanation_parts.append("note high volatility risk")
            confidence = "Low" if confidence == "Very High" else confidence
    
    explanation = ". ".join([p.capitalize() for p in explanation_parts]) + "."
    
    return {
        'recommendation': rec,
        'confidence': confidence,
        'explanation': explanation
    }
