class ExecutionConfirmationEngine:

    def run(self, state, bus):

        bus.publish("EXECUTION_CONFIRMATION_ANALYSIS")

        brain = getattr(state, "brain", {}) or {}
        decision = getattr(state, "decision", {}) or {}
        orderflow = getattr(state, "orderflow", {}) or {}
        mtf = getattr(state, "mtf", {}) or {}
        session = getattr(state, "session", {}) or {}
        vp = getattr(state, "volume_profile", {}) or {}
        risk = getattr(state, "risk", {}) or {}

        score = 0
        reasons = []

        if brain.get("signal") in ("BUY", "STRONG BUY"):
            score += 20
            reasons.append("AI Confirmation")

        if decision.get("decision") == "ENTER":
            score += 20
            reasons.append("Decision Confirmed")

        if orderflow.get("signal") in ("BUY", "SELL"):
            score += 15
            reasons.append("Order Flow Confirmed")

        if mtf.get("alignment", 0) >= 4:
            score += 15
            reasons.append("MTF Alignment")

        if vp.get("score", 0) > 0:
            score += 10
            reasons.append("Volume Confirmation")

        if session.get("score", 0) >= 5:
            score += 10
            reasons.append("Active Session")

        if risk.get("status") == "SAFE":
            score += 10
            reasons.append("Risk Safe")

        score = max(0, min(100, score))

        if score >= 75:
            signal = "ENTER NOW"
            confirmed = True

        elif score >= 55:
            signal = "WAIT CONFIRMATION"
            confirmed = False

        else:
            signal = "NO ENTRY"
            confirmed = False

        state.execution_confirmation = {
            "signal": signal,
            "score": score,
            "confirmed": confirmed,
            "reasons": reasons,
        }

        bus.publish("EXECUTION_CONFIRMATION_READY")

        return state
