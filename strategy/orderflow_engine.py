class OrderFlowEngine:

    def run(self, state, bus):

        candles = state.market_current["candles"]

        last = candles[-1]
        prev = candles[-2]

        buy = 0
        sell = 0
        reasons = []

        # ==========================
        # Candle Direction
        # ==========================
        if last["close"] > last["open"]:
            buy += 15
            reasons.append("Bullish Candle")
        else:
            sell += 15
            reasons.append("Bearish Candle")

        # ==========================
        # Volume Spike
        # ==========================
        avg_volume = sum(c["volume"] for c in candles[-20:]) / 20

        if last["volume"] > avg_volume * 1.5:
            if last["close"] > last["open"]:
                buy += 20
                reasons.append("Bullish Volume Spike")
            else:
                sell += 20
                reasons.append("Bearish Volume Spike")

        # ==========================
        # Candle Body Strength
        # ==========================
        body = abs(last["close"] - last["open"])
        rng = max(last["high"] - last["low"], 0.000001)

        if body / rng > 0.6:
            if last["close"] > last["open"]:
                buy += 15
                reasons.append("Strong Bull Body")
            else:
                sell += 15
                reasons.append("Strong Bear Body")

        # ==========================
        # Break Previous High/Low
        # ==========================
        if last["high"] > prev["high"]:
            buy += 10
            reasons.append("High Break")

        if last["low"] < prev["low"]:
            sell += 10
            reasons.append("Low Break")

        # ==========================
        # Price vs POC
        # ==========================
        vp = getattr(state, "volume_profile", {}) or {}

        poc = vp.get("poc")
        if poc:
            if last["close"] > poc:
                buy += 10
                reasons.append("Above POC")
            else:
                sell += 10
                reasons.append("Below POC")

        # ==========================
        # Multi-Timeframe Bias
        # ==========================
        mtf = getattr(state, "mtf", None)
        if not isinstance(mtf, dict):
            mtf = {}

        if mtf.get("bias") == "BULLISH":
            buy += 10
            reasons.append("Bullish MTF")
        elif mtf.get("bias") == "BEARISH":
            sell += 10
            reasons.append("Bearish MTF")

        # ==========================
        # Delta
        # ==========================
        delta = buy - sell

        if delta >= 20:
            signal = "BULLISH"
        elif delta <= -20:
            signal = "BEARISH"
        else:
            signal = "NEUTRAL"

        state.orderflow = {
            "signal": signal,
            "buy_pressure": buy,
            "sell_pressure": sell,
            "delta": delta,
            "score": abs(delta),
            "reasons": reasons,
        }

        return state
