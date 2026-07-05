def confidence_score(state, reasons):

    score = 0
    confidence = []

    # EMA Alignment
    if "Bullish EMA" in reasons:
        score += 2
        confidence.append("EMA Alignment")

    # Market Structure
    if "Bullish BOS" in reasons:
        score += 2
        confidence.append("Market Structure")

    if "Bullish ChoCH" in reasons:
        score += 2
        confidence.append("Structure Shift")

    # Smart Money
    if "Bullish Order Block" in reasons:
        score += 2
        confidence.append("Institutional Order Block")

    if "Bullish FVG" in reasons:
        score += 1
        confidence.append("Fair Value Gap")

    # Volume
    if "High Volume" in reasons:
        score += 2
        confidence.append("Volume Confirmation")

    # CVD
    if "Bullish CVD" in reasons:
        score += 2
        confidence.append("Positive Delta")

    # VWAP
    if "Above VWAP" in reasons:
        score += 1
        confidence.append("Above VWAP")

    # POC
    if "Above POC" in reasons:
        score += 1
        confidence.append("Above POC")

    # Penalties
    if "Overbought" in reasons:
        score -= 2

    if "Low Volume" in reasons:
        score -= 2

    if "Daily Trend Bearish" in reasons:
        score -= 3

    return score, confidence
