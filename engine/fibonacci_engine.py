"""
Jaguar Quant X Enterprise
Fibonacci Engine v2.0

Canonical state-native Fibonacci market intelligence.

Responsibilities:
- Resolve candles from enterprise market state
- Validate the analytical candle dataset
- Calculate 100-candle structural Fibonacci range
- Detect retracement location
- Expose canonical Fibonacci metadata

Candle authority:

    state.market["candles"]
        ->
    state.candles compatibility fallback
        ->
    empty dataset

No module-global market snapshot is permitted.
"""

from core.engine_result import EngineResult

from engine.structure_utils import (
    get_candles,
    valid_candles,
)


LOOKBACK = 100


# ==========================================================
# SAFE NUMBER
# ==========================================================

def _number(value, default=0.0):

    try:
        return float(value)

    except (TypeError, ValueError):
        return float(default)


# ==========================================================
# ENGINE
# ==========================================================

def analyze(state):

    # ======================================================
    # CANONICAL CANDLE SOURCE
    # ======================================================

    candles = valid_candles(
        get_candles(state)
    )

    if len(candles) < LOOKBACK:

        return EngineResult(
            name="Fibonacci",
            signal="NEUTRAL",
            score=0,
            confidence=0.0,
            weight=1.10,
            reasons=[
                "Not enough candles"
            ],
            metadata={
                "status": "INSUFFICIENT_DATA",
                "candle_count": len(candles),
                "required_candles": LOOKBACK,
            },
        ).to_dict()

    # ======================================================
    # ANALYTICAL WINDOW
    # ======================================================

    window = candles[
        -LOOKBACK:
    ]

    highs = [
        _number(
            candle.get("high")
        )
        for candle in window
    ]

    lows = [
        _number(
            candle.get("low")
        )
        for candle in window
    ]

    swing_high = max(highs)

    swing_low = min(lows)

    diff = (
        swing_high
        - swing_low
    )

    if diff <= 0:

        return EngineResult(
            name="Fibonacci",
            signal="NEUTRAL",
            score=0,
            confidence=0.0,
            weight=1.10,
            reasons=[
                "Invalid Fibonacci structural range"
            ],
            metadata={
                "status": "INVALID_RANGE",
                "swing_high": round(
                    swing_high,
                    2,
                ),
                "swing_low": round(
                    swing_low,
                    2,
                ),
                "candle_count": len(candles),
            },
        ).to_dict()

    # ======================================================
    # FIBONACCI LEVELS
    # ======================================================

    fib236 = (
        swing_high
        - diff * 0.236
    )

    fib382 = (
        swing_high
        - diff * 0.382
    )

    fib500 = (
        swing_high
        - diff * 0.500
    )

    fib618 = (
        swing_high
        - diff * 0.618
    )

    fib786 = (
        swing_high
        - diff * 0.786
    )

    # Fibonacci extensions are separate from retracement levels.
    # Exact Fibonacci extension ratios: 127.2%, 161.8%, 261.8%.
    ext127_2 = (
        swing_high
        + diff * (1.272 - 1.0)
    )

    ext161_8 = (
        swing_high
        + diff * (1.618 - 1.0)
    )

    ext261_8 = (
        swing_high
        + diff * (2.618 - 1.0)
    )

    retracement_levels = {
        "0.0": swing_high,
        "23.6": fib236,
        "38.2": fib382,
        "50.0": fib500,
        "61.8": fib618,
        "78.6": fib786,
        "100.0": swing_low,
    }

    extension_levels = {
        "127.2": ext127_2,
        "161.8": ext161_8,
        "261.8": ext261_8,
    }

    # Backward-compatible aliases for existing consumers.
    ext127 = ext127_2
    ext161 = ext161_8
    ext261 = ext261_8

    # ======================================================
    # CURRENT PRICE
    # ======================================================

    price = _number(
        getattr(
            state,
            "price",
            0.0,
        )
    )

    if price <= 0:

        price = _number(
            window[-1].get(
                "close"
            )
        )

    # ======================================================
    # FIBONACCI LOCATION INTELLIGENCE
    # ======================================================

    signal = "NEUTRAL"

    score = 0

    reasons = []

    status = "NEUTRAL"

    zone = "NEUTRAL"

    if (
        fib618
        <= price
        <= fib500
    ):

        signal = "BULLISH"

        score = 3

        status = "GOLDEN_ZONE"

        zone = "DISCOUNT"

        reasons.append(
            "Golden Zone"
        )

        reasons.append(
            "DISCOUNT"
        )

    elif (
        fib500
        < price
        <= fib382
    ):

        signal = "BULLISH"

        score = 2

        status = "BULLISH_RETRACEMENT"

        zone = "PREMIUM"

        reasons.append(
            "Bullish Retracement"
        )

        reasons.append(
            "PREMIUM"
        )

    elif price > fib236:

        signal = "BULLISH"

        score = 1

        status = "ABOVE_23_6"

        zone = "PREMIUM"

        reasons.append(
            "Above Fib 23.6"
        )

        reasons.append(
            "PREMIUM"
        )

    elif price < fib786:

        signal = "BEARISH"

        score = -1

        status = "BELOW_78_6"

        zone = "DISCOUNT"

        reasons.append(
            "Below Fib 78.6"
        )

        reasons.append(
            "DISCOUNT"
        )

    else:

        status = "MID_RANGE"

        if price < fib500:

            zone = "DISCOUNT"

            reasons.append(
                "DISCOUNT"
            )

        elif price > fib500:

            zone = "PREMIUM"

            reasons.append(
                "PREMIUM"
            )

    # ======================================================
    # RECOVERY STRENGTH
    # ======================================================

    if price > fib618:

        if signal == "BULLISH":

            score += 1

        reasons.append(
            "Strong Recovery"
        )

    # ======================================================
    # CONFIDENCE
    # ======================================================

    confidence = min(
        1.0,
        abs(score) / 4.0,
    )

    # ======================================================
    # RESULT
    # ======================================================

    return EngineResult(
        name="Fibonacci",
        signal=signal,
        score=score,
        confidence=confidence,
        weight=1.10,
        reasons=reasons,
        metadata={
            "status": status,
            "zone": zone,
            "price": round(
                price,
                2,
            ),
            "retracements": {
                "0.0": round(
                    retracement_levels["0.0"],
                    2,
                ),
                "23.6": round(
                    retracement_levels["23.6"],
                    2,
                ),
                "38.2": round(
                    retracement_levels["38.2"],
                    2,
                ),
                "50.0": round(
                    retracement_levels["50.0"],
                    2,
                ),
                "61.8": round(
                    retracement_levels["61.8"],
                    2,
                ),
                "78.6": round(
                    retracement_levels["78.6"],
                    2,
                ),
                "100.0": round(
                    retracement_levels["100.0"],
                    2,
                ),
            },
            "extensions": {
                "127.2": round(
                    extension_levels["127.2"],
                    2,
                ),
                "161.8": round(
                    extension_levels["161.8"],
                    2,
                ),
                "261.8": round(
                    extension_levels["261.8"],
                    2,
                ),
            },
            "fib236": round(
                fib236,
                2,
            ),
            "fib382": round(
                fib382,
                2,
            ),
            "fib500": round(
                fib500,
                2,
            ),
            "fib618": round(
                fib618,
                2,
            ),
            "fib786": round(
                fib786,
                2,
            ),
            "extension127": round(
                ext127,
                2,
            ),
            "extension161": round(
                ext161,
                2,
            ),
            "extension261": round(
                ext261,
                2,
            ),
            "swing_high": round(
                swing_high,
                2,
            ),
            "swing_low": round(
                swing_low,
                2,
            ),
            "range": round(
                diff,
                2,
            ),
            "candle_count": len(
                candles
            ),
            "lookback": LOOKBACK,
        },
    ).to_dict()
