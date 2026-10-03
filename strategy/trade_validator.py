class TradeValidator:

    @staticmethod
    def validate(state):

        confirmation = getattr(state, "execution_confirmation", {}) or {}
        risk = getattr(state, "risk", {}) or {}
        mtf = getattr(state, "mtf", {}) or {}
        orderflow = getattr(state, "orderflow", {}) or {}

        score = 0
        reasons = []

        # -----------------------------------
        # Execution Confirmation
        # -----------------------------------
        if confirmation.get("confirmed", False):
            score += 30
            reasons.append("Execution Confirmed")

        elif confirmation.get("signal") == "WAIT CONFIRMATION":
            score += 15
            reasons.append("Waiting Confirmation")

        # -----------------------------------
        # Risk
        # -----------------------------------
        if risk.get("status") == "SAFE":
            score += 20
            reasons.append("Risk Safe")

        # -----------------------------------
        # Multi-Timeframe
        # -----------------------------------
        if mtf.get("alignment", 0) >= 4:
            score += 20
            reasons.append("Full MTF Alignment")

        elif mtf.get("alignment", 0) >= 3:
            score += 10
            reasons.append("Strong MTF Alignment")

        # -----------------------------------
        # Order Flow
        # -----------------------------------
        if orderflow.get("signal") in ("BUY", "SELL"):
            score += 10
            reasons.append("Order Flow Confirmed")

        # -----------------------------------
        # Final Score
        # -----------------------------------
        score = max(0, min(100, score))

        approved = score >= 50

        state.trade_validator = {
            "approved": approved,
            "signal": "VALID" if approved else "INVALID",
            "score": score,
            "reasons": reasons
        }

        return state
