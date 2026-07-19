from config.decision_config import *


class MasterDecisionEngine:

    def run(self, state, bus):

        bus.publish("MASTER_DECISION_ANALYSIS")

        brain = getattr(state, "brain", {}) or {}
        probability = getattr(state, "probability", {}) or {}
        validator = getattr(state, "trade_validator", {}) or {}
        decision = getattr(state, "decision", {}) or {}
        risk = getattr(state, "risk", {}) or {}
        orderflow = getattr(state, "orderflow", {}) or {}

        final = "WAIT"
        reasons = []

        # --------------------------------------------------
        # Trade Validator
        # --------------------------------------------------

        if not validator.get("approved", False):
            final = "REJECT"
            reasons.append("Trade Validator rejected trade")

        # --------------------------------------------------
        # Probability
        # --------------------------------------------------

        elif probability.get("score", 0) < MIN_PROBABILITY:
            final = "WAIT"
            reasons.append("Probability too low")

        # --------------------------------------------------
        # Risk
        # --------------------------------------------------

        elif risk.get("status") == "HIGH RISK":
            final = "WAIT"
            reasons.append("Risk too high")

        # --------------------------------------------------
        # Order Flow Conflict
        # --------------------------------------------------

        elif (
            orderflow.get("signal") == "SELL"
            and brain.get("signal") in ("BUY", "STRONG BUY")
        ):
            final = "WAIT"
            reasons.append("Order Flow conflict")

        elif (
            orderflow.get("signal") == "BUY"
            and brain.get("signal") in ("SELL", "STRONG SELL")
        ):
            final = "WAIT"
            reasons.append("Order Flow conflict")

        # --------------------------------------------------
        # Legacy Decision Engine
        # --------------------------------------------------

        elif decision.get("decision") == "ENTER":

            if brain.get("signal") in ("BUY", "STRONG BUY"):
                final = "ENTER LONG"
                reasons.append("Bullish institutional alignment")

            elif brain.get("signal") in ("SELL", "STRONG SELL"):
                final = "ENTER SHORT"
                reasons.append("Bearish institutional alignment")

            else:
                final = "WAIT"
                reasons.append("Brain signal not aligned")

        else:
            reasons.append("Decision engine waiting")

        # --------------------------------------------------
        # Output
        # --------------------------------------------------

        state.master_decision = {
            "decision": final,
            "confidence": probability.get("confidence", 0),
            "score": probability.get("score", 0),
            "approved": validator.get("approved", False),
            "reasons": reasons,
        }

        bus.publish("MASTER_DECISION_READY")

        return state
