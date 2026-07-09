class ExecutionEngine:

    def run(self, state, bus):

        bus.publish("EXECUTION_ANALYSIS")

        # Safe defaults
        decision = getattr(state, "decision", {}) or {}
        regime = getattr(state, "regime", {}) or {}
        session = getattr(state, "session", {}) or {}
        orderflow = getattr(state, "orderflow", {}) or {}
        mtf = getattr(state, "mtf", {}) or {}
        risk = getattr(state, "risk", {}) or {}

        score = 0
        reasons = []

        # -------------------------------------------------
        # Decision Engine
        # -------------------------------------------------
        if decision.get("decision") == "ENTER":
            score += 40
            reasons.append("Decision Approved")

        elif decision.get("decision") == "WATCH":
            score += 20
            reasons.append("Decision Watch")

        # -------------------------------------------------
        # Session
        # -------------------------------------------------
        if session.get("score", 0) >= 20:
            score += 15
            reasons.append("Active Trading Session")

        # -------------------------------------------------
        # Order Flow
        # -------------------------------------------------
        if orderflow.get("signal") == "BUY":
            score += 15
            reasons.append("Buy Order Flow")

        elif orderflow.get("signal") == "SELL":
            score += 15
            reasons.append("Sell Order Flow")

        # -------------------------------------------------
        # Market Regime
        # -------------------------------------------------
        if regime.get("regime") == "TREND":
            score += 15
            reasons.append("Trending Market")

        elif regime.get("regime") == "COMPRESSION":
            score -= 10
            reasons.append("Range Market")

        # -------------------------------------------------
        # Multi-Timeframe Alignment
        # -------------------------------------------------
        alignment = mtf.get("alignment", 0)

        if alignment >= 4:
            score += 20
            reasons.append("Full MTF Alignment")

        elif alignment >= 3:
            score += 10
            reasons.append("Strong MTF Alignment")

        # -------------------------------------------------
        # Risk Filter
        # -------------------------------------------------
        if risk.get("status") == "SAFE":
            score += 10
            reasons.append("Risk Acceptable")

        elif risk.get("status") == "HIGH RISK":
            score -= 20
            reasons.append("High Risk")

        elif risk.get("status") == "NO TRADE":
            score -= 100
            reasons.append("Risk Block")

        # -------------------------------------------------
        # Clamp
        # -------------------------------------------------
        score = max(0, min(100, score))

        # -------------------------------------------------
        # Final Execution Signal
        # -------------------------------------------------
        if score >= 85:
            signal = "ENTER NOW"

        elif score >= 65:
            signal = "WAIT CONFIRMATION"

        else:
            signal = "NO ENTRY"

        state.execution = {
            "signal": signal,
            "score": score,
            "reasons": reasons
        }

        bus.publish("EXECUTION_READY")

        return state
