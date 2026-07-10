
"""
Jaguar Quant X Enterprise
Phase 5.2.10
Multi-Timeframe Confluence Engine
"""


class MTFEngine:

    TIMEFRAMES = ["15m", "1h", "4h", "1d"]

    @staticmethod
    def score_to_signal(score):

        if score >= 60:
            return "BUY"

        elif score <= -60:
            return "SELL"

        return "WAIT"

    @staticmethod
    def analyze(state):

        frames = {}

        buy = 0
        sell = 0
        wait = 0

        reasons = []

        timeframes = getattr(state, "timeframes", {}) or {}

        for tf in MTFEngine.TIMEFRAMES:

            score = 0

            if tf in timeframes:

                candles = timeframes[tf].get("candles", [])

                if len(candles) >= 50:

                    first = candles[-50]["close"]
                    last = candles[-1]["close"]

                    if first != 0:

                        change = ((last - first) / first) * 100

                        score = int(change * 20)

                        score = max(-100, min(100, score))

            signal = MTFEngine.score_to_signal(score)

            frames[tf] = {
                "score": score,
                "signal": signal,
            }

            if signal == "BUY":
                buy += 1

            elif signal == "SELL":
                sell += 1

            else:
                wait += 1

        alignment = max(buy, sell)

        if buy >= 3:
            bias = "BULLISH"

        elif sell >= 3:
            bias = "BEARISH"

        else:
            bias = "NEUTRAL"

        strength = int((alignment / 4) * 100)

        reasons.append(f"{buy} BUY timeframe(s)")
        reasons.append(f"{sell} SELL timeframe(s)")
        reasons.append(f"{wait} WAIT timeframe(s)")

        if bias == "BULLISH":
            reasons.append("Higher timeframe bullish alignment")

        elif bias == "BEARISH":
            reasons.append("Higher timeframe bearish alignment")

        else:
            reasons.append("Mixed timeframe alignment")

        return {
            "engine": "MultiTimeframe",
            "frames": frames,
            "buy": buy,
            "sell": sell,
            "wait": wait,
            "alignment": alignment,
            "bias": bias,
            "strength": strength,
            "confidence": strength,
            "signal": bias,
            "score": strength,
            "reasons": reasons,
        }
