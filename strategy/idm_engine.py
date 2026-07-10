class InstitutionalDecisionMatrix:

    @staticmethod
    def evaluate(state):

        score = 0
        reasons = []

        # ==========================================
        # AI Brain
        # ==========================================
        brain = getattr(state, "brain", {}) or {}

        if brain.get("signal") == "STRONG BUY":
            score += 30
            reasons.append("AI Strong Buy")

        elif brain.get("signal") == "BUY":
            score += 15
            reasons.append("AI Buy")

        elif brain.get("signal") == "STRONG SELL":
            score -= 30
            reasons.append("AI Strong Sell")

        elif brain.get("signal") == "SELL":
            score -= 15
            reasons.append("AI Sell")

        # ==========================================
        # Multi Time Frame
        # ==========================================
        mtf = getattr(state, "mtf", {}) or {}

        if mtf.get("bias") == "BULLISH":
            score += 20
            reasons.append("Bullish MTF")

        elif mtf.get("bias") == "BEARISH":
            score -= 20
            reasons.append("Bearish MTF")

        alignment = mtf.get("alignment", 0)

        if alignment >= 4:
            score += 10
            reasons.append("Full MTF Alignment")

        elif alignment >= 3:
            score += 5
            reasons.append("Strong MTF Alignment")

        # ==========================================
        # Confluence
        # ==========================================
        confluence = getattr(state, "confluence", {}) or {}

        score += confluence.get("score", 0)

        if confluence.get("score", 0):
            reasons.append("Confluence")

        # ==========================================
        # Order Flow
        # ==========================================
        orderflow = getattr(state, "orderflow", {}) or {}

        score += orderflow.get("score", 0)

        if orderflow.get("signal") == "BUY":
            reasons.append("Bullish Order Flow")

        elif orderflow.get("signal") == "SELL":
            reasons.append("Bearish Order Flow")

        # ==========================================
        # Session
        # ==========================================
        session = getattr(state, "session", {}) or {}

        score += session.get("score", 0)

        # ==========================================
        # Volume Profile
        # ==========================================
        vp = getattr(state, "volume_profile", {}) or {}

        score += vp.get("score", 0)

        # ==========================================
        # Market Regime
        # ==========================================
        regime = getattr(state, "regime", {}) or {}

        score += regime.get("score", 0)

        # ==========================================
        # Gann
        # ==========================================
        gann = getattr(state, "gann", {}) or {}

        score += gann.get("score", 0)

        # ==========================================
        # Risk
        # ==========================================
        risk = getattr(state, "risk", {}) or {}

        if risk.get("status") == "SAFE":
            score += 10
            reasons.append("Risk Safe")

        elif risk.get("status") == "HIGH RISK":
            score -= 20
            reasons.append("High Risk")

        # ==========================================
        # Clamp Score
        # ==========================================
        score = max(-100, min(100, score))

        # ==========================================
        # Institutional Decision
        # ==========================================

        if (
            score >= 70
            and brain.get("signal") in ("BUY", "STRONG BUY")
            and risk.get("status") == "SAFE"
            and alignment >= 3
        ):

            decision = "ENTER"

        elif (
            score <= -70
            and brain.get("signal") in ("SELL", "STRONG SELL")
            and risk.get("status") == "SAFE"
            and alignment >= 3
        ):

            decision = "SHORT"

        elif score >= 40:

            decision = "WATCH"

        else:

            decision = "WAIT"

        state.idm = {
            "decision": decision,
            "score": score,
            "approved": decision in ("ENTER", "SHORT"),
            "reasons": reasons,
        }

        return state
