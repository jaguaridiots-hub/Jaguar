"""
Evidence Fusion Engine
Phase 2B
"""

from core.fusion_result import FusionResult


class EvidenceFusionEngine:
    """
    Collect EvidenceBlocks and compute confidence statistics.
    """

    # Phase 2B.7 - Initial engine weights
    ENGINE_WEIGHTS = {
        "SMC": 1.30,
        "Structure": 1.25,
        "Wyckoff": 1.05,
        "Liquidity": 1.10,
        "FVG": 1.05,
        "Order Block": 1.20,
        "Order Flow": 1.20,
        "Volume Profile": 1.10,
        "Session": 1.00,
        "MTF": 1.25,
        "Regime": 1.15,
        "Gann": 1.05,
        "Equal Levels": 1.00,
        "Premium/Discount": 1.05,
        "MSS": 1.25,
    }

    def __init__(self):
        pass

    def fuse(self, blackboard):
        result = FusionResult()

        # Collect EvidenceBlocks
        result.evidence_blocks = list(blackboard.get_all())

        if not result.evidence_blocks:
            return result

        # -------------------------------
        # Confidence statistics
        # -------------------------------
        raw = [b.confidence_raw for b in result.evidence_blocks]
        calibrated = [b.confidence_calibrated for b in result.evidence_blocks]

        result.average_raw_confidence = sum(raw) / len(raw)
        result.average_calibrated_confidence = (
            sum(calibrated) / len(calibrated)
        )

        result.max_confidence = max(calibrated)
        result.min_confidence = min(calibrated)

        # -------------------------------
        # Confidence-weighted aggregation
        # -------------------------------
        for block in result.evidence_blocks:

            signal = block.signal.upper()

            if signal == "STRONG BULLISH":
                signal = "BULLISH"
            elif signal == "STRONG BEARISH":
                signal = "BEARISH"

            weight = self.ENGINE_WEIGHTS.get(block.engine, 1.0)

            contribution = weight * block.confidence_calibrated

            result.engine_contributions.append(
                (block.engine, contribution)
            )

            if signal == "BULLISH":
                result.bullish_engines += 1
                result.bullish_score += contribution

            elif signal == "BEARISH":
                result.bearish_engines += 1
                result.bearish_score += contribution

            else:
                result.neutral_engines += 1
                result.neutral_score += contribution

        # Sort engine contributions (highest first)
        result.engine_contributions.sort(
            key=lambda x: x[1],
            reverse=True,
        )


        # -------------------------------
        # Conflict / Agreement detection
        # Phase 2B.8 Institutional Model
        # -------------------------------
        #
        # Neutral evidence is NOT conflict.
        # Conflict exists only when directional
        # engines oppose the consensus.
        #
        # Example:
        #   Bullish = 8
        #   Bearish = 2
        #   Neutral = 5
        #
        #   Directional = 10
        #   Agreement   = 8 / 10 = 0.80
        #   Conflict    = 2
        #
        directional_total = (
            result.bullish_engines +
            result.bearish_engines
        )

        if result.bullish_engines >= result.bearish_engines:
            dominant_directional = result.bullish_engines
            opposing_directional = result.bearish_engines
        else:
            dominant_directional = result.bearish_engines
            opposing_directional = result.bullish_engines

        result.conflict_count = opposing_directional

        if directional_total > 0:
            result.agreement_ratio = (
                dominant_directional / directional_total
            )
        else:
            result.agreement_ratio = 0.0

        # -------------------------------
        # Consensus generation (Phase 2B.9)
        # -------------------------------
        if (
            result.bullish_score >= result.bearish_score and
            result.bullish_score >= result.neutral_score
        ):
            result.consensus = "BULLISH"
            winning_score = result.bullish_score

        elif (
            result.bearish_score >= result.bullish_score and
            result.bearish_score >= result.neutral_score
        ):
            result.consensus = "BEARISH"
            winning_score = result.bearish_score

        else:
            result.consensus = "NEUTRAL"
            winning_score = result.neutral_score

        # -------------------------------
        # Institutional Confidence
        # Normalize using active evidence only
        # -------------------------------

        active_score = (
            result.bullish_score +
            result.bearish_score +
            result.neutral_score
        )

        if active_score > 0:
            result.confidence = min(
                winning_score / active_score,
                1.0,
            )
        else:
            result.confidence = 0.0

        # -------------------------------
        # Explainable consensus (Phase 2B.10)
        # -------------------------------
        for block in result.evidence_blocks:

            signal = block.signal.upper().strip()

            if signal == "STRONG BULLISH":
                signal = "BULLISH"
            elif signal == "STRONG BEARISH":
                signal = "BEARISH"

            contribution = (
                self.ENGINE_WEIGHTS.get(block.engine, 1.0)
                * block.confidence_calibrated
            )

            if signal == result.consensus:
                result.supporting_engines.append(block.engine)
                result.top_supporters.append(
                    (block.engine, contribution)
                )

            elif signal == "NEUTRAL":
                result.ignored_engines.append(block.engine)

            else:
                result.opposing_engines.append(block.engine)
                result.top_opponents.append(
                    (block.engine, contribution)
                )

            result.explanation.append(
                f"{block.engine}: {signal} "
                f"(conf={block.confidence_calibrated:.2f})"
            )

        # Rank contributors
        result.top_supporters.sort(
            key=lambda x: x[1],
            reverse=True,
        )

        result.top_opponents.sort(
            key=lambda x: x[1],
            reverse=True,
        )

        # Keep only top 5
        result.top_supporters = result.top_supporters[:5]
        result.top_opponents = result.top_opponents[:5]


        return result
