"""
Jaguar Quant X Enterprise
Structural Market Utilities v2.0

Canonical swing-structure utility layer.

Responsibilities:
- Resolve candle source
- Detect confirmed swing highs
- Detect confirmed swing lows
- Classify structural pivots
- Expose latest confirmed pivots

This module does not produce trading decisions.
It provides canonical structural facts to specialist engines.
"""



# ==========================================================
# CANDLE SOURCE
# ==========================================================

def get_candles(state):
    """
    Resolve the canonical analytical candle dataset.

    Enterprise candle authority:
        state.market["candles"]

    Legacy state.candles is supported only as a secondary
    compatibility source.

    No module-global market snapshot is permitted.
    """

    market = getattr(
        state,
        "market",
        {},
    )

    if isinstance(market, dict):

        market_candles = market.get(
            "candles",
            [],
        )

        if (
            isinstance(market_candles, list)
            and market_candles
        ):
            return market_candles

    state_candles = getattr(
        state,
        "candles",
        None,
    )

    if (
        isinstance(state_candles, list)
        and state_candles
    ):
        return state_candles

    return []

# ==========================================================
# SAFE NUMBER
# ==========================================================

def _number(value, default=0.0):

    try:
        return float(value)

    except (TypeError, ValueError):
        return float(default)


# ==========================================================
# CANDLE VALIDATION
# ==========================================================

def valid_candles(candles):
    """
    Return only structurally usable candles.
    """

    if not isinstance(candles, list):
        return []

    required = (
        "high",
        "low",
        "close",
    )

    output = []

    for candle in candles:

        if not isinstance(candle, dict):
            continue

        if not all(
            key in candle
            for key in required
        ):
            continue

        output.append(candle)

    return output


# ==========================================================
# SWING HIGH
# ==========================================================

def is_swing_high(
    candles,
    index,
    left=2,
    right=2,
):
    """
    Confirm a pivot high only after right-side candles exist.
    """

    if index < left:
        return False

    if index + right >= len(candles):
        return False

    current_high = _number(
        candles[index].get("high")
    )

    left_highs = [
        _number(
            candles[i].get("high")
        )
        for i in range(
            index - left,
            index,
        )
    ]

    right_highs = [
        _number(
            candles[i].get("high")
        )
        for i in range(
            index + 1,
            index + right + 1,
        )
    ]

    if not left_highs or not right_highs:
        return False

    return (
        current_high > max(left_highs)
        and current_high >= max(right_highs)
    )


# ==========================================================
# SWING LOW
# ==========================================================

def is_swing_low(
    candles,
    index,
    left=2,
    right=2,
):
    """
    Confirm a pivot low only after right-side candles exist.
    """

    if index < left:
        return False

    if index + right >= len(candles):
        return False

    current_low = _number(
        candles[index].get("low")
    )

    left_lows = [
        _number(
            candles[i].get("low")
        )
        for i in range(
            index - left,
            index,
        )
    ]

    right_lows = [
        _number(
            candles[i].get("low")
        )
        for i in range(
            index + 1,
            index + right + 1,
        )
    ]

    if not left_lows or not right_lows:
        return False

    return (
        current_low < min(left_lows)
        and current_low <= min(right_lows)
    )


# ==========================================================
# DETECT SWINGS
# ==========================================================

def detect_swings(
    candles,
    left=2,
    right=2,
    lookback=100,
    include_available_index=False,
):
    """
    Detect confirmed structural pivots.

    Returns:
    {
        "highs": [...],
        "lows": [...]
    }
    """

    candles = valid_candles(
        candles
    )

    result = {
        "highs": [],
        "lows": [],
    }

    minimum = (
        left
        + right
        + 1
    )

    if len(candles) < minimum:
        return result

    start = max(
        left,
        len(candles) - lookback,
    )

    end = (
        len(candles)
        - right
    )

    for index in range(
        start,
        end,
    ):

        candle = candles[index]

        if is_swing_high(
            candles,
            index,
            left,
            right,
        ):

            result["highs"].append(
                {
                    "index": index,
                    "price": _number(
                        candle.get("high")
                    ),
                    "type": "SWING_HIGH",
                           "available_index": (
                               index + right
                           ),
                }
            )

        if is_swing_low(
            candles,
            index,
            left,
            right,
        ):

            result["lows"].append(
                {
                    "index": index,
                    "price": _number(
                        candle.get("low")
                    ),
                    "type": "SWING_LOW",
                           "available_index": (
                               index + right
                           ),

                }
            )

    return result


# ==========================================================
# CLASSIFY HIGH PIVOTS
# ==========================================================

def classify_highs(highs):
    """
    Classify swing highs as HH or LH.
    """

    output = []

    previous = None

    for pivot in highs:

        item = dict(pivot)

        price = _number(
            item.get("price")
        )

        if previous is None:

            item["structure"] = (
                "UNCLASSIFIED"
            )

        elif price > previous:

            item["structure"] = "HH"

        elif price < previous:

            item["structure"] = "LH"

        else:

            item["structure"] = "EQH"

        output.append(item)

        previous = price

    return output


# ==========================================================
# CLASSIFY LOW PIVOTS
# ==========================================================

def classify_lows(lows):
    """
    Classify swing lows as HL or LL.
    """

    output = []

    previous = None

    for pivot in lows:

        item = dict(pivot)

        price = _number(
            item.get("price")
        )

        if previous is None:

            item["structure"] = (
                "UNCLASSIFIED"
            )

        elif price > previous:

            item["structure"] = "HL"

        elif price < previous:

            item["structure"] = "LL"

        else:

            item["structure"] = "EQL"

        output.append(item)

        previous = price

    return output


# ==========================================================
# STRUCTURE SNAPSHOT
# ==========================================================

def structure_snapshot(
    state,
    left=2,
    right=2,
    lookback=100,
):
    """
    Build canonical structural snapshot.
    """

    candles = valid_candles(
        get_candles(state)
    )

    swings = detect_swings(
        candles,
        left=left,
        right=right,
        lookback=lookback,
    )

    highs = classify_highs(
        swings["highs"]
    )

    lows = classify_lows(
        swings["lows"]
    )

    latest_high = (
        highs[-1]
        if highs
        else None
    )

    previous_high = (
        highs[-2]
        if len(highs) >= 2
        else None
    )

    latest_low = (
        lows[-1]
        if lows
        else None
    )

    previous_low = (
        lows[-2]
        if len(lows) >= 2
        else None
    )

    return {
        "candles": candles,

        "swings": {
            "highs": swings["highs"],
            "lows": swings["lows"],
        },

        "highs": highs,
        "lows": lows,

        "latest_high": latest_high,
        "previous_high": previous_high,

        "latest_low": latest_low,
        "previous_low": previous_low,
    }
