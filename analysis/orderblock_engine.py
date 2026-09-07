def orderblock_score():

    score = 0
    reasons = []

    bullish_ob = True
    bearish_ob = False

    if bullish_ob and not bearish_ob:
        score += 2
        reasons.append("Bullish Order Block")

    elif bearish_ob and not bullish_ob:
        score -= 2
        reasons.append("Bearish Order Block")

    else:
        reasons.append("Neutral Order Block")

    return score, reasons
