"""
Jaguar Quant X Enterprise
Liquidity Engine v2.0

Swing-aware liquidity intelligence.

Detects:
- Buy-side liquidity pools
- Sell-side liquidity pools
- Equal highs
- Equal lows
- Buy-side liquidity sweeps
- Sell-side liquidity sweeps
- Post-sweep reclaim confirmation

This engine uses confirmed swing pivots where possible.

Liquidity lifecycle:
POOL_DETECTED
SWEPT
RECLAIMED
CONFIRMED
NEUTRAL
"""

from core.engine_result import EngineResult
from engine.structure_utils import (
    structure_snapshot,
)

LOOKBACK = 80
SWING_LEFT = 2
SWING_RIGHT = 2
EQUAL_TOLERANCE_ATR = 0.15
MIN_EQUAL_TOUCHES = 2


# ==========================================================
# SAFE NUMBER
# ==========================================================

def _number(value, default=0.0):

    try:
        return float(value or default)

    except (TypeError, ValueError):
        return float(default)


# ==========================================================
# TRUE RANGE / ATR
# ==========================================================

def _true_range(current, previous):

    high = _number(current.get("high"))
    low = _number(current.get("low"))

    previous_close = _number(
        previous.get("close")
    )

    return max(
        high - low,
        abs(high - previous_close),
        abs(low - previous_close),
    )


def _atr(window, period=14):

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
# LIQUIDITY POOL CLUSTERING
# ==========================================================

def _find_pool(
    pivots,
    tolerance,
):

    if len(pivots) < MIN_EQUAL_TOUCHES:
        return None

    best_pool = None

    for base_index in range(
        len(pivots)
    ):

        base = pivots[base_index]

        cluster = [
            base
        ]

        for compare_index in range(
            base_index + 1,
            len(pivots),
        ):

            candidate = pivots[compare_index]

            if abs(
                candidate["price"]
                - base["price"]
            ) <= tolerance:

                cluster.append(
                    candidate
                )

        if len(cluster) < MIN_EQUAL_TOUCHES:
            continue

        level = sum(
            pivot["price"]
            for pivot in cluster
        ) / len(cluster)

        pool = {
            "level": level,
            "touches": len(cluster),
            "first_index": cluster[0]["index"],
            "last_index": cluster[-1]["index"],
            "available_index": max(
                pivot["available_index"]
                for pivot in cluster
            ),
        }

        if (
            best_pool is None
            or pool["touches"]
            > best_pool["touches"]
            or (
                pool["touches"]
                == best_pool["touches"]
                and pool["last_index"]
                > best_pool["last_index"]
            )
        ):

            best_pool = pool

    return best_pool


# ==========================================================
# ENGINE
# ==========================================================

def analyze(state):

    snapshot = structure_snapshot(
        state,
        left=SWING_LEFT,
        right=SWING_RIGHT,
        lookback=LOOKBACK,
    )

    candles = snapshot["candles"]

    if len(candles) < 25:

        return EngineResult(
            name="Liquidity",
            signal="NEUTRAL",
            score=0,
            confidence=0.0,
            weight=1.10,
            reasons=[
                "Not enough candles for liquidity analysis"
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

    atr = _atr(window)

    if atr <= 0:

        return EngineResult(
            name="Liquidity",
            signal="NEUTRAL",
            score=0,
            confidence=0.0,
            weight=1.10,
            reasons=[
                "ATR unavailable for liquidity tolerance"
           ],
            metadata={
                "lifecycle": "NEUTRAL",
            },
        ).to_dict()

    tolerance = max(
        atr * EQUAL_TOLERANCE_ATR,
        1e-9,
    )

    # ======================================================
    # STRUCTURAL COORDINATE ADAPTER
    # ======================================================
    #
    # structure_snapshot() publishes pivots in the canonical
    # full-candle coordinate space.
    #
    # Historical Liquidity logic operates on the local
    # LOOKBACK window coordinate space.
    #
    # Preserve the historical Liquidity temporal contract by
    # normalizing canonical pivot coordinates at the consumer
    # boundary.
    # ======================================================

    window_offset = (
        len(candles)
        - len(window)
    )

    def _localize_pivots(pivots):

        localized = []

        for pivot in pivots:

            local_pivot = dict(
                pivot
            )

            pivot_index = local_pivot.get(
                "index"
            )

            if pivot_index is not None:

                local_pivot["index"] = (
                    pivot_index
                    - window_offset
                )

            available_index = local_pivot.get(
                "available_index"
            )

            if available_index is not None:

                local_pivot["available_index"] = (
                    available_index
                    - window_offset
                )

            localized.append(
                local_pivot
            )

        return localized

    swing_highs = _localize_pivots(
        snapshot["swings"]["highs"]
    )

    swing_lows = _localize_pivots(
        snapshot["swings"]["lows"]
    )

    buy_side_pool = _find_pool(
        swing_highs,
        tolerance,
    )

    sell_side_pool = _find_pool(
        swing_lows,
        tolerance,
    )

    last = window[-1]

    current_index = len(window) - 1

    # ======================================================
    # TEMPORAL POOL ELIGIBILITY
    # ======================================================
    #
    # A liquidity pool may be structurally detected on the
    # current candle, but it may only participate in sweep
    # evaluation after it was already knowable.
    #
    # This prevents the current candle from simultaneously:
    #   1. confirming the latest swing pivot,
    #   2. completing the liquidity pool,
    #   3. sweeping that newly completed pool,
    #   4. confirming the reclaim / rejection.
    #
    # Detection remains available for POOL_DETECTED metadata.
    # Sweep evaluation uses only causally eligible pools.
    # ======================================================

    sell_side_sweep_pool = (
        sell_side_pool
        if (
            sell_side_pool is not None
            and sell_side_pool.get(
                "available_index"
            ) is not None
            and sell_side_pool[
                "available_index"
            ] < current_index
        )
        else None
    )

    buy_side_sweep_pool = (
        buy_side_pool
        if (
            buy_side_pool is not None
            and buy_side_pool.get(
                "available_index"
            ) is not None
            and buy_side_pool[
                "available_index"
            ] < current_index
        )
        else None
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

    signal = "NEUTRAL"
    score = 0
    confidence = 0.0

    lifecycle = "NEUTRAL"
    pool_type = None
    pool_level = None
    touches = 0

    pool_origin_index = None
    pool_last_index = None
    sweep_index = None
    confirmation_index = None

    reasons = []

    # ======================================================
    # SELL-SIDE LIQUIDITY SWEEP
    # Bullish structural event
    # ======================================================

    if sell_side_sweep_pool is not None:

        level = sell_side_sweep_pool["level"]

        if (
            last_low < level
            and last_close > level
        ):

            signal = "BULLISH"
            score = 4
            confidence = 0.85

            lifecycle = "CONFIRMED"
            pool_type = "SELL_SIDE"
            pool_level = level
            touches = sell_side_sweep_pool["touches"]

            pool_origin_index = sell_side_sweep_pool[
                "first_index"
            ]

            pool_last_index = sell_side_sweep_pool[
                "last_index"
            ]

            sweep_index = current_index

            confirmation_index = current_index

            reasons.append(
                "Sell-side liquidity swept and reclaimed"
            )

        elif last_low < level:

            signal = "NEUTRAL"
            score = 0
            confidence = 0.50

            lifecycle = "SWEPT"
            pool_type = "SELL_SIDE"
            pool_level = level
            touches = sell_side_sweep_pool["touches"]

            pool_origin_index = sell_side_sweep_pool[
                "first_index"
            ]

            pool_last_index = sell_side_sweep_pool[
                "last_index"
            ]

            sweep_index = current_index

            reasons.append(
                "Sell-side liquidity swept without reclaim confirmation"
            )

    # ======================================================
    # BUY-SIDE LIQUIDITY SWEEP
    # Bearish structural event
    # ======================================================

    if (
        signal == "NEUTRAL"
        and buy_side_sweep_pool is not None
    ):

        level = buy_side_sweep_pool["level"]

        if (
            last_high > level
            and last_close < level
        ):

            signal = "BEARISH"
            score = -4
            confidence = 0.85

            lifecycle = "CONFIRMED"
            pool_type = "BUY_SIDE"
            pool_level = level
            touches = buy_side_sweep_pool["touches"]

            pool_origin_index = buy_side_sweep_pool[
                "first_index"
            ]

            pool_last_index = buy_side_sweep_pool[
                "last_index"
            ]

            sweep_index = current_index

            confirmation_index = current_index

            reasons.append(
                "Buy-side liquidity swept and rejected"
            )

        elif last_high > level:

            signal = "NEUTRAL"
            score = 0
            confidence = 0.50

            lifecycle = "SWEPT"
            pool_type = "BUY_SIDE"
            pool_level = level
            touches = buy_side_sweep_pool["touches"]

            pool_origin_index = buy_side_sweep_pool[
                "first_index"
            ]

            pool_last_index = buy_side_sweep_pool[
                "last_index"
            ]

            sweep_index = current_index

            reasons.append(
                "Buy-side liquidity swept without rejection confirmation"
            )

    # ======================================================
    # ACTIVE POOL
    # ======================================================

    if lifecycle == "NEUTRAL":

        if sell_side_pool is not None:

            lifecycle = "POOL_DETECTED"
            pool_type = "SELL_SIDE"
            pool_level = sell_side_pool["level"]
            touches = sell_side_pool["touches"]

            pool_origin_index = sell_side_pool[
                "first_index"
            ]

            pool_last_index = sell_side_pool[
                "last_index"
            ]

            reasons.append(
                "Sell-side liquidity pool detected"
            )

        elif buy_side_pool is not None:

            lifecycle = "POOL_DETECTED"
            pool_type = "BUY_SIDE"
            pool_level = buy_side_pool["level"]
            touches = buy_side_pool["touches"]

            pool_origin_index = buy_side_pool[
                "first_index"
            ]

            pool_last_index = buy_side_pool[
                "last_index"
            ]

            reasons.append(
                "Buy-side liquidity pool detected"
            )

        else:

            reasons.append(
                "No confirmed liquidity pool"
            )

    return EngineResult(
        name="Liquidity",
        signal=signal,
        score=score,
        confidence=confidence,
        weight=1.10,
        reasons=reasons,
        metadata={
            "lifecycle": lifecycle,
            "pool_type": pool_type,
            "pool_level": pool_level,
            "touches": touches,
            "pool_origin_index":
                pool_origin_index,
            "pool_last_index":
                pool_last_index,
            "sweep_index":
                sweep_index,
            "confirmation_index":
                confirmation_index,
            "trigger_age":
                (
                    current_index
                    - confirmation_index
                    if confirmation_index is not None
                    else None
                ),
            "atr": atr,
            "tolerance": tolerance,
            "swing_high_count": len(
                swing_highs
            ),
            "swing_low_count": len(
                swing_lows
            ),
            "buy_side_pool": buy_side_pool,
            "sell_side_pool": sell_side_pool,
            "last_high": last_high,
            "last_low": last_low,
            "last_close": last_close,
        },
    ).to_dict()


if __name__ == "__main__":

    from core.market_state import MarketState

    state = MarketState()

    print(
        analyze(state)
    )
