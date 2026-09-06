def analyze(state, plan, capital=100000, risk_percent=1):

    if not plan:
        return None

    entry = plan.get("Entry")
    stop = plan.get("StopLoss")

    if entry is None or stop is None:
        return None

    risk_amount = capital * risk_percent / 100

    risk_per_unit = abs(entry - stop)

    if risk_per_unit <= 0:
        return None

    quantity = risk_amount / risk_per_unit

    reward = abs(plan["TP3"] - entry)
    rr = reward / risk_per_unit

    if rr >= 3:
        grade = "A+"
    elif rr >= 2:
        grade = "A"
    elif rr >= 1.5:
        grade = "B"
    else:
        grade = "C"

    return {
        "Capital": capital,
        "RiskPercent": risk_percent,
        "RiskAmount": round(risk_amount, 2),
        "Quantity": round(quantity, 4),
        "RiskPerUnit": round(risk_per_unit, 2),
        "RiskReward": round(rr, 2),
        "Grade": grade,
        "PositionSize": round(quantity, 4)
    }
