"""
Jaguar Quant X Enterprise
Change of Character Engine v2.1

Canonical persistent swing-based CHOCH detector.

CHOCH represents a confirmed break against the currently
protected structural character.

Structural character is persistent across analytical cycles.

Bullish protected structure:
    Higher High + Higher Low

Bearish CHOCH:
    Candle CLOSE below the protected Higher Low

Bearish protected structure:
    Lower High + Lower Low

Bullish CHOCH:
    Candle CLOSE above the protected Lower High

Mixed pivot observations do not automatically erase an
already-established structural character.
"""

from core.engine_result import EngineResult

from engine.structure_utils import (
    structure_snapshot,
)


# ==========================================================
# MEMORY CONTRACT
# ==========================================================

def _memory(state):

    memory = getattr(
        state,
        "structural_memory",
        None,
    )

    if not isinstance(
        memory,
        dict,
    ):

        memory = {
            "direction": "NEUTRAL",
            "state": "UNDEFINED",
            "protected_level": 0.0,
            "protected_pivot_index": None,
            "established_by": "NONE",
            "last_transition": "NONE",
            "last_high_index": None,
            "last_low_index": None,
        }

        state.structural_memory = memory

    memory.setdefault(
        "direction",
        "NEUTRAL",
    )

    memory.setdefault(
        "state",
        "UNDEFINED",
    )

    memory.setdefault(
        "protected_level",
        0.0,
    )

    memory.setdefault(
        "protected_pivot_index",
        None,
    )

    memory.setdefault(
        "established_by",
        "NONE",
    )

    memory.setdefault(
        "last_transition",
        "NONE",
    )

    memory.setdefault(
        "last_high_index",
        None,
    )

    memory.setdefault(
        "last_low_index",
        None,
    )

    return memory


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

    highs = structure[
        "highs"
    ]

    lows = structure[
        "lows"
    ]

    memory = _memory(
        state
    )

    # ======================================================
    # INSUFFICIENT MARKET DATA
    #
    # Do not erase persistent structural memory.
    # ======================================================

    if len(candles) < 20:

        return EngineResult(
            name="CHOCH",
            signal="NEUTRAL",
            score=0,
            confidence=0.0,
            weight=1.15,
            reasons=[
                "Not enough candles"
            ],
            metadata={
                "status": "INSUFFICIENT_DATA",
                "prior_structure": memory[
                    "direction"
                ],
                "protected_level": memory[
                    "protected_level"
                ],
                "protected_pivot_index": memory[
                    "protected_pivot_index"
                ],
                "structural_state": memory[
                    "state"
                ],
                "memory_retained": True,
            },
        ).to_dict()

    if (
        len(highs) < 2
        or len(lows) < 2
    ):

        return EngineResult(
            name="CHOCH",
            signal="NEUTRAL",
            score=0,
            confidence=0.0,
            weight=1.15,
            reasons=[
                "Insufficient confirmed swing structure"
            ],
            metadata={
                "status": "STRUCTURAL_WAIT",
                "prior_structure": memory[
                    "direction"
                ],
                "protected_level": memory[
                    "protected_level"
                ],
                "protected_pivot_index": memory[
                    "protected_pivot_index"
                ],
                "structural_state": memory[
                    "state"
                ],
                "memory_retained": True,
                "swing_high_count": len(
                    highs
                ),
                "swing_low_count": len(
                    lows
                ),
            },
        ).to_dict()

    # ======================================================
    # CONFIRMED STRUCTURAL PIVOTS
    # ======================================================

    previous_high = highs[-2]

    latest_high = highs[-1]

    previous_low = lows[-2]

    latest_low = lows[-1]

    last = candles[-1]

    last_close = float(
        last.get(
            "close",
            0.0,
        )
        or 0.0
    )

    previous_high_price = float(
        previous_high.get(
            "price",
            0.0,
        )
        or 0.0
    )

    latest_high_price = float(
        latest_high.get(
            "price",
            0.0,
        )
        or 0.0
    )

    previous_low_price = float(
        previous_low.get(
            "price",
            0.0,
        )
        or 0.0
    )

    latest_low_price = float(
        latest_low.get(
            "price",
            0.0,
        )
        or 0.0
    )

    latest_high_index = latest_high.get(
        "index"
    )

    latest_low_index = latest_low.get(
        "index"
    )

    # ======================================================
    # CURRENT PIVOT OBSERVATION
    # ======================================================

    bullish_structure = (
        latest_high_price
        > previous_high_price
        and latest_low_price
        > previous_low_price
    )

    bearish_structure = (
        latest_high_price
        < previous_high_price
        and latest_low_price
        < previous_low_price
    )

    # ======================================================
    # EXISTING CANONICAL STRUCTURAL CHARACTER
    # ======================================================

    prior_structure = str(
        memory.get(
            "direction",
            "NEUTRAL",
        )
    ).upper()

    protected_level = float(
        memory.get(
            "protected_level",
            0.0,
        )
        or 0.0
    )

    protected_pivot_index = memory.get(
        "protected_pivot_index"
    )

    signal = "NEUTRAL"

    score = 0

    confidence = 0.0

    reasons = []

    status = "WAITING"

    memory_retained = False

    transition = "NONE"

    # ======================================================
    # ESTABLISH INITIAL BULLISH STRUCTURE
    # ======================================================

    if (
        prior_structure
        not in (
            "BULLISH",
            "BEARISH",
        )
        and bullish_structure
    ):

        prior_structure = "BULLISH"

        protected_level = latest_low_price

        protected_pivot_index = latest_low_index

        memory[
            "direction"
        ] = "BULLISH"

        memory[
            "state"
        ] = "PROTECTED"

        memory[
            "protected_level"
        ] = protected_level

        memory[
            "protected_pivot_index"
        ] = protected_pivot_index

        memory[
            "established_by"
        ] = "HH_HL"

        memory[
            "last_transition"
        ] = "BULLISH_STRUCTURE_ESTABLISHED"

        transition = (
            "BULLISH_STRUCTURE_ESTABLISHED"
        )

        status = "WAITING"

        reasons.append(
            "Bullish structural character established"
        )

    # ======================================================
    # ESTABLISH INITIAL BEARISH STRUCTURE
    # ======================================================

    elif (
        prior_structure
        not in (
            "BULLISH",
            "BEARISH",
        )
        and bearish_structure
    ):

        prior_structure = "BEARISH"

        protected_level = latest_high_price

        protected_pivot_index = latest_high_index

        memory[
            "direction"
        ] = "BEARISH"

        memory[
            "state"
        ] = "PROTECTED"

        memory[
            "protected_level"
        ] = protected_level

        memory[
            "protected_pivot_index"
        ] = protected_pivot_index

        memory[
            "established_by"
        ] = "LH_LL"

        memory[
            "last_transition"
        ] = "BEARISH_STRUCTURE_ESTABLISHED"

        transition = (
            "BEARISH_STRUCTURE_ESTABLISHED"
        )

        status = "WAITING"

        reasons.append(
            "Bearish structural character established"
        )

    # ======================================================
    # PROTECTED BULLISH STRUCTURE
    # ======================================================

    elif prior_structure == "BULLISH":

        # --------------------------------------------------
        # Refresh protected HL when bullish structure extends
        # --------------------------------------------------

        if (
            bullish_structure
            and latest_low_index is not None
            and (
                protected_pivot_index is None
                or latest_low_index
                > protected_pivot_index
            )
        ):

            protected_level = latest_low_price

            protected_pivot_index = (
                latest_low_index
            )

            memory[
                "protected_level"
            ] = protected_level

            memory[
                "protected_pivot_index"
            ] = protected_pivot_index

            memory[
                "state"
            ] = "PROTECTED"

            memory[
                "established_by"
            ] = "HH_HL"

            memory[
                "last_transition"
            ] = "BULLISH_PROTECTION_REFRESHED"

            transition = (
                "BULLISH_PROTECTION_REFRESHED"
            )

        # --------------------------------------------------
        # Bearish CHOCH
        # --------------------------------------------------

        if (
            protected_level > 0.0
            and protected_pivot_index is not None
            and protected_pivot_index
            < len(candles) - 1
            and last_close
            < protected_level
        ):

            signal = "BEARISH"

            score = -4

            confidence = 0.85

            status = "CONFIRMED"

            memory[
                "direction"
            ] = "BEARISH"

            memory[
                "state"
            ] = "CHARACTER_CHANGE"

            memory[
                "protected_level"
            ] = latest_high_price

            memory[
                "protected_pivot_index"
            ] = latest_high_index

            memory[
                "established_by"
            ] = "BEARISH_CHOCH"

            memory[
                "last_transition"
            ] = "BEARISH_CHOCH_CONFIRMED"

            transition = (
                "BEARISH_CHOCH_CONFIRMED"
            )

            reasons.append(
                "Bearish CHOCH below protected higher low"
            )

        else:

            memory_retained = True

            reasons.append(
                "Bullish structure remains protected"
            )

            if not bullish_structure:

                reasons.append(
                    "Mixed pivots did not invalidate "
                    "protected bullish structure"
                )

    # ======================================================
    # PROTECTED BEARISH STRUCTURE
    # ======================================================

    elif prior_structure == "BEARISH":

        # --------------------------------------------------
        # Refresh protected LH when bearish structure extends
        # --------------------------------------------------

        if (
            bearish_structure
            and latest_high_index is not None
            and (
                protected_pivot_index is None
                or latest_high_index
                > protected_pivot_index
            )
        ):

            protected_level = latest_high_price

            protected_pivot_index = (
                latest_high_index
            )

            memory[
                "protected_level"
            ] = protected_level

            memory[
                "protected_pivot_index"
            ] = protected_pivot_index

            memory[
                "state"
            ] = "PROTECTED"

            memory[
                "established_by"
            ] = "LH_LL"

            memory[
                "last_transition"
            ] = "BEARISH_PROTECTION_REFRESHED"

            transition = (
                "BEARISH_PROTECTION_REFRESHED"
            )

        # --------------------------------------------------
        # Bullish CHOCH
        # --------------------------------------------------

        if (
            protected_level > 0.0
            and protected_pivot_index is not None
            and protected_pivot_index
            < len(candles) - 1
            and last_close
            > protected_level
        ):

            signal = "BULLISH"

            score = 4

            confidence = 0.85

            status = "CONFIRMED"

            memory[
                "direction"
            ] = "BULLISH"

            memory[
                "state"
            ] = "CHARACTER_CHANGE"

            memory[
                "protected_level"
            ] = latest_low_price

            memory[
                "protected_pivot_index"
            ] = latest_low_index

            memory[
                "established_by"
            ] = "BULLISH_CHOCH"

            memory[
                "last_transition"
            ] = "BULLISH_CHOCH_CONFIRMED"

            transition = (
                "BULLISH_CHOCH_CONFIRMED"
            )

            reasons.append(
                "Bullish CHOCH above protected lower high"
            )

        else:

            memory_retained = True

            reasons.append(
                "Bearish structure remains protected"
            )

            if not bearish_structure:

                reasons.append(
                    "Mixed pivots did not invalidate "
                    "protected bearish structure"
                )

    # ======================================================
    # UNDEFINED STRUCTURE
    # ======================================================

    else:

        status = "MIXED_STRUCTURE"

        reasons.append(
            "No established directional structure for CHOCH"
        )

    # ======================================================
    # MEMORY OBSERVATION
    # ======================================================

    memory[
        "last_high_index"
    ] = latest_high_index

    memory[
        "last_low_index"
    ] = latest_low_index

    canonical_structure = str(
        memory.get(
            "direction",
            "NEUTRAL",
        )
    ).upper()

    canonical_protected_level = float(
        memory.get(
            "protected_level",
            0.0,
        )
        or 0.0
    )

    canonical_protected_index = memory.get(
        "protected_pivot_index"
    )

    structural_state = str(
        memory.get(
            "state",
            "UNDEFINED",
        )
    ).upper()

    # ======================================================
    # RESULT
    # ======================================================

    return EngineResult(
        name="CHOCH",
        signal=signal,
        score=score,
        confidence=confidence,
        weight=1.15,
        reasons=reasons,
        metadata={
            "status": status,
            "prior_structure": canonical_structure,
            "protected_level":
                canonical_protected_level,
            "protected_pivot_index":
                canonical_protected_index,
            "structural_state":
                structural_state,
            "memory_retained": memory_retained,
            "transition": transition,
            "last_close": last_close,
            "previous_high": previous_high,
            "latest_high": latest_high,
            "previous_low": previous_low,
            "latest_low": latest_low,
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
