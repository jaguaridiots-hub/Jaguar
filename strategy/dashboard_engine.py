class DashboardEngine:

    def run(self, state, bus):

        bus.publish("DASHBOARD_ANALYSIS")

        state.dashboard = {

            "symbol": state.symbol,
            "interval": state.interval,

            "signal": state.brain.get("signal"),
            "score": state.brain.get("score"),
            "confidence": state.brain.get("confidence"),
            "grade": state.brain.get("grade"),

            "entry": state.trade_plan.get("entry"),
            "stop": state.trade_plan.get("stop"),
            "tp1": state.trade_plan.get("tp1"),
            "tp2": state.trade_plan.get("tp2"),

            "risk_status": state.risk.get("status"),
            "position_size": state.risk.get("position_size"),
            "exposure": state.risk.get("exposure"),

            "session": state.session.get("session"),
            "mtf_bias": state.mtf.get("bias"),

            "market_regime": state.regime.get("regime"),
            "regime_score": state.regime.get("score"),

            "orderflow_signal": state.orderflow.get("signal"),
            "orderflow_delta": state.orderflow.get("delta"),

            "decision": state.decision.get("decision"),
            "decision_score": state.decision.get("score"),

            "execution_signal": state.execution.get("signal"),
            "execution_score": state.execution.get("score"),
            "execution_reasons": state.execution.get("reasons"),

            "poc": state.volume_profile.get("poc"),
            "vah": state.volume_profile.get("vah"),
            "val": state.volume_profile.get("val"),

            "gann_support": state.gann.get("support"),
            "gann_resistance": state.gann.get("resistance"),
            "gann_level": state.gann.get("nearest_level"),
        }

        bus.publish("DASHBOARD_READY")

        return state
