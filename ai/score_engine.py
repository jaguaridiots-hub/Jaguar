class ScoreEngine:

    @staticmethod
    def calculate(ind):

        score = 0
        reasons = []

        # ================= EMA =================

        ema20 = ind["ema"]["ema20"]
        ema50 = ind["ema"]["ema50"]
        ema100 = ind["ema"]["ema100"]

        if ema20 > ema50 > ema100:
            score += 30
            reasons.append("EMA Bullish")

        elif ema20 < ema50 < ema100:
            score -= 30
            reasons.append("EMA Bearish")

        # ================= RSI =================

        rsi = ind["rsi"]["value"]

        if 45 <= rsi <= 60:
            score += 10
            reasons.append("Healthy RSI")

        elif rsi < 30:
            score += 10
            reasons.append("Oversold RSI")

        elif rsi > 70:
            score -= 10
            reasons.append("Overbought RSI")

        # ================= MACD =================

        if ind["macd"]["signal"] == "BUY":
            score += 25
            reasons.append("MACD Buy")
        else:
            score -= 25
            reasons.append("MACD Sell")

        # ================= SuperTrend =================

        if ind["supertrend"]["signal"] == "BULLISH":
            score += 20
            reasons.append("SuperTrend Bullish")
        else:
            score -= 20
            reasons.append("SuperTrend Bearish")

        # ================= VWAP =================

        if ind["vwap"]["signal"] == "ABOVE VWAP":
            score += 10
            reasons.append("Above VWAP")
        else:
            score -= 10
            reasons.append("Below VWAP")

        # ================= ADX =================

        if ind["adx"]["signal"] == "STRONG":
            score += 15
            reasons.append("Strong Trend")
        else:
            score -= 5
            reasons.append("Weak Trend")

        # ================= Volume =================

        if ind["volume"]["signal"] == "HIGH VOLUME":
            score += 10
            reasons.append("High Volume")
        else:
            score -= 5
            reasons.append("Low Volume")

        # ================= Market Regime =================

        regime = ind.get("regime", {}).get("regime", "SIDEWAYS")

        if "BULLISH" in regime:
            score += 15
            reasons.append("Bullish Market Regime")

        elif "BEARISH" in regime:
            score -= 15
            reasons.append("Bearish Market Regime")

        # ================= Clamp Score =================

        score = max(-100, min(100, score))

        confidence = round((score + 100) / 2, 2)

        # ================= Final Signal =================

        if score >= 60:
            signal = "BUY"

        elif score <= -60:
            signal = "SELL"

        else:
            signal = "HOLD"

        return {
            "score": score,
            "confidence": confidence,
            "signal": signal,
            "reasons": reasons
        }
