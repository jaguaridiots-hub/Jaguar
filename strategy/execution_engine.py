class ExecutionEngine:

    def run(self, state, bus):

        bus.publish("EXECUTION_ANALYSIS")

        # -------------------------------------------------
        # Read Enterprise Decision Chain
        # -------------------------------------------------
        idm = getattr(state, "idm", {}) or {}
        trade_plan = getattr(state, "trade_plan", {}) or {}
        validator = getattr(state, "trade_validator", {}) or {}
        confirmation = getattr(state, "execution_confirmation", {}) or {}

        reasons = []

        # -------------------------------------------------
        # Gate 1 : Institutional Decision
        # -------------------------------------------------
        if not idm.get("approved", False):
            state.execution = {
                "signal": "NO ENTRY",
                "status": "BLOCKED",
                "reasons": ["Institutional Decision Matrix rejected"]
            }
            bus.publish("EXECUTION_BLOCKED")
            return state

        reasons.append("IDM Approved")

        # ------------------------------------------------
        # Gate 2 : Trade Plan
        # ------------------------------------------------
        if trade_plan.get("signal") not in (
            "ENTER",
            "BUY",
            "STRONG BUY",
        ):
            state.execution = {
                "signal": "WAIT",
                "status": "PENDING",
                "reasons": reasons + ["Trade plan not ready"]
            }
            bus.publish("EXECUTION_PENDING")
            return state

        reasons.append("Trade Plan Ready")

        # -------------------------------------------------
        # Gate 3 : Validator
        # -------------------------------------------------
        if not validator.get("approved", False):
            state.execution = {
                "signal": "WAIT",
                "status": "PENDING",
                "reasons": reasons + ["Trade Validator rejected"]
            }
            bus.publish("EXECUTION_PENDING")
            return state

        reasons.append("Trade Validated")

        # -------------------------------------------------
        # Gate 4 : Execution Confirmation
        # -------------------------------------------------
        if not confirmation.get("confirmed", False):
            state.execution = {
                "signal": "WAIT CONFIRMATION",
                "status": "PENDING",
                "reasons": reasons + ["Waiting for execution confirmation"]
            }
            bus.publish("EXECUTION_WAIT")
            return state

        reasons.append("Execution Confirmed")

        # -------------------------------------------------
        # Final Execution
        # -------------------------------------------------
        state.execution = {
            "signal": "ENTER NOW",
            "status": "APPROVED",
            "score": 100,
            "reasons": reasons
        }

        bus.publish("EXECUTION_READY")

        return state
