class MTFEngine:

    @staticmethod
    def analyze(state):

        frames = {}

        for tf in ["15m", "1h", "4h", "1d"]:

            try:
                score = state.ai["score"]

                if score >= 60:
                    signal = "BUY"

                elif score <= -60:
                    signal = "SELL"

                else:
                    signal = "WAIT"

            except Exception:
                signal = "WAIT"

            frames[tf] = signal

        buy = list(frames.values()).count("BUY")
        sell = list(frames.values()).count("SELL")

        if buy >= 3:
            bias = "BULLISH"

        elif sell >= 3:
            bias = "BEARISH"

        else:
            bias = "NEUTRAL"

        alignment = max(buy, sell)

        return {
            "frames": frames,
            "buy": buy,
            "sell": sell,
            "alignment": alignment,
            "bias": bias
        }
