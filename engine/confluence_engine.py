def analyze(ai, smc, gann, fib, regime):

    score = 0
    reasons = []

    score += ai.get("score", 0)
    score += smc.get("score", 0)
    score += gann.get("score", 0)
    score += fib.get("score", 0)
    score += regime.get("score", 0)

    reasons += ai.get("reasons", [])
    reasons += smc.get("reasons", [])
    reasons += gann.get("reasons", [])
    reasons += fib.get("reasons", [])
    reasons += regime.get("reasons", [])

    if score >= 15:
        decision = "🟢 STRONG BUY"

    elif score >= 8:
        decision = "🟢 BUY"

    elif score <= -15:
        decision = "🔴 STRONG SELL"

    elif score <= -8:
        decision = "🔴 SELL"

    else:
        decision = "⚪ NO TRADE"

    probability = min(95, max(50, 50 + score * 2))

    return {
        "score": score,
        "decision": decision,
        "probability": probability,
        "reasons": reasons
    }
