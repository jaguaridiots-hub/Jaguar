class Candlestick:

    @staticmethod
    def detect(candles):

        last = candles[-1]

        body = abs(last["close"] - last["open"])

        upper = last["high"] - max(last["close"], last["open"])

        lower = min(last["close"], last["open"]) - last["low"]

        signal = "NONE"

        if lower > body * 2 and upper < body:
            signal = "HAMMER"

        elif upper > body * 2 and lower < body:
            signal = "SHOOTING STAR"

        elif body < (last["high"] - last["low"]) * 0.15:
            signal = "DOJI"

        return {
            "pattern": signal
        }
