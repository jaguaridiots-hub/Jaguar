class CHoCHEngine:

    @staticmethod
    def analyze(candles):

        last = candles[-1]
        prev = candles[-2]

        if last["high"] > prev["high"] and last["low"] > prev["low"]:
            signal = "BULLISH"

        elif last["high"] < prev["high"] and last["low"] < prev["low"]:
            signal = "BEARISH"

        else:
            signal = "SIDEWAYS"

        return {
            "signal": signal
        }
