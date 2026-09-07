def trade_plan(state):

    atr = state.atr

    if "BUY" in state.decision:
        entry = state.price
        stop = round(entry - atr * 1.5, 2)
        target1 = round(entry + atr * 2, 2)
        target2 = round(entry + atr * 3.5, 2)

    elif "SELL" in state.decision:
        entry = state.price
        stop = round(entry + atr * 1.5, 2)
        target1 = round(entry - atr * 2, 2)
        target2 = round(entry - atr * 3.5, 2)

    else:
        return None

    return {
        "Direction": state.decision,
        "Entry": entry,
        "Stop": stop,
        "TP1": tp1,
        "TP2": tp2,
        "RR": rr
    }
