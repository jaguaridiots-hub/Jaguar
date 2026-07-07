from engine.ai_brain import analyze as ai_analyze
from engine.market_regime import analyze as regime_analyze
from engine.smc_engine import analyze as smc_analyze

from engine.bos_engine import analyze as bos_analyze
from engine.choch_engine import analyze as choch_analyze
from engine.liquidity_engine import analyze as liquidity_analyze
from engine.order_block_engine import analyze as ob_analyze
from engine.fvg_engine import analyze as fvg_analyze

from engine.fibonacci_engine import analyze as fib_analyze
from engine.gann_engine import analyze as gann_analyze

from engine.institutional_confluence import analyze as confluence

from engine.trade_planner import analyze as planner
from engine.risk_engine import analyze as risk


def analyze(state, capital=100000):

    ai = ai_analyze(state)

    regime = regime_analyze(state)

    smc = smc_analyze(state)

    bos = bos_analyze(state)

    choch = choch_analyze(state)

    liquidity = liquidity_analyze(state)

    order_block = ob_analyze(state)

    fvg = fvg_analyze(state)

    fib = fib_analyze(state)

    gann = gann_analyze(state)

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
    )

    state.ai_score = final["score"]
    state.probability = final["probability"]
    state.confidence = final["confidence"]
    state.decision = final["decision"]

    plan = planner(state)

    risk_report = risk(
        state,
        plan,
        capital
    )

    return {

        "decision": final,

        "plan": plan,

        "risk": risk_report,

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

            "Gann": gann

        }

    }
