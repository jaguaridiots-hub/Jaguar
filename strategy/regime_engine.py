class RegimeEngine:

    def run(self, state, bus):

        bus.publish("REGIME_ANALYSIS")

        tech = state.ai

        adx = tech.get("adx", 20)
        atr = tech.get("atr", 0)
        bb_width = tech.get("bb_width", 0)

        regime = "RANGE"
        score = 0
        reasons = []

        if adx >= 30:
            regime = "TREND"
            score += 20
            reasons.append("Strong Trend")

        elif adx <= 20:
            regime = "RANGE"
            reasons.append("Range Market")

        if bb_width > 0.03:
            regime = "BREAKOUT"
            score += 10
            reasons.append("Volatility Expansion")

        elif bb_width < 0.01:
            regime = "COMPRESSION"
            reasons.append("Low Volatility")

        state.regime = {
            "regime": regime,
            "score": score,
            "atr": atr,
            "adx": adx,
            "bb_width": bb_width,
            "reasons": reasons,
        }

        bus.publish("REGIME_READY")

        return state
