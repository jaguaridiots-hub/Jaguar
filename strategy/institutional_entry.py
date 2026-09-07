class InstitutionalEntry:

    @staticmethod
    def analyze(regime, structure, orderblock, fvg, liquidity, zone):

        score = 0
        reasons = []

        # Market regime
        if regime["regime"] == "TRENDING_BULLISH":
            score += 20
            reasons.append("Bullish Market Regime")

        # Market structure
        if structure["trend"] == "BULLISH":
            score += 20
            reasons.append("Bullish Structure")

        if structure["bos"]:
            score += 15
            reasons.append("Break of Structure")

        # Order Block
        if orderblock["type"] == "BULLISH":
            score += 15
            reasons.append("Bullish Order Block")

        # Fair Value Gap
        if fvg["found"] and fvg["type"] == "BULLISH":
            score += 15
            reasons.append("Bullish FVG")

        # Liquidity
        if liquidity["found"] and liquidity["type"] == "SELL_SIDE_SWEEP":
            score += 10
            reasons.append("Sell-side Liquidity Sweep")

        # Premium / Discount
        if zone["zone"] == "DISCOUNT":
            score += 10
            reasons.append("Discount Zone")

        if score >= 70:
            signal = "HIGH PROBABILITY BUY"
        elif score >= 40:
            signal = "BUY SETUP"
        else:
            signal = "WAIT"

        return {
            "signal": signal,
            "score": score,
            "reasons": reasons
        }
