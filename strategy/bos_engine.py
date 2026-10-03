"""
Jaguar Quant X Enterprise
Institutional Break of Structure (BOS) Engine
"""


class BOSEngine:

    @staticmethod
    def analyze(candles, swing):
        """
        Detect Break of Structure using confirmed swing levels.
        """

        last = candles[-1]

        previous_swing_high = swing.get("previous_swing_high")
        previous_swing_low = swing.get("previous_swing_low")

        signal = "NONE"
        reason = ""
        confidence = 0.0

        # Bullish BOS
        if previous_swing_high and last["close"] > previous_swing_high["price"]:
            signal = "BULLISH_BOS"
            reason = "Close above previous confirmed Swing High"
            confidence = 0.80

        # Bearish BOS
        elif previous_swing_low and last["close"] < previous_swing_low["price"]:
            signal = "BEARISH_BOS"
            reason = "Close below previous confirmed Swing Low"
            confidence = 0.80

        return {
            "signal": signal,
            "high": previous_swing_high,
            "low": previous_swing_low,
            "reason": reason,
            "confidence": confidence,
        }
