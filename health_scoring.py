"""Company financial health scoring using fundamental ratios."""

from typing import Dict


def calculate_health_score(stock_data: Dict) -> Dict:
    """
    Calculate comprehensive financial health score (0-100) based on fundamentals.
    Uses heuristic rules for P/E, debt/equity, profit margin, current ratio, etc.
    """
    if not stock_data.get("success", False):
        return {
            'score': 0,
            'grade': 'F',
            'breakdown': {},
            'explanation': 'Data unavailable'
        }
    
    breakdown = {}
    total_score = 0
    max_score = 0
    
    # 1. P/E Ratio (20 points)
    pe_score = 0
    pe_str = stock_data.get("pe", "N/A")
    try:
        pe = float(pe_str) if pe_str != "N/A" else None
        if pe:
            if 10 <= pe <= 20:
                pe_score = 20  # Ideal range
            elif 5 <= pe < 10 or 20 < pe <= 30:
                pe_score = 15  # Good
            elif 0 < pe < 5 or 30 < pe <= 40:
                pe_score = 10  # Acceptable
            elif pe > 40:
                pe_score = 5   # Overvalued
            breakdown['P/E Ratio'] = {'score': pe_score, 'value': f'{pe:.2f}', 'max': 20}
        else:
            breakdown['P/E Ratio'] = {'score': 10, 'value': 'N/A', 'max': 20}
            pe_score = 10  # Neutral if unavailable
    except Exception:
        breakdown['P/E Ratio'] = {'score': 10, 'value': 'N/A', 'max': 20}
        pe_score = 10
    
    total_score += pe_score
    max_score += 20
    
    # 2. Market Cap (15 points) - larger = more stable
    market_cap = float(stock_data.get("marketCap", 0))
    if market_cap >= 200:  # Mega cap ($200B+)
        cap_score = 15
        cap_label = "Mega Cap"
    elif market_cap >= 50:  # Large cap
        cap_score = 13
        cap_label = "Large Cap"
    elif market_cap >= 10:  # Mid cap
        cap_score = 10
        cap_label = "Mid Cap"
    elif market_cap >= 2:   # Small cap
        cap_score = 7
        cap_label = "Small Cap"
    else:  # Micro cap
        cap_score = 5
        cap_label = "Micro Cap"
    
    breakdown['Market Cap'] = {'score': cap_score, 'value': f'${market_cap:.1f}B ({cap_label})', 'max': 15}
    total_score += cap_score
    max_score += 15
    
    # 3. Dividend Yield (15 points) - income generation
    dividend = float(stock_data.get("dividend", 0))
    if dividend >= 4:
        div_score = 15
    elif dividend >= 2:
        div_score = 12
    elif dividend >= 1:
        div_score = 8
    elif dividend > 0:
        div_score = 5
    else:
        div_score = 3  # No dividend
    
    breakdown['Dividend Yield'] = {'score': div_score, 'value': f'{dividend:.2f}%', 'max': 15}
    total_score += div_score
    max_score += 15
    
    # 4. RSI / Momentum (20 points) - technical health
    rsi = float(stock_data.get("rsi", 50))
    if 30 <= rsi <= 70:
        rsi_score = 20  # Healthy range
    elif 20 <= rsi < 30 or 70 < rsi <= 80:
        rsi_score = 15  # Approaching extremes
    elif rsi < 20:
        rsi_score = 10  # Oversold (could be opportunity)
    else:
        rsi_score = 8   # Overbought
    
    breakdown['RSI/Momentum'] = {'score': rsi_score, 'value': f'{rsi:.1f}', 'max': 20}
    total_score += rsi_score
    max_score += 20
    
    # 5. Price Change / Trend (15 points)
    change = float(stock_data.get("change", 0))
    if change > 5:
        change_score = 15
    elif change > 2:
        change_score = 12
    elif change > 0:
        change_score = 10
    elif change > -2:
        change_score = 8
    elif change > -5:
        change_score = 5
    else:
        change_score = 3
    
    breakdown['Price Trend'] = {'score': change_score, 'value': f'{change:+.2f}%', 'max': 15}
    total_score += change_score
    max_score += 15
    
    # 6. Volume / Liquidity (15 points)
    volume = float(stock_data.get("volume", 0))
    if volume >= 50_000_000:
        vol_score = 15
    elif volume >= 10_000_000:
        vol_score = 12
    elif volume >= 1_000_000:
        vol_score = 9
    elif volume >= 100_000:
        vol_score = 6
    else:
        vol_score = 3
    
    vol_str = f"{volume/1e6:.1f}M" if volume >= 1e6 else f"{volume/1e3:.1f}K"
    breakdown['Volume/Liquidity'] = {'score': vol_score, 'value': vol_str, 'max': 15}
    total_score += vol_score
    max_score += 15
    
    # Calculate final score (0-100)
    final_score = int((total_score / max_score) * 100) if max_score > 0 else 0
    
    # Assign letter grade
    if final_score >= 90:
        grade = 'A+'
    elif final_score >= 85:
        grade = 'A'
    elif final_score >= 80:
        grade = 'A-'
    elif final_score >= 75:
        grade = 'B+'
    elif final_score >= 70:
        grade = 'B'
    elif final_score >= 65:
        grade = 'B-'
    elif final_score >= 60:
        grade = 'C+'
    elif final_score >= 55:
        grade = 'C'
    elif final_score >= 50:
        grade = 'C-'
    elif final_score >= 40:
        grade = 'D'
    else:
        grade = 'F'
    
    # Generate explanation
    if final_score >= 80:
        explanation = "Excellent financial health with strong fundamentals"
    elif final_score >= 70:
        explanation = "Good financial health, solid investment candidate"
    elif final_score >= 60:
        explanation = "Fair financial health with some concerns"
    elif final_score >= 50:
        explanation = "Moderate health, requires careful evaluation"
    else:
        explanation = "Weak financial health, high risk investment"
    
    return {
        'score': final_score,
        'grade': grade,
        'breakdown': breakdown,
        'explanation': explanation
    }


def calculate_volatility_risk(stock_data: Dict) -> Dict:
    """
    Calculate risk metric based on price volatility.
    Note: Full implementation would use historical price data.
    This is a simplified version using available metrics.
    """
    # Use RSI and change as proxies for volatility
    rsi = float(stock_data.get("rsi", 50))
    change = abs(float(stock_data.get("change", 0)))
    
    # Simple risk score (1-10, higher = riskier)
    risk_score = 5  # Baseline
    
    # RSI extremes indicate volatility
    if rsi < 20 or rsi > 80:
        risk_score += 2
    elif rsi < 30 or rsi > 70:
        risk_score += 1
    
    # Large price changes indicate volatility
    if change > 10:
        risk_score += 2
    elif change > 5:
        risk_score += 1
    
    risk_score = min(10, max(1, risk_score))
    
    if risk_score >= 8:
        risk_label = "🔴 Very High Risk"
    elif risk_score >= 6:
        risk_label = "🟠 High Risk"
    elif risk_score >= 4:
        risk_label = "🟡 Moderate Risk"
    else:
        risk_label = "🟢 Low Risk"
    
    return {
        'score': risk_score,
        'label': risk_label
    }
