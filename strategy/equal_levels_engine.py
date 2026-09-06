class EqualLevelsEngine:

    @staticmethod
    def analyze(candles):

        highs = [c["high"] for c in candles[-20:]]
        lows = [c["low"] for c in candles[-20:]]

        tolerance = 0.0015      # 0.15%

        signal = "NONE"
        score = 0
        reasons = []

        eqh = None
        eql = None

        # ---------- Equal High ----------
        for i in range(len(highs) - 1):

            if abs(highs[i] - highs[i + 1]) / highs[i] < tolerance:

                eqh = round((highs[i] + highs[i + 1]) / 2, 2)
                signal = "EQH"
                score = -15
                reasons = ["Equal High Liquidity"]
                break

        # ---------- Equal Low ----------
        if signal == "NONE":

            for i in range(len(lows) - 1):

                if abs(lows[i] - lows[i + 1]) / lows[i] < tolerance:

                    eql = round((lows[i] + lows[i + 1]) / 2, 2)
                    signal = "EQL"
                    score = 15
                    reasons = ["Equal Low Liquidity"]
                    break

        return {
            "signal": signal,
            "score": score,
            "equal_high": eqh,
            "equal_low": eql,
            "reasons": reasons
        }
