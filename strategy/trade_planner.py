class TradePlanner:

    @staticmethod
    def plan(state):

        idm = getattr(state, "idm", {})
        market = getattr(state, "market_current", {})

        if not market:
            state.trade_plan = {}
            return state

        if idm.get("decision") != "ENTER":
            state.trade_plan = {
                "signal": "NO TRADE",
                "reason": "IDM rejected setup"
            }
            return state

        price = market["close"]

        atr = market.get("atr", 100)

        stop = price - (2 * atr)

        risk = price - stop

        tp1 = price + (3 * risk)

        tp2 = price + (5 * risk)

        state.trade_plan = {
            "signal": "ENTER",
            "entry": round(price, 2),
            "stop": round(stop, 2),
            "tp1": round(tp1, 2),
            "tp2": round(tp2, 2),
            "risk_reward": 3,
            "confidence": idm.get("score", 0),
            "institutional_score": idm.get("score", 0),
        }

        return state
