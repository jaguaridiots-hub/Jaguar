class MasterConfluence:

    @staticmethod
    def analyze(
        technical,
        smc,
        gann
    ):

        score = 0
        reasons = []

        # ----------------------------
        # Technical Engine
        # ----------------------------
        score += technical["score"]

        reasons.extend(technical["reasons"])

        # ----------------------------
        # Smart Money Engine
        # ----------------------------
        score += smc["score"]

        reasons.extend(smc["reasons"])

        # ----------------------------
        # Gann Engine
        # ----------------------------
        score += gann["score"]

        reasons.extend(gann["reasons"])

        # ----------------------------
        # Normalize score
        # ----------------------------

        if score > 100:
            score = 100

        if score < -100:
            score = -100

        confidence = abs(score)

        # ----------------------------
        # Final Decision
        # ----------------------------

        if score >= 80:

            signal = "STRONG BUY"

        elif score >= 50:

            signal = "BUY"

        elif score >= 20:

            signal = "WATCH"

        elif score > -20:

            signal = "HOLD"

        elif score > -50:

            signal = "SELL"

        else:

            signal = "STRONG SELL"

        return {

            "signal": signal,

            "score": score,

            "confidence": confidence,

            "reasons": reasons

        }
