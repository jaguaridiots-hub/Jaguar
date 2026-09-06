from engine.ai_brain import analyze as tech_ai
from engine.smart_money import analyze as smc_ai


def analyze(state):

    tech = tech_ai(state)
    smc = smc_ai(state)

    # Weight
    TECH_WEIGHT = 0.55
    SMC_WEIGHT = 0.45

    final_score = (
        tech["score"] * TECH_WEIGHT +
        smc["score"] * SMC_WEIGHT
    )

    probability = (
        tech["probability"] * TECH_WEIGHT +
        smc["probability"] * SMC_WEIGHT
    )

    probability = int(max(0, min(100, probability)))

    reasons = []
    reasons.extend(tech["reasons"])
    reasons.extend(smc["reasons"])

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

    if probability < 60:
        decision = "⚪ NO TRADE"

    elif final_score >= 10:
        decision = "🟢 STRONG BUY"

    elif final_score >= 6:
        decision = "🟢 BUY"

    elif final_score >= 3:
        decision = "🟡 WATCH"

    elif final_score <= -10:
        decision = "🔴 STRONG SELL"

    elif final_score <= -6:
        decision = "🔴 SELL"

    else:
        decision = "⚪ NEUTRAL"

    state.ai_score = round(final_score, 2)
    state.probability = probability
    state.confidence = confidence
    state.decision = decision

    return {
        "score": round(final_score, 2),
        "probability": probability,
        "confidence": confidence,
        "decision": decision,
        "reasons": reasons
    }
