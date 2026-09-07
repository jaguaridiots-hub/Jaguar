from analysis.bos_engine import bos_score
from analysis.liquidity_engine import liquidity_score
from analysis.orderblock_engine import orderblock_score
from analysis.fvg_engine import fvg_score
from analysis.premium_discount_engine import premium_discount_score


def analyze(state):
    total_score = 0
    reasons = []

    modules = [
        bos_score,
        liquidity_score,
        orderblock_score,
        fvg_score,
        premium_discount_score
    ]

    for module in modules:
        try:
            score, msg = module()
            total_score += score
            reasons.extend(msg)
        except Exception as e:
            reasons.append(f"{module.__name__} Error: {e}")

    # Confidence
    if total_score >= 8:
        confidence = "A"

    elif total_score >= 5:
        confidence = "B"

    elif total_score >= 2:
        confidence = "C"

    elif total_score >= 0:
        confidence = "D"

    else:
        confidence = "F"

    # Decision
    if total_score >= 8:
        decision = "🟢 STRONG BUY"

    elif total_score >= 5:
        decision = "🟢 BUY"

    elif total_score >= 2:
        decision = "🟡 WAIT"

    elif total_score <= -8:
        decision = "🔴 STRONG SELL"

    elif total_score <= -5:
        decision = "🔴 SELL"

    else:
        decision = "⚪ NEUTRAL"

    probability = max(5, min(95, 50 + total_score * 5))

    return {
        "score": total_score,
        "confidence": confidence,
        "probability": probability,
        "decision": decision,
        "reasons": reasons,
    }


if __name__ == "__main__":

    result = analyze(None)

    print("\n========== JAGUAR SMART MONEY ==========\n")

    print("Score       :", result["score"])
    print("Confidence  :", result["confidence"])
    print("Probability :", result["probability"], "%")
    print("Decision    :", result["decision"])

    print("\nReasons")
    print("----------------------------------------")

    for r in result["reasons"]:
        print("•", r)
