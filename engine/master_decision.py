from engine.ai_brain import analyze as ai_analyze
from engine.smart_money import analyze as sm_analyze
from engine.market_regime import analyze as regime_analyze
from engine.trade_filter import analyze as filter_analyze
from engine.trade_planner import analyze as planner_analyze


def analyze(state):

    ai = ai_analyze(state)
    sm = sm_analyze(state)
    regime = regime_analyze(state)
    trade_filter = filter_analyze(state)
    plan = planner_analyze(state)

    total = ai["score"] + sm["score"] + regime["score"]

    probability = (
        ai["probability"] +
        sm["probability"]
    ) // 2

    if probability >= 85:
        confidence = "A+"
    elif probability >= 75:
        confidence = "A"
    elif probability >= 65:
        confidence = "B"
    elif probability >= 55:
        confidence = "C"
    else:
        confidence = "D"

    return {
        "ai": ai,
        "smart_money": sm,
        "regime": regime,
        "filter": trade_filter,
        "plan": plan,
        "score": total,
        "probability": probability,
        "confidence": confidence
    }
