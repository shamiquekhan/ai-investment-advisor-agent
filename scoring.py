"""Scoring and recommendation helpers for stock advisor."""


def calculate_ai_score(stock_data: dict) -> float:
    """Compute a simple AI-style score from stock metrics."""
    if not stock_data.get("success", False):
        return 0.0

    score = 5.0

    change = float(stock_data.get("change", 0))
    if change > 5:
        score += 2.5
    elif change > 2:
        score += 1.5
    elif change > 0:
        score += 0.5
    elif change < -5:
        score -= 2.5
    elif change < -2:
        score -= 1.5

    rsi = float(stock_data.get("rsi", 50))
    if rsi < 30:
        score += 2
    elif rsi > 70:
        score -= 1.5
    elif rsi < 50:
        score += 0.5

    pe_str = stock_data.get("pe", "N/A")
    try:
        pe = float(pe_str) if pe_str != "N/A" else 50
        if 0 < pe < 15:
            score += 1.5
        elif pe < 25:
            score += 1
        elif pe > 40:
            score -= 1
    except Exception:
        pass

    dividend = float(stock_data.get("dividend", 0))
    if dividend > 3:
        score += 0.5

    volume = float(stock_data.get("volume", 0))
    if volume > 10_000_000:
        score += 0.3

    return round(min(max(score, 1), 10), 1)


def get_recommendation(score: float) -> str:
    """Convert a numeric score to a buy/hold/sell recommendation label."""
    if score >= 8.5:
        return "🟢 STRONG BUY"
    if score >= 7.0:
        return "🟢 BUY"
    if score >= 5.5:
        return "🟡 HOLD"
    if score >= 4.0:
        return "🔴 SELL"
    return "🔴 STRONG SELL"
