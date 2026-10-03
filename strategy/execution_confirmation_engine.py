from config.decision_config import *


class ExecutionConfirmationEngine:

    def run(self, state, bus):

        bus.publish("EXECUTION_CONFIRMATION_ANALYSIS")

        brain = getattr(state, "brain", {}) or {}
        decision = getattr(state, "decision", {}) or {}
        probability = getattr(state, "probability", {}) or {}
        orderflow = getattr(state, "orderflow", {}) or {}
        mtf = getattr(state, "mtf", {}) or {}
        structure = getattr(state, "market_structure", {}) or {}
        session = getattr(state, "session", {}) or {}
        vp = getattr(state, "volume_profile", {}) or {}
        gann = getattr(state, "gann", {}) or {}
        risk = getattr(state, "risk", {}) or {}
        execution_trigger = getattr(state, "execution_trigger", {}) or {}

        score = 0
        reasons = []

        # AI Brain
        if brain.get("signal") in ("STRONG BUY", "STRONG SELL"):
            score += 20
            reasons.append("Strong AI Signal")
        elif brain.get("signal") in ("BUY", "SELL"):
            score += 15
            reasons.append("AI Signal")

        # Probability
        if probability.get("score", 0) >= 75:
            score += 10
            reasons.append("High Probability")

        # Execution Trigger
        if execution_trigger.get("confirmed", False):
            score += 25
            reasons.append("Execution Trigger Confirmed")

        elif execution_trigger.get("signal") == "BUY":
            score += 15
            reasons.append("Execution Trigger")

        # Decision
        if decision.get("decision") == "ENTER":
            score += 15
            reasons.append("Decision Confirmed")
        elif decision.get("decision") == "WATCH":
            score += 5
            reasons.append("Watchlist Setup")

        # Order Flow
        if orderflow.get("signal") in ("BUY", "SELL"):
            score += 10
            reasons.append("Order Flow")

        # Multi Timeframe
        alignment = mtf.get("alignment", 0)

        if alignment >= 4:
            score += 15
            reasons.append("Full MTF Alignment")
        elif alignment >= 2:
            score += 10
            reasons.append("Partial MTF Alignment")
        elif alignment >= 1:
            score += 5
            reasons.append("Weak MTF Alignment")

        # Market Structure
        if structure.get("score", 0) > 0:
            score += 10
            reasons.append("Bullish Structure")

        # Volume Profile
        if vp.get("score", 0) > 0:
            score += 5
            reasons.append("Volume Profile")

        # Session
        if session.get("score", 0) >= 5:
            score += 5
            reasons.append("Active Session")

        # Gann
        if gann.get("signal") in ("BUY", "BULLISH"):
            score += 5
            reasons.append("Gann Confirmation")

        # Risk
        if risk.get("status") == "SAFE":
            score += 5
            reasons.append("Risk Approved")

        score = max(0, min(MAX_SCORE, score))

        if score >= EXECUTION_CONFIRMATION_THRESHOLD:
            signal = "ENTER NOW"
            confirmed = True

        elif score >= WAIT_CONFIRMATION_THRESHOLD:
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
