# strategy/dashboard_engine.py
from pprint import pprint

class DashboardEngine:

    def run(self, state, bus):
        bus.publish("DASHBOARD_ANALYSIS")

        # ---- Read canonical state ----
        master = getattr(state, "master_decision", {}) or {}
        trade_plan = getattr(state, "trade_plan", {}) or {}
        risk = getattr(state, "risk", {}) or {}
        execution = getattr(state, "execution_result", {}) or {}
        validator = getattr(state, "trade_validator", {}) or {}
        ai_brain = getattr(state, "ai_brain", {}) or {}
        probability = getattr(state, "probability", {}) or {}
        execution_trigger = getattr(state, "execution_trigger", {}) or {}
        execution_confirmation = getattr(state, "execution_confirmation", {}) or {}

        # Context / diagnostics
        session = getattr(state, "session", {}) or {}
        mtf = getattr(state, "mtf", {}) or {}
        regime = getattr(state, "regime", {}) or {}
        orderflow = getattr(state, "orderflow", {}) or {}
        volume_profile = getattr(state, "volume_profile", {}) or {}
        gann = getattr(state, "gann", {}) or {}
        smc = getattr(state, "smc", {}) or {}
        structure = getattr(state, "structure", {}) or {}
        liquidity = getattr(state, "liquidity", {}) or {}
        fvg = getattr(state, "fvg", {}) or {}
        premium_discount = getattr(state, "premium_discount", {}) or {}
        wyckoff = getattr(state, "wyckoff", {}) or {}
        equal_levels = getattr(state, "equal_levels", {}) or {}

        # ---- Build presentation model ----
        state.dashboard = {
            "symbol": getattr(state, "symbol", ""),
            "timeframe": getattr(state, "interval", ""),
            "price": getattr(state, "price", 0),
            "session": session.get("session", "UNKNOWN"),
            "market_regime": regime.get("regime", "UNKNOWN"),

            "brain_signal": ai_brain.get("signal", "NONE"),
            "brain_score": ai_brain.get("score", 0),
            "probability": probability.get("score", 0),
            "probability_confidence": probability.get("confidence", "LOW"),

            "decision": master.get("decision", "WAIT"),
            "decision_score": master.get("score", 0),
            "decision_grade": master.get("grade", "F"),
            "decision_confidence": master.get("confidence", 0),
            "trade_approved": master.get("approved", False),
            "decision_reasons": master.get("reasoning", []),

            "entry": trade_plan.get("entry"),
            "stop": trade_plan.get("stop"),
            "tp1": trade_plan.get("tp1"),
            "tp2": trade_plan.get("tp2"),
            "risk_reward": trade_plan.get("risk_reward", 0),

            "risk_status": risk.get("status", "NO TRADE"),
            "position_size": risk.get("position_size", 0),
            "exposure": risk.get("exposure", 0),

            "execution_trigger": execution_trigger.get("confirmed", False),
            "execution_confirmation": execution_confirmation.get("confirmed", False),
            "execution_status": execution.get("status", "IDLE"),
            "execution_reason": execution.get("reason", ""),

            "validator_approved": validator.get("approved", False),
            "validator_score": validator.get("validation_score", 0),
            "validator_blockers": validator.get("blockers", []),

            # Diagnostics
            "mtf": mtf,
            "orderflow": orderflow,
            "volume_profile": volume_profile,
            "gann": gann,
            "smc": smc,
            "structure": structure,
            "liquidity": liquidity,
            "fvg": fvg,
            "premium_discount": premium_discount,
            "wyckoff": wyckoff,
            "equal_levels": equal_levels,
        }

        bus.publish("DASHBOARD_READY")
        return state
