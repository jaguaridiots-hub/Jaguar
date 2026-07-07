from core.engine_registry import register

from engine.ai_brain import analyze as ai
from engine.market_regime import analyze as regime
from engine.bos_engine import analyze as bos
from engine.choch_engine import analyze as choch
from engine.liquidity_engine import analyze as liquidity
from engine.order_block_engine import analyze as orderblock
from engine.fvg_engine import analyze as fvg
from engine.fibonacci_engine import analyze as fibonacci
from engine.gann_engine import analyze as gann


def load():

    register("AI", ai, 1.20)

    register("Regime", regime, 1.10)

    register("BOS", bos, 1.15)

    register("CHOCH", choch, 1.15)

    register("Liquidity", liquidity, 1.10)

    register("OrderBlock", orderblock, 1.20)

    register("FVG", fvg, 1.15)

    register("Fibonacci", fibonacci, 1.10)

    register("Gann", gann, 1.20)
