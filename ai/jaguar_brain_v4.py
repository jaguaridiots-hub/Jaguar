# ai/jaguar_brain_v4.py
from config.settings import (
    STRONG_BUY_SCORE,
    BUY_SCORE,
    SELL_SCORE,
    STRONG_SELL_SCORE,
)
from ai.profiles import get_profile


class JaguarBrainV4:

    @staticmethod
    def analyze(state):
        debug = getattr(state, "debug_brain", False)
        mode = getattr(state, "mode", "LEGACY")
        profile = get_profile(mode)

        # ------------------------------------------------------------------
        # Safe engine output extraction – always returns a dict
        # ------------------------------------------------------------------
        def _safe(obj):
            """Return obj if it's a dict, else an empty dict."""
            return obj if isinstance(obj, dict) else {}

        # Indicators / Technical
        tech = _safe(getattr(state, "ai", {}))
        # Individual engine outputs
        smc        = _safe(getattr(state, "smc", {}))
        structure  = _safe(getattr(state, "structure", {}))
        probability = _safe(getattr(state, "probability", {}))
        pd         = _safe(getattr(state, "premium_discount", {}))
        wy         = _safe(getattr(state, "wyckoff", {}))
        mss        = _safe(getattr(state, "mss", {}))
        eq         = _safe(getattr(state, "equal_levels", {}))
        orderblock = _safe(getattr(state, "orderblock", {}))
        mtf        = _safe(getattr(state, "mtf", {}))
        gann       = _safe(getattr(state, "gann", {}))
        vp         = _safe(getattr(state, "volume_profile", {}))
        session    = _safe(getattr(state, "session", {}))
        regime     = _safe(getattr(state, "regime", {}))
        orderflow  = _safe(getattr(state, "orderflow", {}))
        liquidity  = _safe(getattr(state, "liquidity", {}))
        fvg        = _safe(getattr(state, "fvg", {}))

        # ------------------------------------------------------------------
        # Explainability
        # ------------------------------------------------------------------
        if debug:
            print("\n" + "=" * 60)
            print("JAGUAR BRAIN EXPLAINABILITY")
            print(f"Mode : {mode}")
            print("=" * 60)

        score = tech.get("score", 0)
        reasons = list(tech.get("reasons", []))
        if "reasons" in probability:
            reasons.extend(probability["reasons"])

        contributions = []

        if debug:
            print(f"\nTechnical Score")
            print(f"Base : {score}")
            print(f"Contribution : +{score}")
            print(f"Running Total : {score}")

        def add_contribution(label, base, multiplier, raw_desc=None):
            nonlocal score
            contrib = base * multiplier
            score += contrib
            contributions.append({
                "label": label,
                "base": base,
                "multiplier": multiplier,
                "raw_desc": raw_desc,
                "contribution": contrib
            })
            if debug:
                print(f"\n{label}")
                if raw_desc is not None:
                    print(f"Raw : {raw_desc}")
                print(f"Base : {base}")
                print(f"Multiplier : {multiplier}")
                print(f"Contribution : {contrib:+.2f}")
                print(f"Running Total : {score:.2f}")
            return contrib

        # ---- Smart Money ----
        smc_base = 0
        smc_desc = "NEUTRAL"
        if smc.get("trend") == "BULLISH":
            smc_base = 10
            smc_desc = "BULLISH"
            reasons.append("Bullish SMC")
        elif smc.get("trend") == "BEARISH":
            smc_base = -10
            smc_desc = "BEARISH"
            reasons.append("Bearish SMC")
        add_contribution("SMC", smc_base, profile.get("smc", 1.0), smc_desc)

        # ---- Premium / Discount ----
        pd_base = 0
        pd_desc = "NEUTRAL"
        if pd.get("zone") == "DISCOUNT":
            pd_base = 10
            pd_desc = "DISCOUNT"
            reasons.append("Discount Zone")
        elif pd.get("zone") == "PREMIUM":
            pd_base = -10
            pd_desc = "PREMIUM"
            reasons.append("Premium Zone")
        add_contribution("Premium/Discount", pd_base, profile.get("premium_discount", 1.0), pd_desc)

        # ---- Wyckoff ----
        wy_base = 0
        wy_desc = "NONE"
        if wy.get("signal") == "ACCUMULATION":
            wy_base = 20
            wy_desc = "ACCUMULATION"
            reasons.append("Wyckoff Accumulation")
        elif wy.get("signal") == "SPRING":
            wy_base = 30
            wy_desc = "SPRING"
            reasons.append("Wyckoff Spring")
        elif wy.get("signal") == "DISTRIBUTION":
            wy_base = -20
            wy_desc = "DISTRIBUTION"
            reasons.append("Wyckoff Distribution")
        elif wy.get("signal") == "UPTHRUST":
            wy_base = -30
            wy_desc = "UPTHRUST"
            reasons.append("Wyckoff Upthrust")
        add_contribution("Wyckoff", wy_base, profile.get("wyckoff", 1.0), wy_desc)

        # ---- MSS ----
        mss_base = 0
        mss_desc = "NONE"
        if mss.get("signal") == "BULLISH_MSS":
            mss_base = 30
            mss_desc = "BULLISH_MSS"
            reasons.append("Bullish MSS")
        elif mss.get("signal") == "BEARISH_MSS":
            mss_base = -30
            mss_desc = "BEARISH_MSS"
            reasons.append("Bearish MSS")
        add_contribution("MSS", mss_base, profile.get("mss", 1.0), mss_desc)

        # ---- Equal Levels ----
        eq_base = 0
        eq_desc = "NONE"
        if eq.get("signal") == "EQL":
            eq_base = 15
            eq_desc = "EQL"
            reasons.append("Equal Low Liquidity")
        elif eq.get("signal") == "EQH":
            eq_base = -15
            eq_desc = "EQH"
            reasons.append("Equal High Liquidity")
        add_contribution("Equal Levels", eq_base, profile.get("equal_levels", 1.0), eq_desc)

        # ---- MTF ----
        mtf_base = 0
        mtf_desc = "NEUTRAL"
        if mtf.get("bias") == "BULLISH" and mtf.get("alignment", 0) >= 3:
            mtf_base = 15
            mtf_desc = f"BULLISH ({mtf.get('alignment')}/4)"
            reasons.append(f"Multi-Timeframe Bullish ({mtf.get('alignment')}/4)")
        elif mtf.get("bias") == "BEARISH" and mtf.get("alignment", 0) >= 3:
            mtf_base = -15
            mtf_desc = f"BEARISH ({mtf.get('alignment')}/4)"
            reasons.append(f"Multi-Timeframe Bearish ({mtf.get('alignment')}/4)")
        else:
            reasons.append("Mixed Multi-Timeframe Structure")
        add_contribution("MTF", mtf_base, profile.get("mtf", 1.0), mtf_desc)

        # ---- Structure ----
        struct_score = structure.get("score", 0)
        add_contribution("Structure", struct_score, profile.get("structure", 1.0), f"Score: {struct_score}")
        if struct_score:
            reasons.extend(structure.get("reasons", []))

        # ---- Liquidity ----
        liq_score = liquidity.get("score", 0)
        add_contribution("Liquidity", liq_score, profile.get("liquidity", 1.0), f"Score: {liq_score}")
        reasons.extend(liquidity.get("reasons", []))

        # ---- FVG ----
        fvg_score = fvg.get("score", 0)
        add_contribution("FVG", fvg_score, profile.get("fvg", 1.0), f"Score: {fvg_score}")
        reasons.extend(fvg.get("reasons", []))

        # ---- Volume Profile ----
        vp_score = vp.get("score", 0)
        add_contribution("Volume Profile", vp_score, profile.get("volume_profile", 1.0), f"Score: {vp_score}")
        reasons.extend(vp.get("reasons", []))

        # ---- Session ----
        sess_score = session.get("score", 0)
        add_contribution("Session", sess_score, profile.get("session", 1.0), f"Score: {sess_score}")
        reasons.extend(session.get("reasons", []))

        # ---- Order Block ----
        ob_base = 0
        ob_desc = "NONE"
        if orderblock:
            trend = orderblock.get("trend", "NONE")
            if trend == "BULLISH":
                ob_base = 15
                ob_desc = "BULLISH"
                reasons.append("Bullish Order Block")
            elif trend == "BEARISH":
                ob_base = -15
                ob_desc = "BEARISH"
                reasons.append("Bearish Order Block")
        add_contribution("Order Block", ob_base, profile.get("order_block", 1.0), ob_desc)

        # ---- Gann ----
        gann_score = gann.get("score", 0)
        add_contribution("Gann", gann_score, profile.get("gann", 1.0), f"Score: {gann_score}")
        reasons.extend(gann.get("reasons", []))

        # ---- Regime ----
        reg_score = regime.get("score", 0)
        add_contribution("Regime", reg_score, profile.get("regime", 1.0), f"Score: {reg_score}")
        reasons.extend(regime.get("reasons", []))

        # ---- Order Flow ----
        of_score = orderflow.get("score", 0)
        add_contribution("Order Flow", of_score, profile.get("order_flow", 1.0), f"Score: {of_score}")
        reasons.extend(orderflow.get("reasons", []))

        # ---- Clamp ----
        score = max(-100, min(100, score))

        if debug:
            print(f"\nFinal Brain Score : {score:.2f}")
            print("=" * 60 + "\n")

        # ---- Store explainability snapshot ----
        state.brain_explain = {
            "contributions": contributions,
            "multipliers": profile,
            "final_score": score,
            "mode": mode
        }

        # ---- Signal ----
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

        confidence_text = probability.get("confidence", "LOW")
        grade = probability.get("grade", "D")

        return {
            "signal": signal,
            "score": score,
            "confidence": confidence_text,
            "grade": grade,
            "reasons": reasons,
        }
