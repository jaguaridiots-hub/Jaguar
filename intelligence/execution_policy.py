"""
Jaguar Quant X Enterprise
Execution Policy V2

Institutional execution policy.

This module classifies structural states into:

- READY
- EARLY_READY
- WATCH
- WAIT

Pipeline integration comes later.
"""

# ==========================================================
# LIFECYCLE STATES
# ==========================================================

CONFIRMED_STATES = {
    "CONFIRMED",
}

ANTICIPATION_STATES = {
    "SWEPT",
    "RECLAIMED",
    "PARTIAL_FILL",
    "MITIGATED",
    "ACTIVE",
    "INTERACTING",
}

WATCH_STATES = {
    "POOL_DETECTED",
    "OPEN",
    "AVAILABLE",
}

INVALID_STATES = {
    "INVALIDATED",
    "BROKEN",
    "FILLED",
    "EXPIRED",
}

# ==========================================================
# EXECUTION MODES
# ==========================================================

READY = "READY"
EARLY_READY = "EARLY_READY"
WATCH = "WATCH"
WAIT = "WAIT"


class ExecutionPolicy:
    """
    Institutional Execution Policy.
    """

    @staticmethod
    def empty_result():
        return {
            "mode": WAIT,
            "approved": False,
            "score": 0,
            "confidence": 0,
            "grade": "F",
            "reasons": [],
        }

    @staticmethod
    def evaluate(
        bos_confirmed=False,
        choch_confirmed=False,
        zone_interaction=False,
        liquidity_state="UNKNOWN",
        order_block_state="UNKNOWN",
        fvg_state="UNKNOWN",
        structure_direction="NEUTRAL",
        trigger_direction="NEUTRAL",
        zone_valid=False,
        location_active=False,
        execution_trigger_confirmed=False,
        execution_trigger_conflict=False,
        conflict_count=0,
    ):
        score = 0
        reasons = []

        if bos_confirmed:
            score += 20
            reasons.append("Confirmed BOS")

        if choch_confirmed:
            score += 15
            reasons.append("Confirmed CHoCH")

        if zone_interaction:
            score += 15
            reasons.append("Zone interaction")

        if liquidity_state in CONFIRMED_STATES:
            score += 25
        elif liquidity_state in ANTICIPATION_STATES:
            score += 15
        elif liquidity_state in INVALID_STATES:
            score -= 20

        if order_block_state in CONFIRMED_STATES:
            score += 25
        elif order_block_state in ANTICIPATION_STATES:
            score += 15
        elif order_block_state in INVALID_STATES:
            score -= 25

        if fvg_state in CONFIRMED_STATES:
            score += 20
        elif fvg_state in ANTICIPATION_STATES:
            score += 12
        elif fvg_state in INVALID_STATES:
            score -= 20
        # ==========================================================
        # DIRECTION ALIGNMENT
        # ==========================================================

        if (
            trigger_direction != "NEUTRAL"
            and structure_direction != "NEUTRAL"
        ):
            if trigger_direction == structure_direction:
                score += 10
                reasons.append("Execution direction aligned")
            else:
                score -= 30
                reasons.append("Execution direction conflict")

        # ==========================================================
        # EXECUTION READINESS
        # ==========================================================

        if zone_valid:
            score += 10
            reasons.append("Valid execution zone")

        if location_active:
            score += 15
            reasons.append("Execution location active")

        if execution_trigger_confirmed:
            score += 25
            reasons.append("Execution trigger confirmed")

        if execution_trigger_conflict:
            score -= 30
            reasons.append("Execution trigger conflict")

        if conflict_count > 0:
            penalty = min(conflict_count * 10, 30)
            score -= penalty
            reasons.append(f"{conflict_count} institutional conflict(s)")

        if score >= 90:
            mode = READY
            approved = True
            grade = "A+"
        elif score >= 70:
            mode = EARLY_READY
            approved = True
            grade = "A"
        elif score >= 40:
            mode = WATCH
            approved = False
            grade = "B"
        else:
            mode = WAIT
            approved = False
            grade = "F"

        return {
            "mode": mode,
            "approved": approved,
            "score": score,
            "confidence": max(0, min(100, score)),
            "grade": grade,
            "reasons": reasons,
        }
