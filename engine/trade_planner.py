from indicators.atr import atr


def analyze(state):

    if state.price <= 0:
        return None

    entry = state.price
    atr_value = float(getattr(state, "atr", 0.0) or 0.0)
    decision = state.decision.upper()

    if "BUY" in decision:

        stop = entry - atr_value
        tp1 = entry + atr_value
        tp2 = entry + atr_value * 2
        tp3 = entry + atr_value * 3

        direction = "BUY"

    elif "SELL" in decision:

        stop = entry + atr_value
        tp1 = entry - atr_value
        tp2 = entry - atr_value * 2
        tp3 = entry - atr_value * 3

        direction = "SELL"

    else:
        return None

    risk = abs(entry - stop)
    reward = abs(tp3 - entry)

    rr = round(reward / risk, 2) if risk > 0 else 0

    return {
        "Direction": direction,
        "Entry": round(entry, 2),
        "StopLoss": round(stop, 2),
        "TP1": round(tp1, 2),
        "TP2": round(tp2, 2),
        "TP3": round(tp3, 2),
        "RiskReward": rr
    }
