from config.decision_config import *


class InstitutionalDecisionMatrix:

    @staticmethod
    def evaluate(state):

        score = 0
        reasons = []

        # ==========================================
        # AI Brain
        # ==========================================

        brain = getattr(state, "brain", {}) or {}

        signal = brain.get("signal", "WAIT")

        if signal == "STRONG BUY":
            score += 30
            reasons.append("AI Strong Buy")

        elif signal == "BUY":
            score += 15
            reasons.append("AI Buy")

        elif signal == "STRONG SELL":
            score -= 30
            reasons.append("AI Strong Sell")

        elif signal == "SELL":
            score -= 15
            reasons.append("AI Sell")

        # ==========================================
        # Probability Engine
        # ==========================================

        probability = getattr(state, "probability", {}) or {}

        probability_score = probability.get("score", 0)

        if probability_score >= 80:
            score += 20
            reasons.append("High Probability")

        elif probability_score >= 65:
            score += 10
            reasons.append("Moderate Probability")

        elif probability_score >= 50:
            score += 5
            reasons.append("Acceptable Probability")

        # ==========================================
        # Multi Time Frame
        # ==========================================

        mtf = getattr(state, "mtf", {}) or {}

        bias = mtf.get("bias", "NEUTRAL")
        alignment = mtf.get("alignment", 0)
        alignment_score = mtf.get("alignment_score", 0)
        mtf_strength = mtf.get("strength", 0)

        if bias == "STRONG BULLISH":
            score += 20
            reasons.append("Strong Bullish MTF")

        elif bias == "BULLISH":
            score += 15
            reasons.append("Bullish MTF")

        elif bias == "STRONG BEARISH":
            score -= 20
            reasons.append("Strong Bearish MTF")

        elif bias == "BEARISH":
            score -= 15
            reasons.append("Bearish MTF")

        if alignment_score >= 8:
            score += 10
            reasons.append("Excellent MTF Alignment")

        elif alignment_score >= 5:
            score += 5
            reasons.append("Good MTF Alignment")

        elif mtf_strength >= 50:
            score += 3
            reasons.append("Moderate MTF Strength")

        # ==========================================
        # Market Structure
        # ==========================================

        structure = getattr(state, "structure", {}) or {}

        structure_score = structure.get("score", 0)
        score += structure_score

        bos = structure.get("bos", {}) or {}
        choch = structure.get("choch", {}) or {}

        if bos.get("signal") in ("BULLISH", "BOS"):
            reasons.append("Bullish BOS")

        elif bos.get("signal") in ("BEARISH",):
            reasons.append("Bearish BOS")

        if choch.get("signal") == "BULLISH":
            score += 5
            reasons.append("Bullish CHoCH")

        elif choch.get("signal") == "BEARISH":
            score -= 5
            reasons.append("Bearish CHoCH")

        # ==========================================
        # Liquidity
        # ==========================================

        liquidity = getattr(state, "liquidity", {}) or {}

        score += liquidity.get("score", 0)

        if liquidity.get("signal") == "BUY":
            reasons.append("Bullish Liquidity")

        elif liquidity.get("signal") == "SELL":
            reasons.append("Bearish Liquidity")

        # ==========================================
        # Fair Value Gap
        # ==========================================

        fvg = getattr(state, "fvg", {}) or {}

        score += fvg.get("score", 0)

        if fvg.get("signal") == "BULLISH":
            reasons.append("Bullish FVG")

        elif fvg.get("signal") == "BEARISH":
            reasons.append("Bearish FVG")

        # ==========================================
        # Premium / Discount
        # ==========================================

        premium = getattr(state, "premium_discount", {}) or {}

        zone = premium.get("zone", "UNKNOWN")

        if zone == "DISCOUNT":
            score += 10
            reasons.append("Discount Zone")

        elif zone == "PREMIUM":
            score -= 10
            reasons.append("Premium Zone")

        else:
            reasons.append("Equilibrium Zone")

        # ==========================================
        # Wyckoff
        # ==========================================

        wyckoff = getattr(state, "wyckoff", {}) or {}

        score += wyckoff.get("score", 0)

        if wyckoff.get("signal") == "ACCUMULATION":
            reasons.append("Wyckoff Accumulation")

        elif wyckoff.get("signal") == "DISTRIBUTION":
            reasons.append("Wyckoff Distribution")

        # ==========================================
        # Volume Profile
        # ==========================================

        vp = getattr(state, "volume_profile", {}) or {}

        score += vp.get("score", 0)

        if vp.get("signal") == "BULLISH":
            reasons.append("Bullish Volume Profile")

        elif vp.get("signal") == "BEARISH":
            reasons.append("Bearish Volume Profile")

        # ==========================================
        # Session
        # ==========================================

        session = getattr(state, "session", {}) or {}

        score += session.get("score", 0)

        if session.get("session") == "LONDON_NEWYORK":
            reasons.append("High Liquidity Session")

        # ==========================================
        # Confluence
        # ==========================================

        confluence = getattr(state, "confluence", {}) or {}

        score += confluence.get("score", 0)

        if confluence.get("score", 0):
            reasons.append("Institutional Confluence")

        # ==========================================
        # Order Flow
        # ==========================================

        orderflow = getattr(state, "orderflow", {}) or {}

        score += orderflow.get("score", 0)

        if orderflow.get("signal") == "BUY":
            reasons.append("Bullish Order Flow")

        elif orderflow.get("signal") == "SELL":
            reasons.append("Bearish Order Flow")

        # ==========================================
        # Session
        # ==========================================

        session = getattr(state, "session", {}) or {}

        score += session.get("score", 0)

        if session.get("score", 0):
            reasons.append("Active Institutional Session")

        # ==========================================
        # Volume Profile
        # ==========================================

        vp = getattr(state, "volume_profile", {}) or {}

        score += vp.get("score", 0)

        if vp.get("score", 0):
            reasons.append("Volume Profile Confirmation")

        # ==========================================
        # Market Regime
        # ==========================================

        regime = getattr(state, "regime", {}) or {}

        score += regime.get("score", 0)

        if regime.get("score", 0):
            reasons.append("Market Regime")

        # ==========================================
        # Gann
        # ==========================================

        gann = getattr(state, "gann", {}) or {}

        score += gann.get("score", 0)

        if gann.get("score", 0):
            reasons.append("Gann Confirmation")

        # ==========================================
        # Risk
        # ==========================================

        risk = getattr(state, "risk", {}) or {}

        if risk.get("status") == "SAFE":
            score += 10
            reasons.append("Risk Safe")

        elif risk.get("status") == "HIGH RISK":
            score -= 20
            reasons.append("High Risk")
        # ==========================================
        # Clamp Score
        # ==========================================

        score = max(MIN_SCORE, min(MAX_SCORE, score))

        # ==========================================
        # Institutional Decision
        # ==========================================

        long_confirm = (
            alignment_score >= 5
            or mtf_strength >= 50
            or probability_score >= 80
            or (
                probability_score >= 75
                and orderflow.get("signal") == "BUY"
                and risk.get("status") == "SAFE"
            )
        )

        short_confirm = (
            alignment_score <= -5
            or mtf_strength >= 50
            or probability_score >= 80
            or (
                probability_score >= 75
                and orderflow.get("signal") == "SELL"
                and risk.get("status") == "SAFE"
            )
        )

        if (
            score >= MASTER_ENTER_SCORE
            and signal in ("BUY", "STRONG BUY")
            and risk.get("status") == "SAFE"
            and long_confirm
        ):
            decision = "ENTER"

        elif (
            score <= MASTER_SHORT_SCORE
            and signal in ("SELL", "STRONG SELL")
            and risk.get("status") == "SAFE"
            and short_confirm
        ):
            decision = "SHORT"

        elif (
            score >= MASTER_WATCH_SCORE
            and signal in ("BUY", "STRONG BUY")
        ):
            decision = "WATCH"

        elif (
            score <= MASTER_SHORT_SCORE
            and signal in ("SELL", "STRONG SELL")
        ):
            decision = "WATCH"

        else:
            decision = "WAIT"

        # ==========================================
        # Save Result
        # ==========================================

        state.idm = {
            "decision": decision,
            "score": score,
            "approved": decision in ("ENTER", "SHORT"),
            "reasons": reasons,
        }

        return state
