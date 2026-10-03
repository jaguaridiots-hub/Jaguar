class MasterDecisionEngine:
    def run(self, state, bus):
        bus.publish("MASTER_DECISION_ANALYSIS")

        # ---- Read canonical state ----
        ai_brain = getattr(state, "ai_brain", {}) or {}
        probability = getattr(state, "probability", {}) or {}
        regime = getattr(state, "regime", {}) or {}
        smc = getattr(state, "smc", {}) or {}
        structure = getattr(state, "structure", {}) or {}
        validator = getattr(state, "trade_validator", {}) or {}

        ai_score = ai_brain.get("score", 50)
        prob_score = probability.get("score", 50)
        smc_signal = smc.get("signal", "NEUTRAL")
        regime_signal = regime.get("regime", "NEUTRAL")
        structure_state = structure.get("state", "NEUTRAL")
        validator_approved = validator.get("approved", True)

        mode = getattr(state, "mode", "SWING")

        base_score = (ai_score * 0.6) + (prob_score * 0.4)

        # ... SMC, Regime, Structure adjustments (unchanged) ...

        # ---- Mode boost (unchanged) ----
        mode_boost = 0
        if mode == "SCALP":
            base_score += 35
            mode_boost = 35
        elif mode == "SWING":
            base_score += 10
            mode_boost = 10
        # CLASSIC gets no boost (mode_boost remains 0)

        base_score = max(0, min(100, base_score))

        # ---- Thresholds (unchanged) ----
        if mode == "SCALP":
            threshold_buy = 65
            grade_a = "A-"
            grade_b = "B+"
        elif mode == "CLASSIC":
            threshold_buy = 90
            grade_a = "A+"
            grade_b = "B"
        else:
            threshold_buy = 80
            grade_a = "A"
            grade_b = "B"

        # ---- Reasoning (unchanged) ----
        reasoning = []
        # ... build reasoning ...

        # ---- Decision logic (unchanged, except no volume bonus) ----
        decision = "WAIT"
        grade = "F"
        execution = "BLOCKED"
        priority = "LOW"
        final_reasons = []

        if not validator_approved:
            decision = "REJECT"
            grade = "F"
            execution = "BLOCKED"
            priority = "NONE"
            final_reasons = ["Trade Validator rejected the setup"]
            reasoning.append("❌ Validator rejected: trade does not meet all criteria")
        elif base_score >= threshold_buy:
            decision = "BUY"
            grade = grade_a
            execution = "READY"
            priority = "HIGH"
            final_reasons = [f"All conditions met ({mode} mode)"]
            reasoning.append(f"✅ Institutional setup confirmed ({mode})")
        elif base_score >= (threshold_buy - 15) and smc_signal == "BULLISH":
            decision = "BUY"
            grade = grade_b
            execution = "READY"
            priority = "MEDIUM"
            final_reasons = [f"Moderate confidence + SMC confirmation ({mode})"]
            reasoning.append(f"✅ SMC confirms moderate setup ({mode})")
        elif base_score >= (threshold_buy - 15):
            decision = "WAIT"
            grade = "C"
            execution = "BLOCKED"
            priority = "LOW"
            final_reasons = ["Score moderate but lacking SMC confirmation"]
            reasoning.append("⏳ Waiting for SMC confirmation")
        else:
            decision = "REJECT"
            grade = "F"
            execution = "BLOCKED"
            priority = "NONE"
            final_reasons = ["Score below threshold"]
            reasoning.append("❌ Insufficient score for trade")

        # ---- Save Master Decision ----
        state.master_decision = {
            "decision": decision,
            "approved": decision == "BUY",
            "score": int(base_score),
            "confidence": int(base_score + 5),
            "grade": grade,
            "priority": priority,
            "execution": execution,
            "reasons": final_reasons,
            "reasoning": reasoning,
            "components": {
                "ai_score": ai_score,
                "prob_score": prob_score,
                "smc_signal": smc_signal,
                "regime": regime_signal,
                "structure": structure_state,
                "validator_approved": validator_approved,
                "composite_score": int(base_score)
            },
            "timestamp": None
        }

        # ---- Store decision weights for research ----
        state._decision_weights = {
            "brain_weight": 0.6,
            "probability_weight": 0.4,
            "mode_boost": mode_boost,
            "threshold": threshold_buy
        }

        print(f"🔴 MASTER DECISION: {decision} (Score: {int(base_score)})")
        print(f"📊 COMPONENTS: {state.master_decision['components']}")

        bus.publish("MASTER_DECISION_READY")
        return state
