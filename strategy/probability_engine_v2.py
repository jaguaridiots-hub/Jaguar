class ProbabilityEngineV2:

    def run(self, state, bus):

        bus.publish("PROBABILITY_V2_ANALYSIS")

        brain = getattr(state, "brain", {}) or {}
        mtf = getattr(state, "mtf", {}) or {}
        decision = getattr(state, "decision", {}) or {}
        risk = getattr(state, "risk", {}) or {}
        orderflow = getattr(state, "orderflow", {}) or {}
        session = getattr(state, "session", {}) or {}
        gann = getattr(state, "gann", {}) or {}

        score = 0
        reasons = []

        # AI
        if brain.get("signal") == "STRONG BUY":
            score += 30
            reasons.append("Strong Buy")

        elif brain.get("signal") == "BUY":
            score += 20
            reasons.append("Buy")

        elif brain.get("signal") == "STRONG SELL":
            score += 30
            reasons.append("Strong Sell")

        elif brain.get("signal") == "SELL":
            score += 20
            reasons.append("Sell")

        # Multi Time Frame
        alignment = mtf.get("alignment", 0)

        if alignment >= 4:
            score += 20
            reasons.append("Full MTF")

        elif alignment >= 3:
            score += 15
            reasons.append("Strong MTF")

        elif alignment >= 2:
            score += 10

        # Decision
        if decision.get("decision") == "ENTER":
            score += 10
            reasons.append("Decision")

        # Order Flow
        if orderflow.get("signal") in ("BUY", "SELL"):
            score += 10
            reasons.append("Order Flow")

        # Session
        if session.get("score", 0) >= 5:
            score += 5

        # Gann
        if gann.get("signal") != "NEUTRAL":
            score += 5

        # Risk
        if risk.get("status") == "SAFE":
            score += 20
            reasons.append("Risk Safe")

        score = max(0, min(100, score))

        if score >= 90:
            confidence = "VERY HIGH"
            grade = "A+"
        elif score >= 80:
            confidence = "HIGH"
            grade = "A"
        elif score >= 70:
            confidence = "GOOD"
            grade = "B"
        elif score >= 60:
            confidence = "MODERATE"
            grade = "C"
        elif score >= 50:
            confidence = "LOW"
            grade = "D"
        else:
            confidence = "VERY LOW"
            grade = "F"

        state.probability = {
            "score": score,
            "confidence": confidence,
            "grade": grade,
            "reasons": reasons,
        }

        bus.publish("PROBABILITY_V2_READY")

        return state
