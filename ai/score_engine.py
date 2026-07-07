class ScoreEngine:

    @staticmethod
    def calculate(ind):

        score = 0
        reasons = []

        # ================= EMA =================
        if ind["ema"]["ema20"] > ind["ema"]["ema50"] > ind["ema"]["ema100"]:
            score += 30
            reasons.append("EMA Bullish")

        elif ind["ema"]["ema20"] < ind["ema"]["ema50"] < ind["ema"]["ema100"]:
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
        if ind["regime"]["regime"] == "BULLISH":
            score += 15
            reasons.append("Bullish Market Regime")

        elif ind["regime"]["regime"] == "BEARISH":
            score -= 15
            reasons.append("Bearish Market Regime")

        # ================= Market Structure =================
        if ind["structure"]["trend"] == "BULLISH":
            score += 15
            reasons.append("Bullish Structure")

        elif ind["structure"]["trend"] == "BEARISH":
            score -= 15
            reasons.append("Bearish Structure")

        if ind["structure"]["bos"]:
            score += 10
            reasons.append("Break of Structure")

        if ind["structure"]["choch"]:
            score += 10
            reasons.append("CHoCH")

        # ================= Order Block =================
        if ind["order_block"]["type"] == "BULLISH":
            score += 20
            reasons.append("Bullish Order Block")

        elif ind["order_block"]["type"] == "BEARISH":
            score -= 20
            reasons.append("Bearish Order Block")

        # ================= Liquidity =================
        if ind["liquidity"]["type"] == "BULLISH":
            score += 15
            reasons.append("Buy-side Liquidity Sweep")

        elif ind["liquidity"]["type"] == "BEARISH":
            score -= 15
            reasons.append("Sell-side Liquidity Sweep")

        # ================= Fair Value Gap =================
        if ind["fvg"]["found"]:

            if ind["fvg"]["type"] == "BULLISH":
                score += 15
                reasons.append("Bullish FVG")

            elif ind["fvg"]["type"] == "BEARISH":
                score -= 15
                reasons.append("Bearish FVG")

        # ================= Premium Discount =================
        if ind["pd"]["zone"] == "DISCOUNT":
            score += 10
            reasons.append("Discount Zone")

        elif ind["pd"]["zone"] == "PREMIUM":
            score -= 10
            reasons.append("Premium Zone")

        # ================= Gann Angle =================
        if ind["gann_angle"]["angle"] == "1x1 BULLISH":
            score += 20
            reasons.append("Bullish Gann Angle")

        else:
            score -= 20
            reasons.append("Bearish Gann Angle")

        # ================= Gann Swing =================
        if ind["gann_swing"]["signal"] == "BUY":
            score += 20
            reasons.append("Bullish Gann Swing")

        elif ind["gann_swing"]["signal"] == "SELL":
            score -= 20
            reasons.append("Bearish Gann Swing")

        # ================= Gann Cycle =================
        if ind["gann_square"]["bias"] == "BULLISH":
            score += 20
            reasons.append("Major Gann Cycle")

        else:
            score -= 20
            reasons.append("Minor Gann Cycle")

        # ================= Confidence =================
        confidence = max(0, min(100, int((score + 100) / 2)))

        return {
            "score": score,
            "confidence": confidence,
            "reasons": reasons
        }
