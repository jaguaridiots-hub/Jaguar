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

        # --------------------------------------------------
        # Read each timeframe independently
        # --------------------------------------------------

        for tf in MTFEngine.TIMEFRAMES:

            try:

                # Future Enterprise Structure
                #
                # state.timeframes = {
                #     "15m":{"score":70},
                #     "1h":{"score":45},
                #     "4h":{"score":-20},
                #     "1d":{"score":85},
                # }

                if hasattr(state, "timeframes") and tf in state.timeframes:
                    score = state.timeframes[tf]["score"]

                else:
                    # Temporary fallback for current Jaguar
                    score = state.ai.get("score", 0)

                signal = MTFEngine.score_to_signal(score)

            except Exception:

                signal = "WAIT"
                score = 0

            frames[tf] = {
                "score": score,
                "signal": signal
            }

            if signal == "BUY":
                buy += 1

            elif signal == "SELL":
                sell += 1

            else:
                wait += 1

        # --------------------------------------------------
        # Institutional Bias
        # --------------------------------------------------

        if buy >= 3:

            bias = "BULLISH"

        elif sell >= 3:

            bias = "BEARISH"

        else:

            bias = "NEUTRAL"

        alignment = max(buy, sell)

        strength = round((alignment / 4) * 100)

        confidence = strength

        # --------------------------------------------------
        # Reasons
        # --------------------------------------------------

        reasons.append(f"{buy} BUY timeframe(s)")
        reasons.append(f"{sell} SELL timeframe(s)")
        reasons.append(f"{wait} WAIT timeframe(s)")

        if bias == "BULLISH":
            reasons.append("Higher timeframe bullish alignment")

        elif bias == "BEARISH":
            reasons.append("Higher timeframe bearish alignment")

        else:
            reasons.append("Mixed timeframe structure")

        # --------------------------------------------------
        # Return Enterprise Result
        # --------------------------------------------------

        return {

            "engine": "MultiTimeframe",

            "frames": frames,

            "buy": buy,

            "sell": sell,

            "wait": wait,

            "alignment": alignment,

            "strength": strength,

            "confidence": confidence,

            "bias": bias,

            "signal": bias,

            "score": strength,

            "reasons": reasons
        }
