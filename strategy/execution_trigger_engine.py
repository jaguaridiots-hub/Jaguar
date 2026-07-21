class ExecutionTriggerEngine:

    @staticmethod
    def analyze(state):

        score = 0
        reasons = []

        bos = getattr(state, "bos", {}) or {}
        choch = getattr(state, "choch", {}) or {}
        fvg = getattr(state, "fvg", {}) or {}
        orderblock = getattr(state, "order_block", {}) or {}
        liquidity = getattr(state, "liquidity", {}) or {}
        volume = getattr(state, "volume", {}) or {}
        vwap = getattr(state, "vwap", {}) or {}
        rsi = getattr(state, "rsi", {}) or {}

        signal = "WAIT"
        trigger = None
        fresh = False

        # BOS
        if bos.get("signal") in ("BUY", "SELL"):
            score += 20
            reasons.append("BOS confirmed")

        # CHoCH
        if choch.get("signal") in ("BUY", "SELL"):
            score += 20
            reasons.append("CHoCH confirmed")

        # FVG
        if fvg.get("active", False):
            score += 15
            reasons.append("FVG interaction")

        # Order Block
        if orderblock.get("active", False):
            score += 15
            reasons.append("Order Block active")

        # Liquidity
        if liquidity.get("sweep", False):
            score += 10
            reasons.append("Liquidity sweep")

        # Volume
        if volume.get("signal") == "HIGH VOLUME":
            score += 10
            reasons.append("High volume")

        # VWAP
        if vwap.get("signal") in ("BUY", "SELL"):
            score += 5
            reasons.append("VWAP confirmation")

        # RSI
        value = rsi.get("value", 50)
        if value >= 60 or value <= 40:
            score += 5
            reasons.append("RSI confirmation")

        # Final decision
        if score >= 80:
            signal = "STRONG BUY"
            trigger = "INSTITUTIONAL_TRIGGER"
            fresh = True

        elif score >= 60:
            signal = "BUY"
            trigger = "CONFIRMED_TRIGGER"
            fresh = True

        confirmed = score >= 60

        state.execution_trigger = {
            "confirmed": confirmed,
            "signal": signal,
            "score": score,
            "trigger": trigger,
            "fresh": fresh,
            "reasons": reasons,
        }

        return state
