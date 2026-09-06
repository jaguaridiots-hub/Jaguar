class WyckoffEngine:

    @staticmethod
    def analyze(candles):

        recent = candles[-30:]

        highs = [c["high"] for c in recent]
        lows = [c["low"] for c in recent]
        volumes = [c["volume"] for c in recent]

        high = max(highs)
        low = min(lows)

        avg_volume = sum(volumes) / len(volumes)

        last = recent[-1]

        signal = "NONE"
        score = 0
        reasons = []

        # Accumulation
        if (
            last["close"] < low * 1.02 and
            last["volume"] > avg_volume * 1.2
        ):
            signal = "ACCUMULATION"
            score = 20
            reasons.append("Wyckoff Accumulation")

        # Distribution
        elif (
            last["close"] > high * 0.98 and
            last["volume"] > avg_volume * 1.2
        ):
            signal = "DISTRIBUTION"
            score = -20
            reasons.append("Wyckoff Distribution")

        # Spring
        elif (
            last["low"] < low and
            last["close"] > low
        ):
            signal = "SPRING"
            score = 30
            reasons.append("Wyckoff Spring")

        # Upthrust
        elif (
            last["high"] > high and
            last["close"] < high
        ):
            signal = "UPTHRUST"
            score = -30
            reasons.append("Wyckoff Upthrust")

        return {
            "signal": signal,
            "score": score,
            "range_high": high,
            "range_low": low,
            "avg_volume": round(avg_volume, 2),
            "reasons": reasons
        }
