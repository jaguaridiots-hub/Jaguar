"""
Canonical Order Block Engine Runner.

The registered runner executes the real strategy-level OrderBlockEngine exactly once
and publishes its result into the canonical enterprise market contract.
"""

import time

from core.engine import Engine
from core.evidence_contracts import EvidenceBlock, SubEvidence
from core.market_blackboard import MarketBlackboard
from strategy.orderblock_engine import OrderBlockEngine


class OrderBlockEngineRunner(Engine):
    engine_name = "Order Block"

    def run(self, state, bus):
        bus.publish("ORDERBLOCK_ANALYSIS")

        if not hasattr(state, "market") or not isinstance(state.market, dict):
            state.market = {}

        engine = OrderBlockEngine()
        result = engine.run(state, bus)

        analysis_data = getattr(state, "order_block", {}) or {}

        if not isinstance(analysis_data, dict):
            analysis_data = {}

        bullish = analysis_data.get("bullish")
        bearish = analysis_data.get("bearish")
        score = analysis_data.get("score", 0)

        if bullish:
            signal = "BULLISH"
        elif bearish:
            signal = "BEARISH"
        else:
            signal = "NEUTRAL"

        try:
            score = float(score or 0)
        except (TypeError, ValueError):
            score = 0.0

        # ------------------------------------------------------------
        # CANONICAL STRUCTURAL ZONE METADATA
        # ------------------------------------------------------------
        # The strategy detector returns real OB candidates in:
        #   bullish = {high, low, index}
        #   bearish = {high, low, index}
        #
        # StructuralZoneEngine requires normalized metadata.
        # Preserve detector truth; do not invent a confirmed trigger.
        # ------------------------------------------------------------

        # ------------------------------------------------------------
        # CANONICAL ZONE SELECTION
        #
        # Preserve BOTH detector candidates and normalize
        # lifecycle independently for each direction.
        # StructuralZoneEngine remains responsible for
        # directional selection.
        # ------------------------------------------------------------

        try:
            price = float(
                getattr(state, "price", 0.0) or 0.0
            )
        except (TypeError, ValueError):
            price = 0.0

        candles = []
        if isinstance(getattr(state, "market_current", None), dict):
            candles = state.market_current.get("candles", []) or []

        def normalize_candidate(candidate, direction):
            if not isinstance(candidate, dict):
                return None

            origin_index = candidate.get("index")
            if origin_index is None:
                return None

            try:
                origin_index = int(origin_index)
                zone_low = float(candidate.get("low", 0.0) or 0.0)
                zone_high = float(candidate.get("high", 0.0) or 0.0)
            except (TypeError, ValueError):
                return None

            if zone_low <= 0 or zone_high <= 0:
                return None

            if zone_low > zone_high:
                zone_low, zone_high = zone_high, zone_low

            metadata = {
                "direction": direction,
                "lifecycle": "DETECTED",
                "zone_low": zone_low,
                "zone_high": zone_high,
                "origin_index": origin_index,
                "interacting": False,
                "interaction_index": None,
                "confirmation_index": None,
                "invalidated_index": None,
                "trigger_age": None,
            }

            if price > 0 and candles:
                for i in range(origin_index + 1, len(candles)):
                    candle = candles[i]

                    try:
                        candle_low = float(candle["low"])
                        candle_high = float(candle["high"])
                        close = float(candle["close"])
                        open_price = float(candle["open"])
                    except (KeyError, TypeError, ValueError):
                        continue

                    touched = (
                        candle_low <= zone_high
                        and candle_high >= zone_low
                    )

                    # Close-based invalidation. Wick penetration alone does not invalidate.
                    if (
                        direction == "BULLISH"
                        and close < zone_low
                    ):
                        metadata["lifecycle"] = "INVALIDATED"
                        metadata["invalidated_index"] = i
                        break

                    if (
                        direction == "BEARISH"
                        and close > zone_high
                    ):
                        metadata["lifecycle"] = "INVALIDATED"
                        metadata["invalidated_index"] = i
                        break

                    if not touched:
                        continue

                    if metadata["interaction_index"] is None:
                        metadata["interaction_index"] = i

                    if (
                        direction == "BULLISH"
                        and close > zone_high
                        and close > open_price
                    ):
                        metadata["confirmation_index"] = i
                        metadata["lifecycle"] = "CONFIRMED"
                        metadata["trigger_age"] = len(candles) - 1 - i
                        break

                    if (
                        direction == "BEARISH"
                        and close < zone_low
                        and close < open_price
                    ):
                        metadata["confirmation_index"] = i
                        metadata["lifecycle"] = "CONFIRMED"
                        metadata["trigger_age"] = len(candles) - 1 - i
                        break

                if zone_low <= price <= zone_high:
                    if metadata["lifecycle"] not in (
                        "CONFIRMED",
                        "INVALIDATED",
                    ):
                        metadata["interacting"] = True
                        metadata["lifecycle"] = "INTERACTING"

            return metadata

        bullish_metadata = normalize_candidate(
            bullish,
            "BULLISH",
        )

        bearish_metadata = normalize_candidate(
            bearish,
            "BEARISH",
        )

        metadata_by_direction = {
            "BULLISH": bullish_metadata,
            "BEARISH": bearish_metadata,
        }

        candidates = [
            metadata
            for metadata in metadata_by_direction.values()
            if metadata is not None
        ]

        # Preserve both directional candidates. StructuralZoneEngine is the
        # canonical authority for directional zone selection, so the runner
        # must not pick a "canonical" OB merely because it has the newest
        # origin_index.
        selected = None

        active_candidates = [
            candidate
            for candidate in candidates
            if str(
                candidate.get("lifecycle", "UNKNOWN")
            ).upper() in {
                "DETECTED",
                "FRESH",
                "INTERACTING",
                "MITIGATED",
                "CONFIRMED",
            }
        ]

        # Only expose a directional runner-level signal when exactly one
        # active directional candidate exists. When both directions are
        # active, remain neutral and let StructuralZoneEngine select.
        if len(active_candidates) == 1:
            selected = active_candidates[0]
            canonical_direction = selected.get(
                "direction",
                "NEUTRAL",
            )
        else:
            canonical_direction = "NEUTRAL"

        metadata = (
            dict(selected)
            if selected is not None
            else {
                "direction": "NEUTRAL",
                "lifecycle": "UNKNOWN",
                "zone_low": 0.0,
                "zone_high": 0.0,
                "origin_index": None,
                "interacting": False,
                "interaction_index": None,
                "confirmation_index": None,
                "trigger_age": None,
            }
        )

        selected_lifecycle = str(
            metadata.get(
                "lifecycle",
                "UNKNOWN",
            )
        ).upper()

        state.orderblock = {
            "signal": canonical_direction,
            "score": 0.0 if selected_lifecycle == "INVALIDATED" else score,
            "bullish": bullish,
            "bearish": bearish,
            "metadata": metadata,
            "metadata_by_direction": metadata_by_direction,
        }

        state.market["order_block_result"] = dict(
            state.orderblock
        )

        confidence = min(abs(score) / 20.0, 1.0) if score else 0.1

        block = EvidenceBlock(
            engine=self.engine_name,
            signal=signal,
            confidence_raw=confidence,
            confidence_calibrated=confidence,
            sub_evidence=[
                SubEvidence(
                    "Order Block Signal",
                    signal,
                    confidence,
                ),
            ],
            lifecycle_state="DETECTED",
            timestamp=time.time(),
        )

        if not hasattr(state, "blackboard"):
            state.blackboard = MarketBlackboard()

        state.blackboard.publish(block)

        bus.publish(
            "ORDERBLOCK_READY",
            state.orderblock,
        )

        return state
