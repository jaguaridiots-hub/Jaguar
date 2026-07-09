class JaguarBrainV4:

    @staticmethod
    def analyze(state):

        # -----------------------------
        # Inputs
        # -----------------------------
        tech = state.ai
        smc = state.smc
        structure = getattr(state, "structure", {})
        probability = state.probability
        pd = state.premium_discount
        wy = state.wyckoff
        mss = state.mss
        eq = state.equal_levels
        orderblock = getattr(state, "orderblock", {})
        score = tech["score"]
        confidence = probability["probability"]
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

        # ===== Equal High / Equal Low =====

        if eq.get("signal") == "EQL":
            score += 15
            reasons.append("Equal Low Liquidity")

        elif eq.get("signal") == "EQH":
            score -= 15
            reasons.append("Equal High Liquidity")

        # -----------------------------
        # Market Structure
        # -----------------------------
        if structure:

            score += structure.get("score", 0)

            if "reasons" in structure:
                reasons.extend(structure["reasons"])

        liquidity = state.liquidity

        score += liquidity.get("score", 0)

        if "reasons" in liquidity:
            reasons.extend(liquidity["reasons"])


        fvg = state.fvg

        score += fvg.get("score", 0)

        if "reasons" in fvg:
            reasons.extend(fvg["reasons"])

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
        # Clamp
        # -----------------------------
        score = max(-100, min(100, score))

        confidence = max(0, min(100, confidence))

        # -----------------------------
        # Signal
        # -----------------------------
        if score >= 80:
            signal = "STRONG BUY"

        elif score >= 50:
            signal = "BUY"

        elif score <= -80:
            signal = "STRONG SELL"

        elif score <= -50:
            signal = "SELL"

        else:
            signal = "WAIT"

        # -----------------------------
        # Grade
        # -----------------------------
        if confidence >= 90:
            grade = "A+"

        elif confidence >= 80:
            grade = "A"

        elif confidence >= 70:
            grade = "B"

        elif confidence >= 60:
            grade = "C"

        else:
            grade = "D"

        # -----------------------------
        # Final Output
        # -----------------------------
        return {
            "signal": signal,
            "score": score,
            "confidence": confidence,
            "grade": grade,
            "reasons": reasons
        }

