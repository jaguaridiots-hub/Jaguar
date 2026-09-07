"""
Jaguar Quant X Enterprise
Break of Structure Engine v2.0

Canonical swing-based BOS detector.

A BOS is confirmed when the latest candle CLOSES beyond a
confirmed structural swing pivot.

Wick-only violations are not treated as BOS.
"""

from core.engine_result import EngineResult

from engine.structure_utils import (
    structure_snapshot,
)


# ==========================================================
# ENGINE
# ==========================================================

def analyze(state):

    structure = structure_snapshot(
        state,
        left=2,
        right=2,
        lookback=100,
    )

    candles = structure[
        "candles"
    ]

    if len(candles) < 10:

        return EngineResult(
            name="BOS",
            signal="NEUTRAL",
            score=0,
            confidence=0.0,
            weight=1.15,
            reasons=[
                "Not enough candles"
            ],
            metadata={
                "status": "INSUFFICIENT_DATA",
            },
        ).to_dict()

    latest_high = structure[
        "latest_high"
    ]

    latest_low = structure[
        "latest_low"
    ]

    last = candles[-1]

    last_close = float(
        last.get(
            "close",
            0.0,
        )
        or 0.0
    )

    signal = "NEUTRAL"

    score = 0

    confidence = 0.0

    reasons = []

    status = "WAITING"

    break_level = 0.0

    pivot_index = None

    # ======================================================
    # CANDIDATE STRUCTURAL BREAKS
    # ======================================================

    bullish_break = False

    bearish_break = False

    if latest_high is not None:

        high_price = float(
            latest_high.get(
                "price",
                0.0,
            )
            or 0.0
        )

        high_index = latest_high.get(
            "index"
        )

        if (
            high_index is not None
            and high_index < len(candles) - 1
            and last_close > high_price
        ):

            bullish_break = True

    if latest_low is not None:

        low_price = float(
            latest_low.get(
                "price",
                0.0,
            )
            or 0.0
        )

        low_index = latest_low.get(
            "index"
        )

        if (
            low_index is not None
            and low_index < len(candles) - 1
            and last_close < low_price
        ):

            bearish_break = True

    # ======================================================
    # BULLISH BOS
    # ======================================================

    if (
        bullish_break
        and not bearish_break
    ):

        signal = "BULLISH"

        score = 4

        confidence = 0.80

        status = "CONFIRMED"

        break_level = float(
            latest_high["price"]
        )

        pivot_index = latest_high[
            "index"
        ]

        reasons.append(
            "Bullish BOS above confirmed swing high"
        )

    # ======================================================
    # BEARISH BOS
    # ======================================================

    elif (
        bearish_break
        and not bullish_break
    ):

        signal = "BEARISH"

        score = -4

        confidence = 0.80

        status = "CONFIRMED"

        break_level = float(
            latest_low["price"]
        )

        pivot_index = latest_low[
            "index"
        ]

        reasons.append(
            "Bearish BOS below confirmed swing low"
        )

    # ======================================================
    # STRUCTURAL WAIT
    # ======================================================

    else:

        reasons.append(
            "No confirmed structural break"
        )

    # ======================================================
    # RESULT
    # ======================================================

    return EngineResult(
        name="BOS",
        signal=signal,
        score=score,
        confidence=confidence,
        weight=1.15,
        reasons=reasons,
        metadata={
            "status": status,
            "break_level": break_level,
            "break_price": last_close,
            "pivot_index": pivot_index,
            "latest_swing_high": (
                latest_high
            ),
            "latest_swing_low": (
                latest_low
            ),
        },
    ).to_dict()


# ==========================================================
# LOCAL TEST
# ==========================================================

if __name__ == "__main__":

    from core.market_state import (
        MarketState,
    )

    state = MarketState()

    print(
        analyze(state)
    )
