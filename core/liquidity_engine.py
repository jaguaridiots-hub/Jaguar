from core.engine import Engine
from strategy.liquidity_engine import LiquidityEngine


class LiquidityEngineRunner(Engine):

    name = "Liquidity Engine"

    def run(self, state, bus):

        bus.publish("LIQUIDITY_ANALYSIS")

        candles = state.market_current["candles"]

        state.liquidity = LiquidityEngine.analyze(candles)

        bus.publish("LIQUIDITY_READY")

        return state
