class ProbabilityEngineV2:

    @staticmethod
    def analyze(state):

        mtf = getattr(state, "mtf", {}) or {}
        decision = getattr(state, "decision", {}) or {}
        risk = getattr(state, "risk", {}) or {}
        orderflow = getattr(state, "orderflow", {}) or {}
        session = getattr(state, "session", {}) or {}
        gann = getattr(state, "gann", {}) or {}
        smc = getattr(state, "smc", {}) or {}
        bos = getattr(state, "bos", {}) or {}
        choch = getattr(state, "choch", {}) or {}
        liquidity = getattr(state, "liquidity", {}) or {}
        orderblock = getattr(state, "orderblock", {}) or {}
        fvg = getattr(state, "fvg", {}) or {}
        premium_discount = getattr(state, "premium_discount", {}) or {}
        wyckoff = getattr(state, "wyckoff", {}) or {}
        equal_levels = getattr(state, "equal_levels", {}) or {}
        volume_profile = getattr(state, "volume_profile", {}) or {}
        market_regime = getattr(state, "market_regime", {}) or {}

        score = 0
        reasons = []

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
        print("Decision :", decision)
        print("MTF :", mtf)
        print("Risk :", risk)

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

        return state
