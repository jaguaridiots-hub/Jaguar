class TradeValidatorEngine:

    def run(self, state, bus):

        bus.publish("TRADE_VALIDATOR_ANALYSIS")

        brain = getattr(state, "brain", {}) or {}
        probability = getattr(state, "probability", {}) or {}
        decision = getattr(state, "decision", {}) or {}
        mtf = getattr(state, "mtf", {}) or {}
        regime = getattr(state, "regime", {}) or {}
        session = getattr(state, "session", {}) or {}
        orderflow = getattr(state, "orderflow", {}) or {}
        volume = getattr(state, "volume_profile", {}) or {}
        gann = getattr(state, "gann", {}) or {}
        risk = getattr(state, "risk", {}) or {}

        score = 0
        reasons = []

        if brain.get("signal") in ("BUY", "STRONG BUY"):
            score += 15
            reasons.append("AI Bullish")

        if probability.get("score", 0) >= 70:
            score += 15
            reasons.append("High Probability")

        if decision.get("decision") == "ENTER":
            score += 15
            reasons.append("Decision Approved")

        if mtf.get("alignment", 0) >= 4:
            score += 15
            reasons.append("MTF Alignment")

        if regime.get("regime") in ("TREND", "COMPRESSION"):
            score += 10
            reasons.append("Valid Market Regime")

        if session.get("score", 0) >= 5:
            score += 5
            reasons.append("Good Session")

        if orderflow.get("signal") == "BUY":
            score += 10
            reasons.append("Buy Order Flow")

        if volume.get("score", 0) > 0:
            score += 5
            reasons.append("Volume Confirmation")

        if gann.get("signal") != "NEUTRAL":
            score += 5
            reasons.append("Gann Confirmation")

        if risk.get("status") == "SAFE":
            score += 5
            reasons.append("Risk Acceptable")

        score = max(0, min(100, score))

        approved = score >= 60

        state.validator = {
            "approved": approved,
            "signal": "VALID" if approved else "INVALID",
            "score": score,
            "reasons": reasons,
        }

        bus.publish("TRADE_VALIDATOR_READY")

        return state
