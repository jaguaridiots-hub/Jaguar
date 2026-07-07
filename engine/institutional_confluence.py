def analyze(
    ai,
    regime,
    smc,
    bos,
    choch,
    liquidity,
    order_block,
    fvg,
    fib,
    gann,
):

    score = 0
    reasons = []

    engines = [
        ai,
        regime,
        smc,
        bos,
        choch,
        liquidity,
        order_block,
        fvg,
        fib,
        gann,
    ]

    for engine in engines:
        if engine:
            score += engine.get("score", 0)
            reasons.extend(engine.get("reasons", []))

    # Probability
    probability = max(50, min(95, 60 + score * 3))

    # Decision
    if score >= 10:
        decision = "🟢 STRONG BUY"

    elif score >= 5:
        decision = "🟢 BUY"

    elif score <= -10:
        decision = "🔴 STRONG SELL"

    elif score <= -5:
        decision = "🔴 SELL"

    else:
        decision = "⚪ NO TRADE"

    # Confidence
    if probability >= 90:
        confidence = "A+"

    elif probability >= 80:
        confidence = "A"

    elif probability >= 70:
        confidence = "B"

    elif probability >= 60:
        confidence = "C"

    else:
        confidence = "D"

    # Remove duplicate reasons
    reasons = list(dict.fromkeys(reasons))

    return {
        "decision": decision,
        "score": score,
        "probability": probability,
        "confidence": confidence,
        "reasons": reasons,
    }
