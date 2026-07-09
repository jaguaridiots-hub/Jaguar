from strategy.bos_engine import BOSEngine
from strategy.choch_engine import CHoCHEngine


class StructureEngine:

    @staticmethod
    def analyze(candles):

        bos = BOSEngine.analyze(candles)
        choch = CHoCHEngine.analyze(candles)

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

        return {
            "score": score,
            "bos": bos,
            "choch": choch,
            "reasons": reasons
        }
