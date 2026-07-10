class MasterDecisionEngine:

    def run(self, state, bus):

        bus.publish("MASTER_DECISION_ANALYSIS")

        brain = getattr(state, "brain", {}) or {}
        probability = getattr(state, "probability", {}) or {}
        validator = getattr(state, "trade_validator", {}) or {}
        execution = getattr(state, "execution_confirmation", {}) or {}
        decision = getattr(state, "decision", {}) or {}
        risk = getattr(state, "risk", {}) or {}
        orderflow = getattr(state, "orderflow", {}) or {}

        final = "WAIT"
        reasons = []

        if not validator.get("approved", False):
            final = "REJECT"
            reasons.append("Trade Validator rejected trade")

        elif execution.get("signal") != "ENTER NOW":
            final = "WAIT"
            reasons.append("Execution Confirmation Pending")

        elif probability.get("score", 0) < 70:
            final = "WAIT"
            reasons.append("Probability too low")

        elif risk.get("status") == "HIGH RISK":
            final = "WAIT"
            reasons.append("Risk too high")

        elif orderflow.get("signal") == "SELL" and brain.get("signal") == "STRONG BUY":
            final = "WAIT"
            reasons.append("Order Flow conflict")

        elif decision.get("decision") == "ENTER":

            if brain.get("signal") in ("BUY", "STRONG BUY"):
                final = "ENTER LONG"

            elif brain.get("signal") in ("SELL", "STRONG SELL"):
                final = "ENTER SHORT"

            else:
                final = "WAIT"

        state.master_decision = {
            "decision": final,
            "confidence": probability.get("confidence"),
            "score": probability.get("score"),
            "approved": validator.get("approved"),
            "reasons": reasons
        }

        bus.publish("MASTER_DECISION_READY")

        return state
