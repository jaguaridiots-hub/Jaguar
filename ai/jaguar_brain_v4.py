from config.settings import (
    STRONG_BUY_SCORE,
    BUY_SCORE,
    SELL_SCORE,
    STRONG_SELL_SCORE,
)

class JaguarBrainV4:

    @staticmethod
    def analyze(state):

        tech = state.ai
        smc = state.smc
        structure = getattr(state, "structure", {})
        probability = getattr(state, "probability", {}) or {}
        pd = state.premium_discount
        wy = state.wyckoff
        mss = state.mss
        eq = state.equal_levels
        orderblock = getattr(state, "orderblock", {})
        mtf = state.mtf
        gann = state.gann
        vp = state.volume_profile
        session = state.session
        regime = getattr(state, "regime", {})
        orderflow = getattr(state, "orderflow", {})

        score = tech["score"]
        probability_score = probability.get("score", 0)
        confidence = probability.get("confidence", "LOW")
        grade = probability.get("grade", "D")
        quality = probability.get("quality", "*")
        reasons = list(tech["reasons"])

        if "reasons" in probability:
            reasons.extend(probability["reasons"])

        # -----------------------------
        # Smart Money
        # -----------------------------

        if smc.get("trend") == "BULLISH":
            score += 10
            reasons.append("Bullish SMC")

        elif smc.get("trend") == "BEARISH":
            score -= 10
            reasons.append("Bearish SMC")

        if pd.get("zone") == "DISCOUNT":
            score += 10
            reasons.append("Discount Zone")

        elif pd.get("zone") == "PREMIUM":
            score -= 10
            reasons.append("Premium Zone")

        if wy.get("signal") == "ACCUMULATION":
            score += 20
            reasons.append("Wyckoff Accumulation")

        elif wy.get("signal") == "SPRING":
            score += 30
            reasons.append("Wyckoff Spring")

        elif wy.get("signal") == "DISTRIBUTION":
            score -= 20
            reasons.append("Wyckoff Distribution")

        elif wy.get("signal") == "UPTHRUST":
            score -= 30
            reasons.append("Wyckoff Upthrust")

        if mss.get("signal") == "BULLISH_MSS":
            score += 30
            reasons.append("Bullish MSS")

        elif mss.get("signal") == "BEARISH_MSS":
            score -= 30
            reasons.append("Bearish MSS")

        if eq.get("signal") == "EQL":
            score += 15
            reasons.append("Equal Low Liquidity")

        elif eq.get("signal") == "EQH":
            score -= 15
            reasons.append("Equal High Liquidity")

        # -----------------------------
        # Multi Timeframe
        # -----------------------------

        if mtf.get("bias") == "BULLISH":

            if mtf.get("alignment", 0) >= 3:
                score += 15
                reasons.append(
                    f"Multi-Timeframe Bullish ({mtf.get('alignment')}/4)"
                )

        elif mtf.get("bias") == "BEARISH":

            if mtf.get("alignment", 0) >= 3:
                score -= 15
                reasons.append(
                    f"Multi-Timeframe Bearish ({mtf.get('alignment')}/4)"
                )

        else:
            reasons.append("Mixed Multi-Timeframe Structure")

        # -----------------------------
        # Structure
        # -----------------------------

        if structure:
            score += structure.get("score", 0)
            reasons.extend(structure.get("reasons", []))

        liquidity = state.liquidity
        score += liquidity.get("score", 0)
        reasons.extend(liquidity.get("reasons", []))

        fvg = state.fvg
        score += fvg.get("score", 0)
        reasons.extend(fvg.get("reasons", []))

        # -----------------------------
        # Volume Profile
        # -----------------------------

        if vp:
            score += vp.get("score", 0)
            reasons.extend(vp.get("reasons", []))

        # -----------------------------
        # Session
        # -----------------------------

        if session:
            score += session.get("score", 0)
            reasons.extend(session.get("reasons", []))

        # -----------------------------
        # Order Block
        # -----------------------------

        if orderblock:

            trend = orderblock.get("trend", "NONE")

            if trend == "BULLISH":
                score += 15
                reasons.append("Bullish Order Block")

            elif trend == "BEARISH":
                score -= 15
                reasons.append("Bearish Order Block")

        # -----------------------------
        # Gann
        # -----------------------------

        if gann:
            score += gann.get("score", 0)
            reasons.extend(gann.get("reasons", []))

        # -----------------------------
        # Market Regime
        # -----------------------------

        if regime:

            score += regime.get("score", 0)
            reasons.extend(regime.get("reasons", []))

        # -----------------------------
        # Order Flow (future engine)
        # -----------------------------

        if orderflow:

            score += orderflow.get("score", 0)
            reasons.extend(orderflow.get("reasons", []))

        # -----------------------------
        # Clamp
        # -----------------------------

        score = max(-100, min(100, score))
        probability_score = max(0, min(100, probability_score))

        # -----------------------------
        # Signal
        # -----------------------------

        if score >= STRONG_BUY_SCORE:
            signal = "STRONG BUY"

        elif score >= BUY_SCORE:
            signal = "BUY"

        elif score <= STRONG_SELL_SCORE:
            signal = "STRONG SELL"

        elif score <= SELL_SCORE:
            signal = "SELL"

        else:
            signal = "WAIT"

        # --------------------------------
        # Final Grade
        # --------------------------------

        confidence_text = probability.get("confidence", "LOW")
        grade = probability.get("grade", "D")

        return {
            "signal": signal,
            "score": score,
            "confidence": confidence_text,
            "grade": grade,
            "reasons": reasons,
        }

