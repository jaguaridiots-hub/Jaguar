class PatternEngine:

    @staticmethod
    def detect(candles):

        if len(candles) < 2:
            return {
                "pattern": "NONE",
                "signal": "NONE",
                "strength": 0
            }

        last = candles[-1]
        prev = candles[-2]

        o = last["open"]
        h = last["high"]
        l = last["low"]
        c = last["close"]

        po = prev["open"]
        pc = prev["close"]

        body = abs(c - o)
        candle_range = h - l

        upper = h - max(o, c)
        lower = min(o, c) - l

        # Doji
        if candle_range > 0 and body <= candle_range * 0.10:
            return {
                "pattern": "DOJI",
                "signal": "NEUTRAL",
                "strength": 40
            }

        # Hammer
        if lower > body * 2 and upper < body:
            return {
                "pattern": "HAMMER",
                "signal": "BUY",
                "strength": 70
            }

        # Shooting Star
        if upper > body * 2 and lower < body:
            return {
                "pattern": "SHOOTING_STAR",
                "signal": "SELL",
                "strength": 70
            }

        # Bullish Engulfing
        if pc < po and c > o and c >= po and o <= pc:
            return {
                "pattern": "BULLISH_ENGULFING",
                "signal": "BUY",
                "strength": 90
            }

        # Bearish Engulfing
        if pc > po and c < o and o >= pc and c <= po:
            return {
                "pattern": "BEARISH_ENGULFING",
                "signal": "SELL",
                "strength": 90
            }

        return {
            "pattern": "NONE",
            "signal": "NONE",
            "strength": 0
        }
