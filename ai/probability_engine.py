class ProbabilityEngine:

    @staticmethod
    def calculate(state):

        probability = 0
        reasons = []

        tech = state.ai
        smc = state.smc

        # Technical score
        if abs(tech["score"]) >= 60:
            probability += 25
            reasons.append("Strong Technical Score")

        # Market structure
        if smc.get("bos"):
            probability += 20
            reasons.append("Break of Structure")

        if smc.get("choch"):
            probability += 15
            reasons.append("Change of Character")

        if smc.get("liquidity_sweep"):
            probability += 15
            reasons.append("Liquidity Sweep")

        if smc.get("trend") != "SIDEWAYS":
            probability += 15
            reasons.append("Trending Market")

        ob = state.orderblock

        if ob.get("bullish"):
            probability += 10
            reasons.append("Bullish Order Block")

        if ob.get("bearish"):
            probability += 10
            reasons.append("Bearish Order Block")

        # Indicator agreement
        if len(tech["reasons"]) >= 5:
            probability += 10
            reasons.append("Indicator Confluence")

        probability = min(100, probability)

        return {
            "probability": probability,
            "reasons": reasons
        }
