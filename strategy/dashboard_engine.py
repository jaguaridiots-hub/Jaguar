class DashboardEngine:

    def run(self, state, bus):

        bus.publish("DASHBOARD_ANALYSIS")

        brain = getattr(state, "brain", {}) or {}
        master = getattr(state, "master_decision", {}) or {}
        probability = getattr(state, "probability", {}) or {}
        trade_plan = getattr(state, "trade_plan", {}) or {}
        risk = getattr(state, "risk", {}) or {}
        session = getattr(state, "session", {}) or {}
        mtf = getattr(state, "mtf", {}) or {}
        regime = getattr(state, "regime", {}) or {}
        orderflow = getattr(state, "orderflow", {}) or {}
        decision = getattr(state, "decision", {}) or {}
        execution = getattr(state, "execution", {}) or {}
        validator = getattr(state, "trade_validator", {}) or {}
        execution_confirmation = getattr(state, "execution_confirmation", {}) or {}
        volume_profile = getattr(state, "volume_profile", {}) or {}
        gann = getattr(state, "gann", {}) or {}

        state.dashboard = {

            # General
            "symbol": getattr(state, "symbol", ""),
            "interval": getattr(state, "interval", ""),

            # AI Brain
            "signal": brain.get("signal", "NONE"),
            "score": brain.get("score", 0),

            # Probability
            "probability": probability.get("score", 0),
            "confidence": probability.get("confidence", "LOW"),
            "institution_grade": probability.get("grade", "D"),
            "trade_quality": probability.get("quality", "★"),

            # Trade Plan
            "entry": trade_plan.get("entry"),
            "stop": trade_plan.get("stop"),
            "tp1": trade_plan.get("tp1"),
            "tp2": trade_plan.get("tp2"),

            # Risk
            "risk_status": risk.get("status", "UNKNOWN"),
            "position_size": risk.get("position_size", 0),
            "exposure": risk.get("exposure", 0),

            # Session
            "session": session.get("session", "UNKNOWN"),

            # Multi Timeframe
            "mtf_bias": mtf.get("bias", "NEUTRAL"),

            # Regime
            "market_regime": regime.get("regime", "UNKNOWN"),
            "regime_score": regime.get("score", 0),

            # Order Flow
            "orderflow_signal": orderflow.get("signal", "NONE"),
            "orderflow_delta": orderflow.get("delta", 0),

            # Decision
            "decision": decision.get("decision", "WAIT"),
            "decision_score": decision.get("score", 0),

            # Execution
            "execution_signal": execution.get("signal", "NO ENTRY"),
            "execution_score": execution.get("score", 0),
            "execution_reasons": execution.get("reasons", []),

            # Execution Confirmation
            "execution_confirmation": execution_confirmation.get("signal", "NO ENTRY"),
            "execution_confirmation_score": execution_confirmation.get("score", 0),
            "execution_confirmed": execution_confirmation.get("confirmed", False),

            # Trade Validator
            "validator_signal": validator.get("signal", "INVALID"),
            "validator_score": validator.get("score", 0),
            "validator_approved": validator.get("approved", False),

            # Master Decision
            "final_decision": master.get("decision", "WAIT"),
            "trade_approved": master.get("approved", False),
            "master_score": master.get("score", 0),

            # Volume Profile
            "poc": volume_profile.get("poc"),
            "vah": volume_profile.get("vah"),
            "val": volume_profile.get("val"),

            # Gann
            "gann_support": gann.get("support"),
            "gann_resistance": gann.get("resistance"),
            "gann_level": gann.get("nearest_level"),
        }

        bus.publish("DASHBOARD_READY")

        return state
