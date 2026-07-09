class TradePlannerEngine:

    def run(self, state, bus):

        bus.publish("TRADE_PLANNER_ANALYSIS")

        brain = state.brain

        candles = state.market_current["candles"]

        last = candles[-1]["close"]

        signal = brain["signal"]

        entry = last
        stop = None
        tp1 = None
        tp2 = None
        rr = 0

        if signal in ("BUY", "STRONG BUY"):

            stop = min(
                state.structure["bos"]["low"],
                state.volume_profile["val"]
            )

            risk = entry - stop

            tp1 = entry + risk * 2
            tp2 = entry + risk * 3

            rr = 3

        elif signal in ("SELL", "STRONG SELL"):

            stop = max(
                state.structure["bos"]["high"],
                state.volume_profile["vah"]
            )

            risk = stop - entry

            tp1 = entry - risk * 2
            tp2 = entry - risk * 3

            rr = 3

        state.trade_plan = {

            "signal": signal,

            "entry": round(entry,2),

            "stop": None if stop is None else round(stop,2),

            "tp1": None if tp1 is None else round(tp1,2),

            "tp2": None if tp2 is None else round(tp2,2),

            "risk_reward": rr,

            "confidence": brain["confidence"],

            "grade": brain["grade"]
        }

        bus.publish("TRADE_PLANNER_READY")

        return state
