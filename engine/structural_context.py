"""
==========================================================
Jaguar Quant X Enterprise
==========================================================

Module:
    Structural Context Engine (SCE)

Version:
    0.5

Owner:
    Core Architecture

Status:
    Experimental

Regression:
    Required

Purpose:
    Build and publish the canonical structural context
    shared by all market structure engines.

==========================================================
"""

from engine.structure_utils import (
    get_candles,
    valid_candles,
    detect_swings,
)


def analyze(state):
    """
    Build canonical structural context.
    """

    candles = valid_candles(
        get_candles(state)
    )

    swings = detect_swings(
        candles
    )

    highs = swings["highs"]
    lows = swings["lows"]

    latest_high = highs[-1] if highs else None
    latest_low = lows[-1] if lows else None

    previous_high = highs[-2] if len(highs) >= 2 else None
    previous_low = lows[-2] if len(lows) >= 2 else None

    has_structure = (
        latest_high is not None
        and latest_low is not None
    )

    structural_range = {
        "high": (
            latest_high["price"]
            if latest_high
            else None
        ),
        "low": (
            latest_low["price"]
            if latest_low
            else None
        ),
    }

    summary = {
        "swing_high_count": len(highs),
        "swing_low_count": len(lows),
        "latest_high": latest_high,
        "latest_low": latest_low,
        "previous_high": previous_high,
        "previous_low": previous_low,
        "range": structural_range,
        "has_structure": has_structure,
    }

    return {
        "version": "0.5",
        "ready": has_structure,
        "context": {
            "swings": swings,
            "summary": summary,
        },
    }
