"""
Jaguar Quant X Enterprise
Institutional Master v2.3

Canonical enterprise orchestration layer.

Enterprise authority:

    Specialist Engines
        ->
    Canonical Structural Contract
        ->
    SMC Aggregation
        ->
    Institutional Confluence
        ->
    Enterprise Adapter
        ->
    Institutional Score
        ->
    IDM
        ->
    Trade Planner V2
        ->
    Risk Manager V2
        ->
    Execution Gateway V2

Structural specialist engines are executed exactly once per
institutional analysis cycle.

Legacy analytics are preserved for diagnostics and compatibility.
They are not execution authorities.
"""

from copy import deepcopy

from engine.ai_brain import analyze as ai_analyze
from engine.market_regime import analyze as regime_analyze

from engine.bos_engine import analyze as bos_analyze
from engine.choch_engine import analyze as choch_analyze
from engine.liquidity_engine import analyze as liquidity_analyze
from engine.order_block_engine import analyze as ob_analyze
from engine.fvg_engine import analyze as fvg_analyze

from engine.fibonacci_engine import analyze as fib_analyze
from engine.gann_engine import analyze as gann_analyze

from engine.institutional_confluence import analyze as confluence

from intelligence.enterprise_adapter import EnterpriseAdapter
from intelligence.execution_confirmation_engine import analyze as execution_confirmation_analyze
from intelligence.structural_zone_engine import (
    StructuralZoneEngine,
)

adapter = EnterpriseAdapter()

structural_zone_engine = StructuralZoneEngine()

# ============================================================
# ENGINE RESULT HELPERS
# ============================================================

def _signal(result, default="NEUTRAL"):
    """
    Normalize an engine result into a directional signal.
    """

    if isinstance(result, dict):
        return str(
            result.get(
                "signal",
                default,
            )
        ).upper().strip()

    if isinstance(result, str):
        return result.upper().strip()

    return default


def _score(result):
    """
    Safely extract an engine score.
    """

    if not isinstance(result, dict):
        return 0

    try:
        return int(
            result.get(
                "score",
                0,
            )
            or 0
        )

    except (TypeError, ValueError):
        return 0


def _confidence(result):
    """
    Safely extract an engine confidence value.
    """

    if not isinstance(result, dict):
        return 0.0

    try:
        return float(
            result.get(
                "confidence",
                0.0,
            )
            or 0.0
        )

    except (TypeError, ValueError):
        return 0.0


def _reasons(result):
    """
    Safely extract engine reasons.
    """

    if not isinstance(result, dict):
        return []

    reasons = result.get(
        "reasons",
        [],
    )

    if not isinstance(reasons, list):
        return []

    return reasons


def _metadata(result):
    """
    Safely extract engine metadata.
    """

    if not isinstance(result, dict):
        return {}

    metadata = result.get(
        "metadata",
        {},
    )

    if not isinstance(metadata, dict):
        return {}

    return metadata


def _confirmed(result):
    """
    True only when a specialist engine emits an active
    directional structural signal.
    """

    return _signal(result) in (
        "BULLISH",
        "BEARISH",
    )


def _direction(result):
    """
    Return canonical directional market fact.
    """

    signal = _signal(result)

    if signal == "BULLISH":
        return "BULLISH"

    if signal == "BEARISH":
        return "BEARISH"

    return "NEUTRAL"


# ============================================================
# SMC AGGREGATION
# ============================================================

def _aggregate_smc(
    bos,
    choch,
    liquidity,
    order_block,
    fvg,
):
    """
    Aggregate already-computed structural specialist results.

    IMPORTANT:

    This function does not execute structural detectors.

    BOS, CHOCH, Liquidity, Order Block, and FVG remain the
    analytical and scoring authorities.

    The SMC result is descriptive and compatibility-only.
    """

    structural_results = (
        bos,
        choch,
        liquidity,
        order_block,
        fvg,
    )

    reasons = []

    for result in structural_results:
        reasons.extend(
            _reasons(result)
        )

    reasons = list(
        dict.fromkeys(reasons)
    )

    raw_score = sum(
        _score(result)
        for result in structural_results
    )

    bullish_count = sum(
        1
        for result in structural_results
        if _direction(result) == "BULLISH"
    )

    bearish_count = sum(
        1
        for result in structural_results
        if _direction(result) == "BEARISH"
    )

    active_count = (
        bullish_count
        + bearish_count
    )

    if raw_score > 0:
        signal = "BULLISH"

    elif raw_score < 0:
        signal = "BEARISH"

    else:
        signal = "NEUTRAL"

    if active_count > 0:
        confidence = sum(
            _confidence(result)
            for result in structural_results
            if _confirmed(result)
        ) / active_count

    else:
        confidence = 0.0

    return {
        "name": "SMC Aggregator",
        "signal": signal,

        # Deliberately zero.
        # Specialist engines own scoring authority.
        "score": 0,

        "confidence": confidence,
        "weight": 0.0,
        "reasons": reasons,

        "metadata": {
            "raw_score": raw_score,
            "bullish_count": bullish_count,
            "bearish_count": bearish_count,
            "active_count": active_count,

            "bos": _direction(bos),
            "choch": _direction(choch),
            "liquidity": _direction(liquidity),
            "order_block": _direction(order_block),
            "fvg": _direction(fvg),
        },

        # Legacy compatibility fields
        "bos": _direction(bos),
        "choch": _direction(choch),
        "liquidity": _direction(liquidity),
        "order_block": _direction(order_block),
        "fvg": _direction(fvg),

        "premium": False,
        "discount": False,
    }


# ============================================================
# INSTITUTIONAL MASTER
# ============================================================

def analyze(state, capital=100000):

    # ========================================================
    # ENSURE CANONICAL CONTAINERS
    # ========================================================

    if (
        not hasattr(state, "market")
        or not isinstance(
            state.market,
            dict,
        )
    ):
        state.market = {}

    if (
        not hasattr(state, "metadata")
        or not isinstance(
            state.metadata,
            dict,
        )
    ):
        state.metadata = {}

    # ========================================================
    # PRIMARY ANALYTICAL ENGINES
    # ========================================================

    ai = ai_analyze(state)

    # ========================================================
    # CANONICAL STRUCTURAL SPECIALIST ENGINES
    #
    # EXECUTE EXACTLY ONCE.
    # ========================================================

    bos = bos_analyze(state)

    choch = choch_analyze(state)

    liquidity = liquidity_analyze(state)

    order_block = ob_analyze(state)

    fvg = fvg_analyze(state)

    # ========================================================
    # CANONICAL STRUCTURAL RESULTS CONTRACT
    # ========================================================

    structural_results = {
        "bos": bos,
        "choch": choch,
        "liquidity": liquidity,
        "order_block": order_block,
        "fvg": fvg,
    }

    state.market[
        "structural_results"
    ] = structural_results

    # ========================================================
    # SMC AGGREGATION
    #
    # Uses already-computed specialist results.
    # No detector is executed again.
    # ========================================================

    smc = _aggregate_smc(
        bos,
        choch,
        liquidity,
        order_block,
        fvg,
    )

    state.market[
        "smc_result"
    ] = smc

    # ========================================================
    # FIBONACCI / GANN
    # ========================================================

    fib = fib_analyze(state)

    gann = gann_analyze(state)

    state.fibonacci = fib

    state.gann = gann

    # ========================================================
    # LEGACY BOOLEAN STRUCTURAL COMPATIBILITY
    # ========================================================

    state.bos = _confirmed(
        bos
    )

    state.choch = _confirmed(
        choch
    )

    state.liquidity = _confirmed(
        liquidity
    )

    state.order_block = _confirmed(
        order_block
    )

    state.fvg = _confirmed(
        fvg
    )

    # ========================================================
    # CANONICAL DIRECTIONAL MARKET FACTS
    # ========================================================

    state.market[
        "bos_signal"
    ] = _direction(
        bos
    )

    state.market[
        "choch_signal"
    ] = _direction(
        choch
    )

    state.market[
        "liquidity_signal"
    ] = _direction(
        liquidity
    )

    state.market[
        "order_block_signal"
    ] = _direction(
        order_block
    )

    state.market[
        "fvg_signal"
    ] = _direction(
        fvg
    )

    # ========================================================
    # CANONICAL BOOLEAN MARKET FACTS
    # ========================================================

    state.market[
        "bos"
    ] = _confirmed(
        bos
    )

    state.market[
        "choch"
    ] = _confirmed(
        choch
    )

    state.market[
        "liquidity"
    ] = _confirmed(
        liquidity
    )

    state.market[
        "order_block"
    ] = _confirmed(
        order_block
    )

    state.market[
        "fvg"
    ] = _confirmed(
        fvg
    )

    # ========================================================
    # CANONICAL RAW ENGINE RESULTS
    # ========================================================

    state.market[
        "bos_result"
    ] = bos

    state.market[
        "choch_result"
    ] = choch

    state.market[
        "liquidity_result"
    ] = liquidity

    state.market[
        "order_block_result"
    ] = order_block

    state.market[
        "fvg_result"
    ] = fvg

    regime = regime_analyze(state)

    state.market[
        "regime_result"
    ] = regime
    # ========================================================
    # NORMALIZE REGIME
    # ========================================================

    regime_signal = _signal(
        regime
    )

    state.market[
        "fibonacci_result"
    ] = fib

    state.market[
        "gann_result"
    ] = gann

    # ========================================================
    # STRUCTURAL SNAPSHOT
    # ========================================================

    state.market[
        "structure"
    ] = {
        "bos": _direction(
            bos
        ),
        "choch": _direction(
            choch
        ),
        "liquidity": _direction(
            liquidity
        ),
        "order_block": _direction(
            order_block
        ),
        "fvg": _direction(
            fvg
        ),
        "smc_direction": _direction(
            smc
        ),
        "smc_raw_score": _metadata(
            smc
        ).get(
            "raw_score",
            0,
        ),
    }

    # ========================================================
    # CANONICAL STRUCTURAL ZONE AUTHORITY
    #
    # Structural specialist engines have already executed
    # exactly once and their raw results are available in
    # state.market.
    #
    # StructuralZoneEngine interprets those specialist facts
    # into the canonical enterprise structural contract.
    #
    # This contract must exist before Institutional Confluence
    # establishes canonical market context.
    # ========================================================

    state = structural_zone_engine.process(
        state
    )

    execution_confirmation = execution_confirmation_analyze(state)

    state.market["execution_confirmation"] = execution_confirmation

    state.execution_confirmation = execution_confirmation

    structural_zone = getattr(
        state,
        "structural_zone",
        {},
    )

    if not isinstance(
        structural_zone,
        dict,
    ):
        structural_zone = {}

    # ========================================================
    # DIRECTIONAL ANALYTICAL CONFLUENCE
    # ========================================================

    final = confluence(
        ai,
        regime,
        smc,
        bos,
        choch,
        liquidity,
        order_block,
        fvg,
        fib,
        gann,
        structural_zone,
    )

    if not isinstance(
        final,
        dict,
    ):
        final = {}

    # ========================================================
    # CONTEXT RESULT
    # ========================================================

    context = {
        # Canonical directional context authority.
        "score": final.get(
            "context_score",
            final.get(
                "score",
                0.0,
            ),
        ),

        "context_score": final.get(
            "context_score",
            final.get(
                "score",
                0.0,
            ),
        ),

        # Analytical evidence balance.
        "analytical_score": final.get(
            "analytical_score",
            0,
        ),

        "weighted_score": final.get(
            "weighted_score",
            0.0,
        ),

        "probability": final.get(
            "probability",
            0,
        ),

        "confidence": final.get(
            "confidence",
            "D",
        ),

        "decision": final.get(
            "decision",
            "⚪ NO TRADE",
        ),

        "direction": final.get(
            "direction",
            "NEUTRAL",
        ),

        "structure_confirmed": final.get(
            "structure_confirmed",
            False,
        ),

        "location_confirmed": final.get(
            "location_confirmed",
            False,
        ),

        "setup_confirmed": final.get(
            "setup_confirmed",
            False,
        ),

        "reasons": final.get(
            "reasons",
            [],
        ),
    }
    # ========================================================
    # EXPLICIT CONTEXT STATE
    # ========================================================

    state.context_score = context[
        "score"
    ]

    state.context_probability = context[
        "probability"
    ]

    state.context_confidence = context[
        "confidence"
    ]

    state.context_decision = context[
        "decision"
    ]

    state.context_direction = context[
        "direction"
    ]

    state.context_structure_confirmed = context[
        "structure_confirmed"
    ]

    state.context_location_confirmed = context[
        "location_confirmed"
    ]

    state.context_setup_confirmed = context[
        "setup_confirmed"
    ]

    # ========================================================
    # COMPATIBILITY STATE
    #
    # Required by EnterpriseAdapter.
    # Compatibility-only.
    # ========================================================

    state.ai_score = context[
        "score"
    ]

    state.probability = context[
        "probability"
    ]

    state.confidence = context[
        "confidence"
    ]

    state.decision = context[
        "decision"
    ]

    # ========================================================
    # CANONICAL ENTERPRISE PIPELINE
    # ========================================================

    state = adapter.process(
        state
    )

    # ========================================================
    # SAFE ENTERPRISE CONTAINERS
    # ========================================================

    institutional = getattr(
        state,
        "institutional",
        {},
    )

    if not isinstance(
        institutional,
        dict,
    ):
        institutional = {}

    idm = getattr(
        state,
        "idm",
        {},
    )

    if not isinstance(
        idm,
        dict,
    ):
        idm = {}

    # ========================================================
    # CANONICAL ENTERPRISE RESULT
    # ========================================================

    enterprise = {
        "score": institutional.get(
            "score",
            0,
        ),

        "grade": institutional.get(
            "grade",
            "F",
        ),

        "confidence": institutional.get(
            "confidence",
            0,
        ),

        "decision": idm.get(
            "decision",
            "WAIT",
        ),

        "priority": idm.get(
            "priority",
            "LOW",
        ),

        "approved": idm.get(
            "approved",
            False,
        ),

        "reasons": idm.get(
            "reasons",
            [],
        ),

        "trade": getattr(
            state,
            "trade",
            {},
        ),

        "risk": getattr(
            state,
            "risk",
            {},
        ),

        "execution": getattr(
            state,
            "execution",
            {},
        ),
    }

    # ========================================================
    # FINAL RESULT
    # ========================================================

    return {
        "context": context,

        # Backward compatibility.
        # Existing callers may still use report["decision"].
        "decision": context,

        "enterprise": enterprise,

        "plan": getattr(
            state,
            "trade",
            {},
        ),

        "risk": getattr(
            state,
            "risk",
            {},
        ),

        "engines": {
            "AI": ai,
            "Regime": regime,
            "SMC": smc,
            "BOS": bos,
            "CHOCH": choch,
            "Liquidity": liquidity,
            "OrderBlock": order_block,
            "FVG": fvg,
            "Fibonacci": fib,
            "Gann": gann,
        },
    }
