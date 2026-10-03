# engine/trade_planner.py
from indicators.atr import atr

def analyze(state):
    """
    PHASE 7.6: Trade Planner now ONLY reads the Master Decision.
    No independent decision-making.
    """

    # 1. Grab the single source of truth
    md = state.master_decision
    
    # 2. If the Master says WAIT or REJECT, we bail out (No Trade Plan)
    if md["decision"] not in ["BUY", "SELL"]:
        return None

    # 3. Master gave permission! Now calculate the technical plan (Entry, SL, TP)
    if state.price <= 0:
        return None

    entry = state.price
    
    # Safely get ATR (use 0.0 if missing, or calculate it on the fly)
    atr_value = 0.0
    if hasattr(state, "atr") and state.atr:
        atr_value = float(state.atr)
    else:
        # Fallback: if ATR isn't stored, calculate it from candles if available
        try:
            if hasattr(state, "candles") and len(state.candles) > 14:
                atr_value = atr(state.candles, 14)
            else:
                atr_value = entry * 0.01  # 1% fallback
        except:
            atr_value = entry * 0.01  # 1% fallback if anything breaks

    # 4. Build the plan based on Master's direction
    if md["decision"] == "BUY":
        stop = entry - atr_value
        tp1 = entry + atr_value
        tp2 = entry + atr_value * 2
        tp3 = entry + atr_value * 3
        direction = "BUY"
    else:  # SELL
        stop = entry + atr_value
        tp1 = entry - atr_value
        tp2 = entry - atr_value * 2
        tp3 = entry - atr_value * 3
        direction = "SELL"

    risk = abs(entry - stop)
    reward = abs(tp3 - entry)
    rr = round(reward / risk, 2) if risk > 0 else 0

    # 5. Return the plan (which will be stored in state.trade_plan)
    return {
        "Direction": direction,
        "Entry": round(entry, 2),
        "StopLoss": round(stop, 2),
        "TP1": round(tp1, 2),
        "TP2": round(tp2, 2),
        "TP3": round(tp3, 2),
        "RiskReward": rr,
        # Add the Master's signature so we know who approved it
        "Approved_By": "MasterDecisionEngine",
        "Master_Score": md.get("score", 0),
        "Master_Grade": md.get("grade", "F")
    }
