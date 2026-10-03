# strategy/trade_planner_engine.py
class TradePlannerEngine:

    def run(self, state, bus):
        bus.publish("TRADE_PLANNER_ANALYSIS")

        # PHASE 7.6: Use Master Decision as the single source of truth
        md = state.master_decision
        decision = md["decision"]

        # Get current price safely
        entry = 0
        if hasattr(state, "price") and state.price:
            entry = state.price
        elif hasattr(state, "market_current") and state.market_current:
            candles = state.market_current.get("candles", [])
            if candles:
                entry = candles[-1]["close"]

        if entry <= 0:
            state.trade_plan = None
            bus.publish("TRADE_PLANNER_READY")
            return state

        # Default values
        stop = None
        tp1 = None
        tp2 = None
        rr = 0
        signal = None

        # Only proceed if Master says BUY or SELL
        if decision in ("BUY", "SELL"):
            # Get ATR (fallback to 0.5% of price)
            atr_value = entry * 0.005
            if hasattr(state, "atr") and state.atr:
                atr_value = float(state.atr)
            else:
                try:
                    if hasattr(state, "candles") and len(state.candles) > 14:
                        from indicators.atr import atr
                        atr_value = atr(state.candles, 14)
                except:
                    pass

            # ============================================================
            # MODE-SPECIFIC ATR MULTIPLIERS
            # ============================================================
            mode = getattr(state, "mode", "SWING")  # default to SWING

            if mode == "SCALP":
                stop_mult = 1.0
                tp1_mult = 1.5
                tp2_mult = 2.0
                rr_target = 2.0
            elif mode == "CLASSIC":
                stop_mult = 2.0
                tp1_mult = 3.0
                tp2_mult = 4.0
                rr_target = 4.0
            else:  # SWING
                stop_mult = 1.5
                tp1_mult = 2.5
                tp2_mult = 3.5
                rr_target = 3.0

            if decision == "BUY":
                stop = entry - atr_value * stop_mult
                tp1 = entry + atr_value * tp1_mult
                tp2 = entry + atr_value * tp2_mult
                signal = "BUY"
            else:  # SELL
                stop = entry + atr_value * stop_mult
                tp1 = entry - atr_value * tp1_mult
                tp2 = entry - atr_value * tp2_mult
                signal = "SELL"

            # Risk/Reward ratio is based on TP2
            risk = abs(entry - stop)
            reward = abs(tp2 - entry)
            rr = round(reward / risk, 2) if risk > 0 else rr_target

            state.trade_plan = {
                "signal": signal,
                "entry": round(entry, 2),
                "stop": None if stop is None else round(stop, 2),
                "tp1": None if tp1 is None else round(tp1, 2),
                "tp2": None if tp2 is None else round(tp2, 2),
                "risk_reward": rr,
                "confidence": md.get("confidence", 50),
                "grade": md.get("grade", "F"),
                "source": "MasterDecision",
                "mode": mode  # track which mode was used
            }
            print(f"📋 Trade Planner: ACCEPTING MASTER {decision} ({mode} mode)")
        else:
            # Master says WAIT or REJECT – no trade plan
            state.trade_plan = None
            print(f"📋 Trade Planner: OBEYING MASTER -> No Trade ({decision})")

        bus.publish("TRADE_PLANNER_READY")
        return state
