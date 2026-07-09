class DashboardEngine:

    def run(self, state, bus):

        bus.publish("DASHBOARD_ANALYSIS")

        brain = getattr(state, "brain", {}) or {}
        probability = getattr(state, "probability", {}) or {}
        trade_plan = getattr(state, "trade_plan", {}) or {}
        risk = getattr(state, "risk", {}) or {}
        session = getattr(state, "session", {}) or {}
        mtf = getattr(state, "mtf", {}) or {}
        regime = getattr(state, "regime", {}) or {}
        orderflow = getattr(state, "orderflow", {}) or {}
        decision = getattr(state, "decision", {}) or {}
        execution = getattr(state, "execution", {}) or {}
        volume_profile = getattr(state, "volume_profile", {}) or {}
        gann = getattr(state, "gann", {}) or {}

        state.dashboard = {

            "symbol": state.symbol,
            "interval": state.interval,

            # AI
            "signal": brain.get("signal"),
            "score": brain.get("score"),

            # Probability V2
            "probability": probability.get("score"),
            "confidence": probability.get("confidence"),
            "institution_grade": probability.get("grade"),
            "trade_quality": probability.get("quality"),

            # Trade Plan
            "entry": trade_plan.get("entry"),
            "stop": trade_plan.get("stop"),
            "tp1": trade_plan.get("tp1"),
            "tp2": trade_plan.get("tp2"),

            # Risk
            "risk_status": risk.get("status"),
            "position_size": risk.get("position_size"),
            "exposure": risk.get("exposure"),

            # Session
            "session": session.get("session"),

            # Multi Timeframe
            "mtf_bias": mtf.get("bias"),

            # Regime
            "market_regime": regime.get("regime"),
            "regime_score": regime.get("score"),

            # Orderflow
            "orderflow_signal": orderflow.get("signal"),
            "orderflow_delta": orderflow.get("delta"),

            # Decision
            "decision": decision.get("decision"),
            "decision_score": decision.get("score"),

            # Execution
            "execution_signal": execution.get("signal"),
            "execution_score": execution.get("score"),
            "execution_reasons": execution.get("reasons"),

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
