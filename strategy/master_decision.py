class MasterDecision:

    @staticmethod
    def decide(state):
        PROBABILITY_WEIGHT = 0.20

        score = 0
        reasons = []

        # AI Brain
        brain = state.brain
        if brain["signal"] == "STRONG BUY":
            score += 25
            reasons.append("AI Strong Buy")
        elif brain["signal"] == "BUY":
            score += 15
            reasons.append("AI Buy")
        elif brain["signal"] == "STRONG SELL":
            score -= 25
            reasons.append("AI Strong Sell")
        elif brain["signal"] == "SELL":
            score -= 15
            reasons.append("AI Sell")

        # Multi-Timeframe
        if state.mtf.get("bias") == "BULLISH":
            score += 20
            reasons.append("Bullish MTF")
        elif state.mtf.get("bias") == "BEARISH":
            score -= 20
            reasons.append("Bearish MTF")

        # Order Flow
        if state.orderflow.get("signal") == "BUY":
            score += 15
            reasons.append("Buy Order Flow")
        elif state.orderflow.get("signal") == "SELL":
            score -= 15
            reasons.append("Sell Order Flow")

        # Session
        score += state.session.get("score", 0)

        # Regime
        score += state.regime.get("score", 0)

        # Volume Profile
        score += state.volume_profile.get("score", 0)

        # Gann
        score += state.gann.get("score", 0)

        # ---- Probability (weighted) ----
        probability = getattr(state, "probability", {})
        prob_score = probability.get("score", 0)
        weighted_probability = round(prob_score * PROBABILITY_WEIGHT)
        score += weighted_probability
        if weighted_probability > 0:
            reasons.append(f"Probability +{weighted_probability}")

        score = max(-100, min(100, score))

        if score >= 80:
            decision = "ENTER"
        elif score >= 60:
            decision = "WATCH"
        elif score <= -80:
            decision = "SHORT"
        else:
            decision = "WAIT"

        state.decision = {
            "decision": decision,
            "score": score,
            "reasons": reasons
        }

        return state
