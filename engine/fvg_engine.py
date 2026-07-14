"""
Jaguar Quant X Enterprise
Fair Value Gap Engine v2.0

Structural imbalance intelligence.

Detects:
- Bullish three-candle fair value gaps
- Bearish three-candle fair value gaps
- ATR-normalized minimum gap size
- Fresh imbalance zones
- Partial fills
- Mitigation
- Directional rejection confirmation
- Fully filled / invalidated gaps

FVG lifecycle:
FRESH
PARTIAL_FILL
MITIGATED
CONFIRMED
FILLED
NEUTRAL

A fair value gap is contextual information until current price
interacts with the active imbalance and confirms a directional
reaction.
"""

from core.engine_result import EngineResult
from engine.structure_utils import (
    get_candles,
    valid_candles,
)

LOOKBACK = 100
ATR_PERIOD = 14

MIN_GAP_ATR = 0.10
MITIGATION_RATIO = 0.50


# ==========================================================
# SAFE NUMBER
# ==========================================================

def _number(value, default=0.0):

    try:
        return float(value or default)

    except (TypeError, ValueError):
        return float(default)


# ==========================================================
# TRUE RANGE
# ==========================================================

def _true_range(current, previous):

    high = _number(
        current.get("high")
    )

    low = _number(
        current.get("low")
    )

    previous_close = _number(
        previous.get("close")
    )

    return max(
        high - low,
        abs(
            high - previous_close
        ),
        abs(
            low - previous_close
        ),
    )


# ==========================================================
# ATR
# ==========================================================

def _atr(window, period=ATR_PERIOD):

    if len(window) < 2:

        return 0.0

    ranges = []

    start = max(
        1,
        len(window) - period,
    )

    for index in range(
        start,
        len(window),
    ):

        ranges.append(
            _true_range(
                window[index],
                window[index - 1],
            )
        )

    if not ranges:

        return 0.0

    return sum(ranges) / len(ranges)


# ==========================================================
# CANDLE HELPERS
# ==========================================================

def _bullish(candle):

    return (
        _number(
            candle.get("close")
        )
        >
        _number(
            candle.get("open")
        )
    )


def _bearish(candle):

    return (
        _number(
            candle.get("close")
        )
        <
        _number(
            candle.get("open")
        )
    )


def _intersects(
    candle,
    zone_low,
    zone_high,
):

    high = _number(
        candle.get("high")
    )

    low = _number(
        candle.get("low")
    )

    return (
        high >= zone_low
        and low <= zone_high
    )


# ==========================================================
# FVG DETECTION
# ==========================================================

def _detect_gaps(
    window,
    atr,
):

    gaps = []

    minimum_gap = (
        atr * MIN_GAP_ATR
    )

    for index in range(
        2,
        len(window),
    ):

        first = window[index - 2]

        middle = window[index - 1]

        third = window[index]

        first_high = _number(
            first.get("high")
        )

        first_low = _number(
            first.get("low")
        )

        third_high = _number(
            third.get("high")
        )

        third_low = _number(
            third.get("low")
        )

        # ==================================================
        # BULLISH FVG
        # First candle high below third candle low
        # ==================================================

        bullish_gap_size = (
            third_low - first_high
        )

        if (
            bullish_gap_size >= minimum_gap
            and _bullish(middle)
        ):

            gaps.append(
                {
                    "direction": "BULLISH",
                    "index": index,
                    "zone_low": first_high,
                    "zone_high": third_low,
                    "gap_size":
                        bullish_gap_size,
                }
            )

        # ==================================================
        # BEARISH FVG
        # First candle low above third candle high
        # ==================================================

        bearish_gap_size = (
            first_low - third_high
        )

        if (
            bearish_gap_size >= minimum_gap
            and _bearish(middle)
        ):

            gaps.append(
                {
                    "direction": "BEARISH",
                    "index": index,
                    "zone_low": third_high,
                    "zone_high": first_low,
                    "gap_size":
                        bearish_gap_size,
                }
            )

    return gaps


# ==========================================================
# GAP LIFECYCLE
# ==========================================================

def _evaluate_gap(
    window,
    gap,
):

    direction = gap["direction"]

    zone_low = gap["zone_low"]

    zone_high = gap["zone_high"]

    gap_size = max(
        zone_high - zone_low,
        1e-9,
    )

    midpoint = (
        zone_low + zone_high
    ) / 2.0

    start = gap["index"] + 1

    historical = window[
        start:-1
    ]

    last = window[-1]

    current_index = len(window) - 1

    touched = False

    mitigated = False

    filled = False

    interaction_index = None

    confirmation_index = None

    deepest_fill_ratio = 0.0

    # ======================================================
    # HISTORICAL LIFECYCLE
    # ======================================================
    for historical_offset, candle in enumerate(
        historical,
        start=start,
    ):

        high = _number(
            candle.get("high")
        )

        low = _number(
            candle.get("low")
        )

        close = _number(
            candle.get("close")
        )

        if direction == "BULLISH":

            if low <= zone_high:

                touched = True

                interaction_index = historical_offset

                penetration = (
                    zone_high
                    - max(
                        low,
                        zone_low,
                    )
                )

                fill_ratio = (
                    penetration / gap_size
                )

                deepest_fill_ratio = max(
                    deepest_fill_ratio,
                    fill_ratio,
                )

            if low <= midpoint:

                mitigated = True

            if (
                low <= zone_low
                or close < zone_low
            ):

                filled = True
                break

        else:

            if high >= zone_low:

                touched = True

                interaction_index = historical_offset

                penetration = (
                    min(
                        high,
                        zone_high,
                    )
                    - zone_low
                )

                fill_ratio = (
                    penetration / gap_size
                )

                deepest_fill_ratio = max(
                    deepest_fill_ratio,
                    fill_ratio,
                )

            if high >= midpoint:

                mitigated = True

            if (
                high >= zone_high
                or close > zone_high
            ):

                filled = True
                break

    if filled:

        return {
            "lifecycle": "FILLED",
            "signal": "NEUTRAL",
            "score": 0,
            "confidence": 0.0,
            "interacting": False,
            "fill_ratio":
                deepest_fill_ratio,
        }

    # ======================================================
    # CURRENT CANDLE INTERACTION
    # ======================================================

    last_open = _number(
        last.get("open")
    )

    last_high = _number(
        last.get("high")
    )

    last_low = _number(
        last.get("low")
    )

    last_close = _number(
        last.get("close")
    )

    interacting = _intersects(
        last,
        zone_low,
        zone_high,
    )

    if interacting:

        interaction_index = current_index

    if direction == "BULLISH":

        if (
            last_low <= zone_low
            or last_close < zone_low
        ):

            return {
                "lifecycle": "FILLED",
                "signal": "NEUTRAL",
                "score": 0,
                "confidence": 0.0,
                "interacting":
                    interacting,
                "fill_ratio": 1.0,
            }

        if interacting:

            penetration = (
                zone_high
                - max(
                    last_low,
                    zone_low,
                )
            )

            current_fill = (
                penetration / gap_size
            )

            deepest_fill_ratio = max(
                deepest_fill_ratio,
                current_fill,
            )

            if (
                last_low <= midpoint
                and last_close > zone_high
                and last_close > last_open
            ):

                return {
                    "lifecycle":
                        "CONFIRMED",
                    "signal": "BULLISH",
                    "score": 4,
                    "confidence": 0.85,
                    "interacting": True,
                    "fill_ratio":
                        deepest_fill_ratio,
                    "confirmation_index":
                        current_index,
                    "interaction_index":
                        interaction_index,
                }

            if last_low <= midpoint:

                return {
                    "lifecycle":
                        "MITIGATED",
                    "signal": "NEUTRAL",
                    "score": 0,
                    "confidence": 0.55,
                    "interacting": True,
                    "fill_ratio":
                        deepest_fill_ratio,
                }

            return {
                "lifecycle":
                    "PARTIAL_FILL",
                "signal": "NEUTRAL",
                "score": 0,
                "confidence": 0.40,
                "interacting": True,
                "fill_ratio":
                    deepest_fill_ratio,
            }

    else:

        if (
            last_high >= zone_high
            or last_close > zone_high
        ):

            return {
                "lifecycle": "FILLED",
                "signal": "NEUTRAL",
                "score": 0,
                "confidence": 0.0,
                "interacting":
                    interacting,
                "fill_ratio": 1.0,
            }

        if interacting:

            penetration = (
                min(
                    last_high,
                    zone_high,
                )
                - zone_low
            )

            current_fill = (
                penetration / gap_size
            )

            deepest_fill_ratio = max(
                deepest_fill_ratio,
                current_fill,
            )

            if (
                last_high >= midpoint
                and last_close < zone_low
                and last_close < last_open
            ):

                return {
                    "lifecycle":
                        "CONFIRMED",
                    "signal": "BEARISH",
                    "score": -4,
                    "confidence": 0.85,
                    "interacting": True,
                    "fill_ratio":
                        deepest_fill_ratio,
                    "confirmation_index":
                          current_index,
                      "interaction_index":
                          interaction_index,
                }

            if last_high >= midpoint:

                return {
                    "lifecycle":
                        "MITIGATED",
                    "signal": "NEUTRAL",
                    "score": 0,
                    "confidence": 0.55,
                    "interacting": True,
                    "fill_ratio":
                        deepest_fill_ratio,
                }

            return {
                "lifecycle":
                    "PARTIAL_FILL",
                "signal": "NEUTRAL",
                "score": 0,
                "confidence": 0.40,
                "interacting": True,
                "fill_ratio":
                    deepest_fill_ratio,
            }

    # ======================================================
    # EXISTING ACTIVE GAP
    # ======================================================

    if mitigated:

        lifecycle = "MITIGATED"
        confidence = 0.35

    elif touched:

        lifecycle = "PARTIAL_FILL"
        confidence = 0.30

    else:

        lifecycle = "FRESH"
        confidence = 0.25

    return {
        "lifecycle": lifecycle,
        "signal": "NEUTRAL",
        "score": 0,
        "confidence": confidence,
        "interacting": False,
        "fill_ratio":
            deepest_fill_ratio,
    }


# ==========================================================
# ENGINE
# ==========================================================

def analyze(state):

    candles = valid_candles(
        get_candles(state)
    )

    if len(candles) < 25:

        return EngineResult(
            name="Fair Value Gap",
            signal="NEUTRAL",
            score=0,
            confidence=0.0,
            weight=1.15,
            reasons=[
                "Not enough candles for FVG analysis"
            ],
            metadata={
                "lifecycle": "NEUTRAL",
            },
        ).to_dict()

    window = candles[
        -min(
            LOOKBACK,
            len(candles),
        ):
    ]

    # ======================================================
    # CURRENT ANALYTICAL INDEX
    # ======================================================
    #
    # Canonical index of the latest candle in the local
    # analytical window.
    #
    # This value belongs to analyze() scope. _evaluate_gap()
    # maintains its own local current_index for lifecycle
    # evaluation.
    #
    # ======================================================

    current_index = len(window) - 1

    atr = _atr(
        window
    )

    if atr <= 0:

        return EngineResult(
            name="Fair Value Gap",
            signal="NEUTRAL",
            score=0,
            confidence=0.0,
            weight=1.15,
            reasons=[
                "ATR unavailable for FVG analysis"
            ],
            metadata={
                "lifecycle": "NEUTRAL",
            },
        ).to_dict()

    gaps = _detect_gaps(
        window,
        atr,
    )

    if not gaps:

        return EngineResult(
            name="Fair Value Gap",
            signal="NEUTRAL",
            score=0,
            confidence=0.0,
            weight=1.15,
            reasons=[
                "No structural fair value gap detected"
            ],
            metadata={
                "lifecycle": "NEUTRAL",
                "atr": atr,
                "gap_count": 0,
            },
        ).to_dict()

    # ======================================================
    # SELECT MOST RECENT ACTIVE GAP
    # ======================================================

    selected_gap = None

    selected_evaluation = None

    for gap in reversed(
        gaps
    ):

        evaluation = _evaluate_gap(
            window,
            gap,
        )

        if evaluation[
            "lifecycle"
        ] != "FILLED":

            selected_gap = gap

            selected_evaluation = evaluation

            break

    if selected_gap is None:

        return EngineResult(
            name="Fair Value Gap",
            signal="NEUTRAL",
            score=0,
            confidence=0.0,
            weight=1.15,
            reasons=[
                "All detected fair value gaps filled"
            ],
            metadata={
                "lifecycle": "FILLED",
                "atr": atr,
                "gap_count": len(gaps),
            },
        ).to_dict()

    lifecycle = selected_evaluation[
        "lifecycle"
    ]

    signal = selected_evaluation[
        "signal"
    ]

    score = selected_evaluation[
        "score"
    ]

    confidence = selected_evaluation[
        "confidence"
    ]

    direction = selected_gap[
        "direction"
    ]

    reasons = []

    if lifecycle == "CONFIRMED":

        if direction == "BULLISH":

            reasons.append(
                "Bullish FVG mitigation rejection confirmed"
            )

        else:

            reasons.append(
                "Bearish FVG mitigation rejection confirmed"
            )

    elif lifecycle == "MITIGATED":

        reasons.append(
            f"{direction.title()} FVG mitigated"
        )

    elif lifecycle == "PARTIAL_FILL":

        reasons.append(
            f"{direction.title()} FVG partially filled"
        )

    elif lifecycle == "FRESH":

        reasons.append(
            f"Fresh {direction.lower()} FVG detected"
        )

    else:

        reasons.append(
            "FVG awaiting confirmation"
        )

    return EngineResult(
        name="Fair Value Gap",
        signal=signal,
        score=score,
        confidence=confidence,
        weight=1.15,
        reasons=reasons,
        metadata={
            "lifecycle": lifecycle,
            "direction": direction,
            "zone_low":
                selected_gap["zone_low"],
            "zone_high":
                selected_gap["zone_high"],
            "gap_size":
                selected_gap["gap_size"],

            "origin_index":
                selected_gap["index"],
            "confirmation_index":
                selected_evaluation.get(
                     "confirmation_index"
                ),
            "interaction_index":
                selected_evaluation.get(
                    "interaction_index"
                ),
            "trigger_age":
                (
                    current_index
                    - selected_evaluation.get(
                        "confirmation_index"
                    )
                    if selected_evaluation.get(
                        "confirmation_index"
                    ) is not None
                    else None
                ),
            "interacting":
                selected_evaluation[
                    "interacting"
                ],
            "fill_ratio":
                selected_evaluation[
                    "fill_ratio"
                ],
            "atr": atr,
            "gap_count": len(gaps),
            "last_close": _number(
                window[-1].get("close")
            ),
        },
    ).to_dict()


if __name__ == "__main__":

    from core.market_state import MarketState

    state = MarketState()

    print(
        analyze(state)
    )
