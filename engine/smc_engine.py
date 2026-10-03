"""
Jaguar Quant X Enterprise
SMC Aggregation Engine

Single-source-of-truth aggregator for Smart Money Concepts.

This engine does NOT independently detect BOS, CHOCH, liquidity,
order blocks, or fair value gaps.

Dedicated structural engines are the analytical authorities.
"""

from engine.bos_engine import analyze as bos_analyze
from engine.choch_engine import analyze as choch_analyze
from engine.liquidity_engine import analyze as liquidity_analyze
from engine.order_block_engine import analyze as ob_analyze
from engine.fvg_engine import analyze as fvg_analyze


def _signal(result, default="NEUTRAL"):
    if isinstance(result, dict):
        return str(result.get("signal", default)).upper()

    if isinstance(result, str):
        return result.upper()

    return default


def _score(result):
    if not isinstance(result, dict):
        return 0

    try:
        return int(result.get("score", 0) or 0)
    except (TypeError, ValueError):
        return 0


def _reasons(result):
    if not isinstance(result, dict):
        return []

    reasons = result.get("reasons", [])

    if not isinstance(reasons, list):
        return []

    return reasons


def analyze(state):
    """
    Aggregate canonical SMC engine results.

    Important:
    This engine is descriptive only.

    The dedicated engines remain the scoring authorities in
    institutional confluence and enterprise scoring.
    """

    bos = bos_analyze(state)
    choch = choch_analyze(state)
    liquidity = liquidity_analyze(state)
    order_block = ob_analyze(state)
    fvg = fvg_analyze(state)

    reasons = []

    for result in (
        bos,
        choch,
        liquidity,
        order_block,
        fvg,
    ):
        reasons.extend(_reasons(result))

    reasons = list(dict.fromkeys(reasons))

    raw_score = sum(
        _score(result)
        for result in (
            bos,
            choch,
            liquidity,
            order_block,
            fvg,
        )
    )

    if raw_score > 0:
        signal = "BULLISH"
    elif raw_score < 0:
        signal = "BEARISH"
    else:
        signal = "NEUTRAL"

    return {
        "name": "SMC Aggregator",
        "signal": signal,

        # Deliberately zero.
        # Dedicated engines own scoring authority.
        "score": 0,

        "confidence": 0.0,
        "weight": 0.0,

        "reasons": reasons,

        "metadata": {
            "raw_score": raw_score,
            "bos": _signal(bos),
            "choch": _signal(choch),
            "liquidity": _signal(liquidity),
            "order_block": _signal(order_block),
            "fvg": _signal(fvg),
        },

        # Legacy compatibility fields
        "bos": _signal(bos),
        "choch": _signal(choch),
        "liquidity": _signal(liquidity),
        "order_block": _signal(order_block),
        "fvg": _signal(fvg),
        "premium": False,
        "discount": False,
    }


if __name__ == "__main__":
    from core.market_state import MarketState

    state = MarketState()

    print(analyze(state))
