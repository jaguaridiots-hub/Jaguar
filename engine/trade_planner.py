from indicators.atr import atr
from engine.trade_filter import analyze as trade_filter


def analyze(state):

    report = trade_filter(state)

    if not report["allow_trade"]:
        return {
            "Trade": "BLOCKED",
            "Reasons": report["reasons"],
            "Entry": None,
            "StopLoss": None,
            "TP1": None,
            "TP2": None,
            "TP3": None
        }

    entry = state.price

    if entry <= 0:
        return None

    if "BUY" in state.decision:

        stop = entry - atr

        tp1 = entry + atr
        tp2 = entry + atr * 2
        tp3 = entry + atr * 3

        direction = "🟢 BUY"

    elif "SELL" in state.decision:

        stop = entry + atr

        tp1 = entry - atr
        tp2 = entry - atr * 2
        tp3 = entry - atr * 3

        direction = "🔴 SELL"

    else:
        return None

    risk = abs(entry - stop)
    reward = abs(tp3 - entry)

    rr = round(reward / risk, 2)

    plan = {
        "Direction": direction,
        "Entry": round(entry, 2),
        "StopLoss": round(stop, 2),
        "TP1": round(tp1, 2),
        "TP2": round(tp2, 2),
        "TP3": round(tp3, 2),
        "RiskReward": rr,
        "Reasons": report["reasons"]
    }

    return plan


if __name__ == "__main__":

    from core.market_state import MarketState

    state = MarketState()

    state.price = 62750

    state.decision = "🟢 BUY"

    print(analyze(state))
