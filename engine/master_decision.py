from engine.ai_brain import analyze as ai_analyze
from engine.smc_engine import analyze as smc_analyze
from engine.gann_engine import analyze as gann_analyze
from engine.fibonacci_engine import analyze as fib_analyze
from engine.market_regime import analyze as regime_analyze
from engine.trade_filter import analyze as filter_analyze
from engine.trade_planner import analyze as planner_analyze
from engine.confluence_engine import analyze as confluence


def analyze(state):

    ai = ai_analyze(state)
    smc = smc_analyze(state)
    gann = gann_analyze(state)
    fib = fib_analyze(state)
    regime = regime_analyze(state)

    final = confluence(
        ai,
        smc,
        gann,
        fib,
        regime
    )

    state.decision = final["decision"]

    trade_filter = filter_analyze(state)

    if trade_filter["allow_trade"]:
        plan = planner_analyze(state)
    else:
        plan = None

    state.ai_score = final["score"]
    state.probability = final["probability"]

    p = state.probability

    if p >= 90:
        state.confidence = "A+"
    elif p >= 80:
        state.confidence = "A"
    elif p >= 70:
        state.confidence = "B"
    elif p >= 60:
        state.confidence = "C"
    else:
        state.confidence = "D"

    if plan:
        if "Direction" in plan:
            state.decision = plan["Direction"]
        elif "Trade" in plan:
            state.decision = plan["Trade"]
        else:
            state.decision = final["decision"]
    else:
        state.decision = final["decision"]

    return {
        "ai": ai,
        "smart_money": smc,
        "gann": gann,
        "fib": fib,
        "regime": regime,
        "filter": trade_filter,
        "plan": plan,
        "score": final["score"],
        "probability": final["probability"],
        "confidence": state.confidence,
        "decision": state.decision,
        "reasons": final["reasons"],
    }
