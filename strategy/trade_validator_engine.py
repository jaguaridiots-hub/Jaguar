from config.decision_config import *

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

        # AI Brain
        if brain.get("signal") in ("BUY", "STRONG BUY"):
            score += 15
            reasons.append("AI Bullish")

        # Probability
        if probability.get("score", 0) >= MIN_PROBABILITY:
            score += 15
            reasons.append("High Probability")

        # Decision
        if decision.get("decision") == "ENTER":
            score += 15
            reasons.append("Decision Approved")

        # Multi-Timeframe
        if mtf.get("alignment", 0) >= MIN_MTF_ALIGNMENT:
            score += 15
            reasons.append("MTF Alignment")

        # Market Regime
        if regime.get("regime") in ("TREND", "COMPRESSION"):
            score += 10
            reasons.append("Valid Market Regime")

        # Session
        if session.get("score", 0) >= 5:
            score += 5
            reasons.append("Good Session")

        # Order Flow
        if orderflow.get("signal") in ("BUY", "SELL"):
            score += 10
            reasons.append("Order Flow Confirmed")

        # Volume Profile
        if volume.get("score", 0) > 0:
            score += 5
            reasons.append("Volume Confirmation")

        # Gann
        if gann.get("signal") != "NEUTRAL":
            score += 5
            reasons.append("Gann Confirmation")

        # Risk
        if risk.get("status") == "SAFE":
            score += 5
            reasons.append("Risk Acceptable")

        # Final Score
        score = max(0, min(100, score))
        approved = score >= TRADE_VALIDATOR_THRESHOLD

        state.trade_validator = {
            "approved": approved,
            "signal": "VALID" if approved else "INVALID",
            "score": score,
            "reasons": reasons,
        }

        print("\n========== TRADE VALIDATOR ==========")
        print(state.trade_validator)

        bus.publish("TRADE_VALIDATOR_READY")

        return state
