class ProbabilityEngineV2:

    def run(self, state, bus):

        bus.publish("PROBABILITY_V2_ANALYSIS")

        score = 0
        reasons = []

        brain = getattr(state, "brain", {}) or {}
        decision = getattr(state, "decision", {}) or {}
        execution = getattr(state, "execution", {}) or {}
        mtf = getattr(state, "mtf", {}) or {}
        orderflow = getattr(state, "orderflow", {}) or {}
        vp = getattr(state, "volume_profile", {}) or {}
        session = getattr(state, "session", {}) or {}
        regime = getattr(state, "regime", {}) or {}
        gann = getattr(state, "gann", {}) or {}

        # -----------------------------
        # Brain
        # -----------------------------
        score += max(0, min(20, brain.get("score", 0) // 5))

        # -----------------------------
        # Decision
        # -----------------------------
        if decision.get("decision") == "ENTER":
            score += 15
            reasons.append("Decision Approved")

        elif decision.get("decision") == "WATCH":
            score += 8
            reasons.append("Decision Watch")

        # -----------------------------
        # Execution
        # -----------------------------
        if execution.get("signal") == "ENTER NOW":
            score += 15
            reasons.append("Execution Ready")

        elif execution.get("signal") == "WAIT CONFIRMATION":
            score += 8
            reasons.append("Execution Waiting")

        # -----------------------------
        # Multi-Timeframe
        # -----------------------------
        alignment = mtf.get("alignment", 0)

        if alignment >= 4:
            score += 15
            reasons.append("Full MTF Alignment")

        elif alignment >= 3:
            score += 10
            reasons.append("Strong MTF Alignment")

        # -----------------------------
        # Order Flow
        # -----------------------------
        if orderflow.get("signal") in ("BUY", "SELL"):
            score += 10
            reasons.append("Order Flow Confirmed")

        # -----------------------------
        # Volume Profile
        # -----------------------------
        score += max(0, min(10, vp.get("score", 0)))

        # -----------------------------
        # Session
        # -----------------------------
        if session.get("score", 0) >= 20:
            score += 5
            reasons.append("High Liquidity Session")

        # -----------------------------
        # Regime
        # -----------------------------
        if regime.get("regime") == "TREND":
            score += 5
            reasons.append("Trending Market")

        # -----------------------------
        # Gann
        # -----------------------------
        if gann.get("signal") != "NEUTRAL":
            score += 5
            reasons.append("Gann Confirmation")

        # Clamp
        score = max(0, min(100, score))

        # Confidence
        if score >= 90:
            confidence = "VERY HIGH"
            grade = "A+"
            quality = "★★★★★"

        elif score >= 80:
            confidence = "HIGH"
            grade = "A"
            quality = "★★★★☆"

        elif score >= 65:
            confidence = "GOOD"
            grade = "B"
            quality = "★★★☆☆"

        elif score >= 50:
            confidence = "MODERATE"
            grade = "C"
            quality = "★★☆☆☆"

        else:
            confidence = "LOW"
            grade = "D"
            quality = "★☆☆☆☆"

        state.probability = {
            "signal": confidence,
            "score": score,
            "confidence": confidence,
            "grade": grade,
            "quality": quality,
            "reasons": reasons,
        }

        bus.publish("PROBABILITY_V2_READY")

        return state
