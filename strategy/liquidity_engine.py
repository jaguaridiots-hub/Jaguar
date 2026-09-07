class LiquidityEngine:

    @staticmethod
    def analyze(candles):

        last = candles[-1]

        highs = [c["high"] for c in candles[-10:-1]]
        lows = [c["low"] for c in candles[-10:-1]]

        signal = "NEUTRAL"
        score = 0
        reasons = []

        # Buy-side sweep
        if last["high"] > max(highs) and last["close"] < max(highs):
            signal = "BEARISH"
            score = -15
            reasons.append("Buy-side Liquidity Sweep")

        # Sell-side sweep
        elif last["low"] < min(lows) and last["close"] > min(lows):
            signal = "BULLISH"
            score = 15
            reasons.append("Sell-side Liquidity Sweep")

        return {
            "signal": signal,
            "score": score,
            "reasons": reasons
        }
