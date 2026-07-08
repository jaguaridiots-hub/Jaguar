class JaguarBrainV3:

    @staticmethod
    def decide(technical, smc, gann, mtf, risk):

        tech = technical["score"]
        smc_score = smc["score"]
        gann_score = gann["score"]
        mtf_conf = mtf["confidence"]

        weighted = (
            tech * 0.40 +
            smc_score * 0.30 +
            gann_score * 0.20 +
            mtf_conf * 0.10
        )

        confidence = round(min(100, abs(weighted)), 2)

        reasons = []

        if tech > 50:
            reasons.append("Technical Trend Bullish")
        elif tech < -50:
            reasons.append("Technical Trend Bearish")

        if smc_score > 50:
            reasons.append("Institutional Buying")
        elif smc_score < -50:
            reasons.append("Institutional Selling")

        if gann_score > 50:
            reasons.append("Gann Bullish")
        elif gann_score < -50:
            reasons.append("Gann Bearish")

        if mtf["trend"] == "BULLISH":
            reasons.append("Multi Timeframe Bullish")
        elif mtf["trend"] == "BEARISH":
            reasons.append("Multi Timeframe Bearish")

        if weighted >= 70:
            signal = "STRONG BUY"
            grade = "A+"

        elif weighted >= 50:
            signal = "BUY"
            grade = "A"

        elif weighted >= 20:
            signal = "BUY ON RETRACEMENT"
            grade = "B+"

        elif weighted > -20:
            signal = "WAIT"
            grade = "B"

        elif weighted > -50:
            signal = "SELL ON RALLY"
            grade = "B-"

        elif weighted > -70:
            signal = "SELL"
            grade = "C"

        else:
            signal = "STRONG SELL"
            grade = "D"

        return {
            "signal": signal,
            "confidence": confidence,
            "grade": grade,
            "score": round(weighted, 2),
            "reasons": reasons
        }
