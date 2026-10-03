# strategy/smc_engine.py

from core.evidence_contracts import EvidenceBlock, SubEvidence
from core.market_blackboard import MarketBlackboard


class SMCEngine:

    def run(self, state, bus):

        bus.publish("SMC_ANALYSIS")

        candles = state.market_current["candles"]

        highs = [c["high"] for c in candles]
        lows = [c["low"] for c in candles]
        closes = [c["close"] for c in candles]

        # -------------------------------------------------
        # CANONICAL STRUCTURE AUTHORITY
        # StructureEngineRunner runs before SMC.
        # SMC consumes canonical BOS / CHOCH / trend.
        # -------------------------------------------------
        structure = getattr(state, "structure", {}) or {}
        structure_bos = structure.get("bos", {}) or {}
        structure_choch = structure.get("choch", {}) or {}

        trend = structure.get("trend", "SIDEWAYS")

        bos_signal = structure_bos.get("signal", "NONE")
        choch_signal = structure_choch.get("signal", "NEUTRAL")

        bos = bos_signal in ("BULLISH_BOS", "BEARISH_BOS")
        choch = choch_signal in ("BULLISH", "BEARISH")

        swing = structure.get("swing", {}) or {}

        swing_high_data = swing.get("swing_high", {})
        swing_low_data = swing.get("swing_low", {})

        swing_high = (
            swing_high_data.get("price")
            if isinstance(swing_high_data, dict)
            else None
        )

        swing_low = (
            swing_low_data.get("price")
            if isinstance(swing_low_data, dict)
            else None
        )

        # Equal levels and liquidity remain SMC-specific.
        equal_high = (
            swing_high is not None
            and abs(swing_high - highs[-2]) < 0.001 * swing_high
        )

        equal_low = (
            swing_low is not None
            and abs(swing_low - lows[-2]) < 0.001 * swing_low
        )

        liquidity = False

        if swing_high is not None and highs[-1] > swing_high and closes[-1] < swing_high:
            liquidity = True


        # ---- Canonical structure score ----
        # StructureEngine is the authoritative source for
        # BOS / CHOCH / trend / directional score.
        score = structure.get("score", 0)

        # SMC-specific liquidity may contribute only when
        # canonical structure itself has no directional score.
        if score == 0 and liquidity:
            score = 5 if trend == "BULLISH" else -5

        state.smc = {
            "trend": trend,
            "bos": bos,
            "choch": choch,
            "liquidity_sweep": liquidity,
            "equal_high": equal_high,
            "equal_low": equal_low,
            "swing_high": swing_high,
            "swing_low": swing_low,
            "score": score                     # <-- new
        }

        # ---- Brain V5 EvidenceBlock ----
        # IMPORTANT:
        # StructureEngine is the canonical authority for:
        #   - trend
        #   - BOS
        #   - CHOCH
        #   - structural score
        #
        # Those values remain available in state.smc for compatibility,
        # but MUST NOT be re-published by SMC as independent evidence.
        #
        # SMC EvidenceBlock contains only SMC-specific evidence.

        liquidity_evidence_signal = (
            "BULLISH"
            if liquidity and trend == "BULLISH"
            else "BEARISH"
            if liquidity and trend == "BEARISH"
            else "NEUTRAL"
        )

        sub_list = [
            SubEvidence(
                "Liquidity Sweep",
                liquidity_evidence_signal,
                0.7 if liquidity else 0.2,
            ),
        ]

        # SMC evidence confidence is based ONLY on SMC-specific evidence.
        # Do not derive it from canonical Structure score.
        smc_raw_conf = 0.7 if liquidity else 0.1

        smc_signal = (
            liquidity_evidence_signal
            if liquidity
            else "NEUTRAL"
        )

        block = EvidenceBlock(
            engine="SMC",
            signal=smc_signal,
            confidence_raw=smc_raw_conf,
            sub_evidence=sub_list,
        )

        if not hasattr(state, "blackboard"):
            state.blackboard = MarketBlackboard()
        state.blackboard.publish(block)

        bus.publish("SMC_READY")

        return state
