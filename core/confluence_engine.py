class ConfluenceEngine:

    @staticmethod
    def evaluate(state):

        score = 0
        reasons = []

        # ---------------- AI ----------------
        brain = getattr(state, "brain", {})

        if brain.get("signal") == "STRONG BUY":
            score += 25
            reasons.append("AI Strong Buy")

        elif brain.get("signal") == "BUY":
            score += 15
            reasons.append("AI Buy")

        elif brain.get("signal") == "STRONG SELL":
            score -= 25
            reasons.append("AI Strong Sell")

        elif brain.get("signal") == "SELL":
            score -= 15
            reasons.append("AI Sell")

        # ---------------- Multi Timeframe ----------------
        mtf = getattr(state, "mtf", {})

        if mtf.get("bias") == "BULLISH":
            score += 20
            reasons.append("Bullish Multi-Timeframe")

        elif mtf.get("bias") == "BEARISH":
            score -= 20
            reasons.append("Bearish Multi-Timeframe")

        # ---------------- Order Flow ----------------
        orderflow = getattr(state, "orderflow", {})

        if orderflow.get("signal") == "BUY":
            score += 10
            reasons.append("Buy Order Flow")

        elif orderflow.get("signal") == "SELL":
            score -= 10
            reasons.append("Sell Order Flow")

        # ---------------- Volume Profile ----------------
        vp = getattr(state, "volume_profile", {})

        score += vp.get("score", 0)

        # ---------------- Session ----------------
        session = getattr(state, "session", {})

        score += session.get("score", 0)

        # ---------------- Regime ----------------
        regime = getattr(state, "regime", {})

        score += regime.get("score", 0)

        # ---------------- Probability ----------------
        probability = getattr(state, "probability", {})

        score += probability.get("score", 0)

        # ---------------- Risk ----------------
        risk = getattr(state, "risk", {})

        if risk.get("status") == "SAFE":
            score += 5
            reasons.append("Risk Safe")

        elif risk.get("status") == "DANGEROUS":
            score -= 20
            reasons.append("Risk Dangerous")

        # Clamp score
        score = max(-100, min(100, score))

        # Grade
        if score >= 95:
            grade = "A+"
            quality = "ELITE"

        elif score >= 90:
            grade = "A"
            quality = "HIGH"

        elif score >= 80:
            grade = "B"
            quality = "GOOD"

        elif score >= 70:
            grade = "C"
            quality = "AVERAGE"

        elif score >= 60:
            grade = "WATCH"
            quality = "WATCH"

        else:
            grade = "REJECT"
            quality = "AVOID"

        confidence = abs(score)

        if score >= 80:
            decision = "ENTER"

        elif score >= 60:
            decision = "WATCH"

        elif score <= -80:
            decision = "SHORT"

        else:
            decision = "WAIT"

        state.confluence = {
            "institutional_score": score,
            "grade": grade,
            "trade_quality": quality,
            "decision": decision,
            "confidence": confidence,
            "reasons": reasons,
        }

        return state
