def regime_score(state):

    score = 0
    reasons = []

    if state.atr > 120:
        score += 2
        reasons.append("Trending Market")

    elif state.atr < 60:
        score -= 2
        reasons.append("Range Market")

    return score, reasons
