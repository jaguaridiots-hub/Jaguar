from core.engine_runner import run


def analyze(state):

    reports = run(state)

    total_score = 0.0
    total_weight = 0.0
    reasons = []
    engines = {}

    for item in reports:

        report = item["report"]
        weight = item["weight"]

        score = report.get("score", 0)

        total_score += score * weight
        total_weight += weight

        reasons.extend(report.get("reasons", []))

        engines[item["name"]] = report

    if total_weight == 0:
        final_score = 0
    else:
        final_score = round(total_score / total_weight, 2)

    probability = max(50, min(99, int(50 + final_score * 5)))

    if final_score >= 3:
        decision = "🟢 BUY"
    elif final_score <= -3:
        decision = "🔴 SELL"
    else:
        decision = "⚪ NO TRADE"

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

    return {
        "decision": decision,
        "score": final_score,
        "probability": probability,
        "confidence": confidence,
        "reasons": reasons,
        "engines": engines
    }
