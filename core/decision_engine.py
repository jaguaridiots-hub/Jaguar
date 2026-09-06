"""
Institutional Decision Engine
Phase 3.3.1
"""

from core.decision_result import DecisionResult


class DecisionEngine:

    # Institutional thresholds
    MIN_CONFIDENCE = 0.60
    MIN_AGREEMENT_RATIO = 0.65
    MAX_CONFLICT_COUNT = 4

    REQUIRED_ENGINES = (
        "SMC",
        "Structure",
        "MTF",
    )

    def evaluate(self, fusion):

        result = DecisionResult()

        # Copy FusionResult statistics
        result.confidence = fusion.confidence
        result.agreement_ratio = fusion.agreement_ratio
        result.conflict_count = fusion.conflict_count

        result.supporting_engines = list(fusion.supporting_engines)
        result.opposing_engines = list(fusion.opposing_engines)

        # ---------------------------------
        # Rule 1 : Minimum confidence
        # ---------------------------------
        if fusion.confidence < self.MIN_CONFIDENCE:
            result.action = "WAIT"
            result.approved = False

            result.failed_checks.append(
                f"Confidence below threshold ({fusion.confidence:.2f} < {self.MIN_CONFIDENCE:.2f})"
            )

            result.reasons.append(
                "Trade rejected because confidence is too low."
            )

            return result

        result.passed_checks.append(
            "Minimum confidence satisfied"
        )
        # ---------------------------------
        # Rule 2 : Minimum agreement ratio
        # ---------------------------------
        if fusion.agreement_ratio < self.MIN_AGREEMENT_RATIO:

            result.action = "WAIT"
            result.approved = False

            result.failed_checks.append(
                f"Agreement ratio below threshold ({fusion.agreement_ratio:.2f} < {self.MIN_AGREEMENT_RATIO:.2f})"
            )

            result.reasons.append(
                "Trade rejected because engine agreement is too low."
            )

            return result

        result.passed_checks.append(
            "Minimum agreement ratio satisfied"
        )

        # ---------------------------------
        # Rule 3 : Maximum conflict count
        # ---------------------------------
        if fusion.conflict_count > self.MAX_CONFLICT_COUNT:

            result.action = "WAIT"
            result.approved = False

            result.failed_checks.append(
                f"Conflict count above threshold ({fusion.conflict_count} > {self.MAX_CONFLICT_COUNT})"
            )

            result.reasons.append(
                "Trade rejected because engine conflict is too high."
            )

            return result

        result.passed_checks.append(
            "Maximum conflict count satisfied"
        )

        # ---------------------------------
        # Rule 4 : Required engine confirmation
        # ---------------------------------
        available = set(result.supporting_engines)

        missing = [
            engine
            for engine in self.REQUIRED_ENGINES
            if engine not in available
        ]

        if missing:

            result.action = "WAIT"
            result.approved = False

            result.failed_checks.append(
                "Missing required engines: " + ", ".join(missing)
            )

            result.reasons.append(
                "Institutional confirmation requirements not satisfied."
            )

            return result

        result.passed_checks.append(
            "Required engine confirmation satisfied"
        )

        # ---------------------------------
        # Basic decision
        # ---------------------------------
        if fusion.consensus == "BULLISH":
            result.action = "ENTER_LONG"
            result.approved = True

        elif fusion.consensus == "BEARISH":
            result.action = "ENTER_SHORT"
            result.approved = True

        else:
            result.action = "WAIT"
            result.approved = False

        result.reasons.append(
            f"Fusion consensus = {fusion.consensus}"
        )

        return result
