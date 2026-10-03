from strategy.bos_engine import BOSEngine
from strategy.choch_engine import CHoCHEngine
from strategy.swing_engine import SwingEngine

class StructureEngine:

    @staticmethod
    def analyze(candles):

        swing = SwingEngine.analyze(candles)

        bos = BOSEngine.analyze(candles, swing)

        print("\n========== BOS DEBUG ==========")
        print("Previous Swing High :", swing["previous_swing_high"])
        print("Previous Swing Low  :", swing["previous_swing_low"])
        print("Last Close          :", candles[-1]["close"])
        print("BOS Result          :", bos)

        choch = CHoCHEngine.analyze(candles, swing)

        score = 0
        reasons = []

        if bos["signal"] == "BULLISH_BOS":
            score += 25
            reasons.append("Bullish BOS")

        elif bos["signal"] == "BEARISH_BOS":
            score -= 25
            reasons.append("Bearish BOS")

        if choch["signal"] == "BULLISH":
            score += 15
            reasons.append("Bullish CHoCH")

        elif choch["signal"] == "BEARISH":
            score -= 15
            reasons.append("Bearish CHoCH")

        print("\n========== SWING ENGINE ==========")
        print("Trend :", swing["trend"])
        print("Swing High :", swing["swing_high"])
        print("Swing Low :", swing["swing_low"])
        print("Total Pivots :", len(swing["pivots"]))
        print("Total Swings :", len(swing["swings"]))

        return {
            "score": score,
            "bos": bos,
            "choch": choch,
            "swing": swing,
            "trend": swing["trend"],
            "reasons": reasons
        }
